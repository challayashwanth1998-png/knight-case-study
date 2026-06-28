"""
Pipeline Service — Orchestrates the full document processing workflow.
OPTIMIZED: Parallel image extraction, batch classification, Python-based
extraction for structured docs, driver deduplication.
"""
import re
import time
import logging
from typing import Dict, Any
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from models.database import SessionLocal, Submission, Document, AnalysisResult, RuleResult, AuditLog
from services.document_processor import DocumentProcessor
from services.document_classifier import DocumentClassifier
from services.data_extractor import DataExtractor
from services.ai_analyzer import AIAnalyzer
from rules import RulesEngine
from utils.gemini import start_tracking, get_current_metrics, set_tracking

logger = logging.getLogger(__name__)

STEP_NAMES = {
    1: "Text Extraction",
    2: "Document Classification",
    3: "Data Extraction",
    4: "AI Analysis",
    5: "Rules Engine",
    6: "Decision",
}


def run_pipeline(submission_id: str) -> None:
    """Run the full document processing + analysis pipeline with cost tracking."""
    pipeline_start = time.time()
    ai_metrics = start_tracking()

    db = SessionLocal()
    try:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found")
            return

        # Set status to processing immediately
        submission.status = "processing"
        db.commit()

        documents = db.query(Document).filter(Document.submission_id == submission_id).all()

        _step_extract_text(db, submission_id, documents)
        _step_classify(db, submission_id, documents)
        _step_extract_data(db, submission_id, documents)

        # Re-fetch for updated data
        documents = db.query(Document).filter(Document.submission_id == submission_id).all()
        unified = _build_unified_data(documents)

        _step_ai_analysis(db, submission_id, unified)
        _step_rules(db, submission_id, unified)
        _step_decision(db, submission_id, unified)

        # ── Store AI metrics on submission ──
        pipeline_duration = int((time.time() - pipeline_start) * 1000)
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission and ai_metrics:
            submission.ai_input_tokens = ai_metrics.total_input_tokens
            submission.ai_output_tokens = ai_metrics.total_output_tokens
            submission.ai_cost_usd = round(ai_metrics.total_cost_usd, 6)
            submission.ai_calls_count = ai_metrics.total_calls
            submission.processing_duration_ms = pipeline_duration
            db.commit()

        logger.info(
            f"[{submission_id}] Pipeline complete in {pipeline_duration}ms. "
            f"AI: {ai_metrics.total_calls} calls, "
            f"{ai_metrics.total_input_tokens}+{ai_metrics.total_output_tokens} tokens, "
            f"${ai_metrics.total_cost_usd:.5f}"
        )

    except Exception as e:
        logger.error(f"Pipeline error for {submission_id}: {e}", exc_info=True)
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            submission.status = "error"
            submission.decision_reason = f"Pipeline error: {str(e)}"
            if ai_metrics:
                submission.ai_input_tokens = ai_metrics.total_input_tokens
                submission.ai_output_tokens = ai_metrics.total_output_tokens
                submission.ai_cost_usd = round(ai_metrics.total_cost_usd, 6)
                submission.ai_calls_count = ai_metrics.total_calls
                submission.processing_duration_ms = int((time.time() - pipeline_start) * 1000)
            _audit(db, submission_id, "pipeline_error", str(e), step=0)
            db.commit()
    finally:
        db.close()


# ─── Pipeline Steps ──────────────────────────────────────────

def _step_extract_text(db, submission_id: str, documents: list) -> None:
    """Step 1: Extract text. PDFs/Excel use Python. Images use Gemini Vision in parallel."""
    step = 1
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")
    _audit(db, submission_id, "step_extract_text",
           f"Processing {len(documents)} documents", step=step)
    db.commit()

    processor = DocumentProcessor()

    # Separate images (need vision API) from other docs (Python extraction)
    image_docs = []
    other_docs = []
    for doc in documents:
        ext = Path(doc.file_path).suffix.lower() if doc.file_path else ""
        if ext in (".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif", ".webp"):
            image_docs.append(doc)
        else:
            other_docs.append(doc)

    # Process non-image docs synchronously (fast Python extraction)
    for doc in other_docs:
        try:
            doc.processing_status = "extracting"
            db.commit()
            text, structured, quality = processor.process(doc.file_path)
            doc.extracted_text = text
            if structured:
                doc.extracted_data = {"structured_raw": structured}
            doc.quality_score = quality
            doc.processing_status = "extracted"
            db.commit()
        except Exception as e:
            doc.processing_status = "error"
            doc.processing_error = str(e)
            db.commit()
            logger.error(f"  Extract error: {doc.filename}: {e}")

    # Process image docs with BATCH Gemini Vision (1 API call for all images)
    if image_docs:
        for doc in image_docs:
            doc.processing_status = "extracting"
        db.commit()

        try:
            from utils.gemini import call_gemini_vision_batch

            # Collect all images for batch
            images_batch = []
            ext_map = {
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".bmp": "image/bmp", ".tiff": "image/tiff",
                ".webp": "image/webp",
            }
            for doc in image_docs:
                with open(doc.file_path, "rb") as f:
                    img_data = f.read()
                ext = Path(doc.file_path).suffix.lower()
                mime = ext_map.get(ext, "image/png")
                images_batch.append((img_data, mime, doc.filename))

            batch_prompt = (
                "Extract ALL text and data from EACH image below. "
                "For each image, provide the extracted data under a clear header matching the image label. "
                "If an image is a driver's license or CDL, extract: "
                "full name, date of birth, license number, state, class, "
                "endorsements, restrictions, expiration date, sex, height, weight, eye color. "
                "Format each as structured text with clear labels."
            )

            batch_result = call_gemini_vision_batch(
                batch_prompt, images_batch, step_name="batch_cdl_ocr"
            )

            # Split batch result by image labels and assign to each doc
            for i, doc in enumerate(image_docs):
                # Try to find section for this doc's filename
                label = doc.filename
                next_label = image_docs[i + 1].filename if i + 1 < len(image_docs) else None

                start_marker = f"--- Image: {label} ---"
                start_idx = batch_result.find(start_marker)
                if start_idx < 0:
                    # Try alternate markers
                    start_idx = batch_result.lower().find(label.lower())
                    if start_idx < 0:
                        start_idx = 0

                if next_label:
                    next_marker = f"--- Image: {next_label} ---"
                    end_idx = batch_result.find(next_marker, start_idx + 1)
                    if end_idx < 0:
                        end_idx = batch_result.lower().find(next_label.lower(), start_idx + len(label))
                    if end_idx < 0:
                        end_idx = len(batch_result)
                else:
                    end_idx = len(batch_result)

                doc_text = batch_result[start_idx:end_idx].strip()
                if not doc_text or len(doc_text) < 20:
                    # Fallback: give each doc an equal portion
                    chunk_size = len(batch_result) // len(image_docs)
                    doc_text = batch_result[i * chunk_size:(i + 1) * chunk_size].strip()

                doc.extracted_text = doc_text
                doc.quality_score = 0.85 if len(doc_text) > 50 else 0.5
                doc.processing_status = "extracted"
                logger.info(f"  Batch OCR: {doc.filename} → {len(doc_text)} chars")
            db.commit()

        except Exception as batch_err:
            logger.warning(f"Batch vision failed ({batch_err}), falling back to individual calls")
            # Fallback: individual parallel calls (old approach)
            parent_tracker = get_current_metrics()
            def _extract_image(doc_path):
                if parent_tracker:
                    set_tracking(parent_tracker)
                return processor.process(doc_path)

            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                for doc in image_docs:
                    futures[executor.submit(_extract_image, doc.file_path)] = doc

                for future in as_completed(futures):
                    doc = futures[future]
                    try:
                        text, structured, quality = future.result()
                        doc.extracted_text = text
                        if structured:
                            doc.extracted_data = {"structured_raw": structured}
                        doc.quality_score = quality
                        doc.processing_status = "extracted"
                    except Exception as e:
                        doc.processing_status = "error"
                        doc.processing_error = str(e)
                        logger.error(f"  Vision error: {doc.filename}: {e}")
                    db.commit()

    _audit(db, submission_id, "step_extract_text_complete",
           f"Extracted {len(other_docs)} docs + {len(image_docs)} images (batch)", step=step)
    db.commit()


def _step_classify(db, submission_id: str, documents: list) -> None:
    """Step 2: Batch classify ALL documents in a single Gemini call."""
    step = 2
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")
    _audit(db, submission_id, "step_classify",
           "Batch AI document classification", step=step)
    db.commit()

    classifier = DocumentClassifier()

    # Build batch input
    batch_docs = []
    valid_docs = []
    for doc in documents:
        if doc.processing_status == "error":
            continue
        structured = doc.extracted_data.get("structured_raw") if doc.extracted_data else None
        batch_docs.append({
            "filename": doc.original_filename,
            "text": doc.extracted_text or "",
            "structured_data": structured,
        })
        valid_docs.append(doc)

    # Single AI call for all documents
    results = classifier.classify_batch(batch_docs)

    for doc in valid_docs:
        classification = results.get(doc.original_filename)
        if classification:
            doc_type, confidence, reasoning = classification
            doc.classified_type = doc_type
            doc.classification_confidence = confidence
            doc.processing_status = "classified"
            if not doc.extracted_data:
                doc.extracted_data = {}
            doc.extracted_data["classification_reasoning"] = reasoning
            logger.info(f"  {doc.original_filename} → {doc_type} ({confidence:.0%})")
        db.commit()

    _audit(db, submission_id, "step_classify_complete",
           f"Batch classified {len(valid_docs)} documents in 1 AI call", step=step)
    db.commit()


def _step_extract_data(db, submission_id: str, documents: list) -> None:
    """Step 3: Extract structured data. Python for Excel/PDFs, AI only for application + DL images."""
    step = 3
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")
    _audit(db, submission_id, "step_extract_data",
           "Structured data extraction (Python + AI)", step=step)
    db.commit()

    from sqlalchemy.orm.attributes import flag_modified

    extractor = DataExtractor()
    extracted = 0
    ai_count = 0
    python_count = 0
    ai_pending = []  # docs that need AI extraction

    for doc in documents:
        if doc.processing_status == "error" or not doc.classified_type:
            continue
        try:
            structured_raw = doc.extracted_data.get("structured_raw") if doc.extracted_data else None
            doc_type = doc.classified_type

            # Try Python extraction first for structured doc types
            result = None
            if doc_type in ("driver_list", "equipment_list") and structured_raw:
                result = _python_extract_excel(doc_type, structured_raw)
                if result:
                    python_count += 1

            if doc_type in ("ifta_report", "loss_run") and doc.extracted_text:
                result = _python_extract_pdf(doc_type, doc.extracted_text)
                if result:
                    python_count += 1

            # Parse DL vision text with Python regex — no AI needed
            if doc_type == "drivers_license" and doc.extracted_text:
                result = _python_extract_dl(doc.extracted_text)
                if result:
                    python_count += 1

            if result:
                updated = dict(doc.extracted_data) if doc.extracted_data else {}
                updated["extracted"] = result
                doc.extracted_data = updated
                flag_modified(doc, "extracted_data")
                doc.processing_status = "complete"
                extracted += 1
                db.commit()
                logger.info(f"  ✅ {doc.original_filename} extracted (Python)")
            else:
                # Queue for parallel AI extraction
                ai_pending.append(doc)
        except Exception as e:
            logger.error(f"  Extract error: {doc.filename}: {e}")

    # Run all AI extractions IN PARALLEL
    if ai_pending:
        logger.info(f"  Running {len(ai_pending)} AI extractions in parallel...")

        parent_tracker = get_current_metrics()
        def _ai_extract(doc):
            if parent_tracker:
                set_tracking(parent_tracker)
            structured_raw = doc.extracted_data.get("structured_raw") if doc.extracted_data else None
            return extractor.extract(
                doc.classified_type, doc.extracted_text or "",
                structured_raw, doc.original_filename
            )

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_ai_extract, doc): doc for doc in ai_pending}
            for future in as_completed(futures):
                doc = futures[future]
                try:
                    result = future.result()
                    if result:
                        updated = dict(doc.extracted_data) if doc.extracted_data else {}
                        updated["extracted"] = result
                        doc.extracted_data = updated
                        flag_modified(doc, "extracted_data")
                        doc.processing_status = "complete"
                        extracted += 1
                        ai_count += 1
                        db.commit()
                        logger.info(f"  ✅ {doc.original_filename} extracted (AI)")
                except Exception as e:
                    logger.error(f"  AI extract error: {doc.filename}: {e}")

    _audit(db, submission_id, "step_extract_data_complete",
           f"Extracted {extracted} docs ({python_count} Python, {ai_count} AI parallel)", step=step)
    db.commit()


# ─── Python-based Extraction (no AI) ────────────────────────

def _python_extract_excel(doc_type: str, structured_raw: dict) -> dict | None:
    """Extract structured data from Excel using Python — no AI needed."""
    try:
        all_rows = []
        headers = []
        for sheet_name, sheet_data in structured_raw.items():
            if isinstance(sheet_data, dict):
                h = sheet_data.get("headers", [])
                r = sheet_data.get("rows", [])
                if h:
                    headers = [str(x).lower().strip() for x in h if x]
                if r:
                    all_rows.extend(r)

        if not all_rows or not headers:
            return None

        if doc_type == "driver_list":
            return _parse_driver_excel(headers, all_rows)
        elif doc_type == "equipment_list":
            return _parse_equipment_excel(headers, all_rows)
    except Exception as e:
        logger.warning(f"Python Excel extraction failed for {doc_type}: {e}")
    return None


def _parse_driver_excel(headers: list, rows: list) -> dict:
    """Parse driver roster from Excel rows."""
    field_map = {
        "name": ["name", "driver name", "driver"],
        "date_of_birth": ["date of birth", "dob", "birth date"],
        "age": ["age"],
        "license_number": ["cdl number", "cdl", "license", "dl number", "cdl #"],
        "license_state": ["cdl state", "state", "dl state"],
        "license_class": ["cdl class", "class"],
        "years_experience": ["years experience", "experience", "yrs exp"],
        "date_of_hire": ["hire date", "date hired"],
        "violations_3yr": ["violations 3yr", "violations"],
        "accidents_3yr": ["accidents 3yr", "accidents"],
        "status": ["status"],
    }

    def _find_col(target_keys):
        for i, h in enumerate(headers):
            for k in target_keys:
                if k in h:
                    return i
        return None

    col_indices = {field: _find_col(keys) for field, keys in field_map.items()}

    drivers = []
    for row in rows:
        values = list(row.values()) if isinstance(row, dict) else (row if isinstance(row, list) else [])
        if not values or all(v is None or str(v).strip() == "" for v in values):
            continue

        driver = {}
        for field, idx in col_indices.items():
            if idx is not None and idx < len(values):
                driver[field] = values[idx] if values[idx] is not None else None
            else:
                driver[field] = None

        if driver.get("name") and str(driver["name"]).strip():
            name = str(driver["name"]).strip()
            if name.lower() in ("name", "driver name", "driver", "summary", "#"):
                continue
            drivers.append(driver)

    return {"drivers": drivers, "total_drivers": len(drivers)}


def _parse_equipment_excel(headers: list, rows: list) -> dict:
    """Parse vehicle/equipment schedule from Excel rows."""
    field_map = {
        "unit_number": ["unit #", "unit", "#"],
        "year": ["year"],
        "make": ["make / model", "make", "make/model"],
        "model": ["model"],
        "vin": ["vin"],
        "vehicle_type": ["vehicle type", "type"],
        "gvw": ["gvw", "gross vehicle weight"],
        "stated_value": ["stated value", "value"],
    }

    def _find_col(target_keys):
        for i, h in enumerate(headers):
            for k in target_keys:
                if k in h:
                    return i
        return None

    col_indices = {field: _find_col(keys) for field, keys in field_map.items()}

    vehicles = []
    for row in rows:
        values = list(row.values()) if isinstance(row, dict) else (row if isinstance(row, list) else [])
        if not values or all(v is None or str(v).strip() == "" for v in values):
            continue

        vehicle = {}
        for field, idx in col_indices.items():
            if idx is not None and idx < len(values):
                vehicle[field] = values[idx]
            else:
                vehicle[field] = None

        year_str = str(vehicle.get("year", "")).strip()
        if year_str and year_str.lower() not in ("year", "", "none"):
            vehicles.append(vehicle)

    from rules.base import is_power_unit
    power_units = sum(1 for v in vehicles if is_power_unit(v))
    trailers = len(vehicles) - power_units

    return {
        "vehicles": vehicles,
        "total_power_units": power_units,
        "total_trailers": trailers,
        "total_vehicles": len(vehicles),
    }


def _python_extract_dl(text: str) -> dict | None:
    """Parse driver license fields from Gemini Vision-extracted text — no AI needed."""
    if not text or len(text) < 20:
        return None

    result = {}
    text_upper = text.upper()

    # License number patterns: XX-12345678 or XX12345678
    for p in [r"(?:DL\s*(?:NO|#|NUMBER)?:?\s*)([A-Z]{2}[-\s]?\d{6,10})",
              r"(?:LICENSE\s*(?:NUMBER|#)?:?\s*)([A-Z]{2}[-\s]?\d{6,10})",
              r"\b([A-Z]{2}-\d{7,9})\b"]:
        m = re.search(p, text_upper)
        if m:
            result["license_number"] = m.group(1).strip()
            break

    # Name
    for p in [r"NAME:?\s*([A-Z][A-Z\s\.]+?)(?:\n|$)",
              r"([A-Z]{2,}\s+[A-Z]\.?\s+[A-Z]{2,})"]:
        m = re.search(p, text_upper)
        if m:
            name = m.group(1).strip()
            if len(name) > 3 and name not in ("COMMERCIAL DRIVER LICENSE", "DRIVER LICENSE"):
                result["driver_name"] = name
                break

    # DOB
    for p in [r"(?:DOB|DATE\s*OF\s*BIRTH|D\.O\.B):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
              r"DOB:?\s*(\d{2}/\d{2}/\d{4})"]:
        m = re.search(p, text_upper)
        if m:
            result["date_of_birth"] = m.group(1)
            break

    # Expiration
    for p in [r"(?:EXP|EXPIR\w*):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
              r"EXPIRES?:?\s*(\d{2}/\d{2}/\d{4})"]:
        m = re.search(p, text_upper)
        if m:
            result["expiration_date"] = m.group(1)
            break

    # Class
    m = re.search(r"CLASS:?\s*([A-C])\b", text_upper)
    if m:
        result["license_class"] = m.group(1)

    # Endorsements
    m = re.search(r"ENDORSEMENTS?:?\s*([A-Z\s,]+?)(?:\n|$|RESTRICT)", text_upper)
    if m:
        endorsements = m.group(1).strip().rstrip(",").strip()
        if endorsements and endorsements not in ("NONE", "N/A"):
            result["endorsements"] = endorsements

    # Restrictions
    m = re.search(r"RESTRICTIONS?:?\s*(.+?)(?:\n|$)", text_upper)
    if m:
        result["restrictions"] = m.group(1).strip()

    # State
    for p in [r"STATE\s+OF\s+([A-Z]+)", r"^([A-Z]{2,})\s*$"]:
        m = re.search(p, text_upper, re.MULTILINE)
        if m:
            state_name = m.group(1).strip()
            state_map = {"TENNESSEE": "TN", "ALABAMA": "AL", "ARKANSAS": "AR",
                        "VIRGINIA": "VA", "TEXAS": "TX", "CALIFORNIA": "CA",
                        "ARIZONA": "AZ", "SOUTH CAROLINA": "SC", "UTAH": "UT",
                        "WISCONSIN": "WI", "WYOMING": "WY", "WEST VIRGINIA": "WV"}
            result["license_state"] = state_map.get(state_name, state_name[:2])
            break

    # Status
    if "VALID" in text_upper:
        result["license_status"] = "Valid"
    elif "EXPIRED" in text_upper:
        result["license_status"] = "Expired"

    # CDL check
    result["is_commercial"] = "CDL" in text_upper or "COMMERCIAL" in text_upper
    result["license_class"] = result.get("license_class", "A" if result["is_commercial"] else None)

    # Sex
    m = re.search(r"SEX:?\s*([MF])\b", text_upper)
    if m:
        result["sex"] = m.group(1)

    # Only return if we got at least a name or license number
    if result.get("driver_name") or result.get("license_number"):
        return result
    return None


def _python_extract_pdf(doc_type: str, text: str) -> dict | None:
    """Extract structured data from PDF text using regex — no AI needed."""
    try:
        if doc_type == "ifta_report":
            return _parse_ifta_text(text)
        elif doc_type == "loss_run":
            return _parse_loss_run_text(text)
    except Exception as e:
        logger.warning(f"Python PDF extraction failed for {doc_type}: {e}")
    return None


def _parse_ifta_text(text: str) -> dict | None:
    """Parse IFTA report from extracted PDF text."""
    result = {}

    q_match = re.search(r"(Q[1-4])\s+(\d{4})", text)
    if q_match:
        result["quarter"] = f"{q_match.group(1)} {q_match.group(2)}"

    for pattern in [r"Company:\s*(.+?)(?:\n|$)", r"Licensee:\s*(.+?)(?:\n|$)"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            result["company_name"] = m.group(1).strip()
            break

    for field, patterns in [
        ("ifta_license", [r"IFTA\s*(?:License|#):\s*(\S+)"]),
        ("dot_number", [r"DOT\s*(?:#|Number)?:\s*(\d+)", r"USDOT[:\s]*(\d+)"]),
        ("fein", [r"FEIN:\s*(\S+)", r"EIN:\s*(\S+)"]),
    ]:
        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                result[field] = m.group(1).strip()
                break

    # Jurisdictions
    jurisdictions = []
    valid_states = {"AL","AZ","AR","CA","CO","CT","DE","FL","GA","ID","IL","IN","IA",
                    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
                    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD",
                    "TN","TX","UT","VT","VA","WA","WV","WI","WY"}
    state_pattern = re.compile(
        r"\b([A-Z]{2})\b\s+[\$]?([\d,]+(?:\.\d+)?)\s+[\$]?([\d,]+(?:\.\d+)?)", re.MULTILINE
    )
    for m in state_pattern.finditer(text):
        state = m.group(1)
        if state in valid_states:
            try:
                miles = float(m.group(2).replace(",", ""))
                gallons = float(m.group(3).replace(",", ""))
                if miles > 0:
                    jurisdictions.append({"state": state, "miles": miles, "gallons": gallons})
            except ValueError:
                continue

    result["jurisdictions"] = jurisdictions
    # Build flat states_traveled list for rules engine (ELIG-003, EXP-003)
    result["states_traveled"] = list({j["state"] for j in jurisdictions})
    total_miles = sum(j["miles"] for j in jurisdictions)
    total_gallons = sum(j["gallons"] for j in jurisdictions)
    result["total_miles"] = total_miles
    result["total_gallons"] = total_gallons
    result["fleet_mpg"] = round(total_miles / total_gallons, 2) if total_gallons > 0 else None

    return result if jurisdictions or result.get("quarter") else None


def _parse_loss_run_text(text: str) -> dict | None:
    """Parse loss run from extracted PDF text."""
    result = {}

    for p in [r"Insured:\s*(.+?)(?:\n|$)", r"Named Insured:\s*(.+?)(?:\n|$)"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            result["insured_name"] = m.group(1).strip()
            break

    for p in [r"(?:Valued?|Valuation)\s*(?:Date|as of)?:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
              r"Report\s+Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            result["valuation_date"] = m.group(1)
            break

    m = re.search(r"Total\s+Claims?:?\s*(\d+)", text, re.IGNORECASE)
    if m:
        result["total_claims_3yr"] = int(m.group(1))

    m = re.search(r"(?:Overall\s+)?Loss\s+Ratio:?\s*([\d.]+%)", text, re.IGNORECASE)
    if m:
        result["overall_loss_ratio"] = m.group(1)

    if re.search(r"(?:no|zero|0)\s+claims", text, re.IGNORECASE):
        result["total_claims_3yr"] = 0
        result["total_incurred_3yr"] = 0

    return result if result else None


# ─── Remaining Pipeline Steps ────────────────────────────────

def _step_ai_analysis(db, submission_id: str, unified: dict) -> None:
    step = 4
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")
    _audit(db, submission_id, "step_ai_analysis", "AI risk analysis", step=step)
    db.commit()

    analyzer = AIAnalyzer()
    analysis = analyzer.analyze_submission(unified)

    if analysis:
        submission = db.query(Submission).filter(Submission.id == submission_id).first()
        if submission:
            db.add(AnalysisResult(
                submission_id=submission_id,
                summary=analysis.get("summary"),
                business_profile=unified.get("application"),
                completeness_report=analysis.get("completeness_report"),
                conflicts=analysis.get("conflicts"),
                risk_assessment=analysis.get("risk_assessment"),
                recommendations=analysis.get("recommendations"),
                confidence_score=analysis.get("confidence_score"),
                unified_business_info=unified.get("application"),
                unified_drivers=unified.get("drivers"),
                unified_vehicles=unified.get("vehicles"),
                unified_ifta=unified.get("ifta_reports"),
            ))
            db.commit()

    _audit(db, submission_id, "step_ai_analysis_complete",
           f"Confidence: {analysis.get('confidence_score') if analysis else 'N/A'}", step=step)
    db.commit()


def _step_rules(db, submission_id: str, unified: dict) -> None:
    step = 5
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")
    _audit(db, submission_id, "step_rules", "Rules engine evaluation", step=step)
    db.commit()

    engine = RulesEngine()
    evaluations = engine.evaluate_all(unified)

    # ── Filename-vs-Classification discrepancy check ──
    documents = db.query(Document).filter(Document.submission_id == submission_id).all()
    mismatches = _check_filename_classification_mismatch(documents)
    if mismatches:
        mismatch_details = "; ".join(
            f"'{m['filename']}' → classified as {m['classified_as']} (filename suggests {m['expected']})"
            for m in mismatches
        )
        from rules.base import RuleEvaluation
        evaluations.append(RuleEvaluation(
            "SUB-009", "Filename-Content Consistency", "submission",
            "WARNING", "medium",
            f"{len(mismatches)} document(s) have filenames that don't match their content: {mismatch_details}",
            {"mismatches": mismatches},
        ))
    else:
        from rules.base import RuleEvaluation
        evaluations.append(RuleEvaluation(
            "SUB-009", "Filename-Content Consistency", "submission",
            "PASS", "low",
            "All document filenames are consistent with their classified content.",
            {},
        ))

    for ev in evaluations:
        db.add(RuleResult(
            submission_id=submission_id,
            rule_id=ev.rule_id,
            rule_name=ev.rule_name,
            category=ev.category,
            result=ev.result,
            severity=ev.severity,
            details=ev.details,
            data_used=ev.data_used,
        ))
    db.commit()

    _audit(db, submission_id, "step_rules_complete",
           f"{sum(1 for e in evaluations if e.result == 'PASS')} pass, "
           f"{sum(1 for e in evaluations if e.result == 'FAIL')} fail, "
           f"{sum(1 for e in evaluations if e.result == 'WARNING')} warnings",
           step=step)
    db.commit()


def _step_decision(db, submission_id: str, unified: dict) -> None:
    step = 6
    logger.info(f"[{submission_id}] Step {step}: {STEP_NAMES[step]}")

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    rules = db.query(RuleResult).filter(RuleResult.submission_id == submission_id).all()

    fails = [r for r in rules if r.result == "FAIL"]
    warnings = [r for r in rules if r.result == "WARNING"]
    critical_fails = [r for r in fails if r.severity == "critical"]

    if critical_fails:
        decision = "decline"
        reason = f"Declined: {len(critical_fails)} critical rule failure(s)."
    elif fails:
        decision = "refer"
        reason = f"Referred: {len(fails)} rule failure(s) for review."
    elif warnings:
        decision = "refer"
        reason = f"Referred: {len(warnings)} warning(s) for review."
    else:
        decision = "accept"
        reason = "All rules passed. Eligible pending final approval."

    submission.overall_decision = decision
    submission.decision_reason = reason
    submission.status = "complete"
    db.commit()

    logger.info(f"[{submission_id}] Decision: {decision}")
    _audit(db, submission_id, "decision", f"{decision}: {reason}", step=step)
    db.commit()


# ─── Filename-Classification Mismatch Detection ─────────────

# Map filename keywords to expected document types
_FILENAME_HINTS = {
    "application": "insurance_application",
    "app_form": "insurance_application",
    "insurance_app": "insurance_application",
    "driver_roster": "driver_list",
    "driver_list": "driver_list",
    "drivers_list": "driver_list",
    "roster": "driver_list",
    "equipment": "equipment_list",
    "vehicle_schedule": "equipment_list",
    "vehicle_list": "equipment_list",
    "loss_run": "loss_run",
    "lossrun": "loss_run",
    "loss_runs": "loss_run",
    "ifta": "ifta_report",
    "cdl": "drivers_license",
    "license": "drivers_license",
    "dl_": "drivers_license",
}


def _check_filename_classification_mismatch(documents: list) -> list:
    """Compare original filenames against AI classification to detect discrepancies."""
    mismatches = []
    for doc in documents:
        if not doc.original_filename or not doc.classified_type:
            continue
        # Skip DL images — they are often generically named
        if doc.classified_type == "drivers_license":
            continue

        fname_lower = doc.original_filename.lower().replace(" ", "_").replace("-", "_")

        # Find what the filename suggests
        suggested_type = None
        for keyword, expected_type in _FILENAME_HINTS.items():
            if keyword in fname_lower:
                suggested_type = expected_type
                break

        if suggested_type and suggested_type != doc.classified_type:
            # Filename suggests one type but content is classified as another
            type_labels = {
                "insurance_application": "Insurance Application",
                "driver_list": "Driver List/Roster",
                "equipment_list": "Equipment/Vehicle Schedule",
                "loss_run": "Loss Runs",
                "ifta_report": "IFTA Report",
                "drivers_license": "Driver License",
            }
            mismatches.append({
                "filename": doc.original_filename,
                "classified_as": type_labels.get(doc.classified_type, doc.classified_type),
                "expected": type_labels.get(suggested_type, suggested_type),
            })
    return mismatches


# ─── Unified Data Builder ────────────────────────────────────

def _build_unified_data(documents: list) -> Dict[str, Any]:
    unified: Dict[str, Any] = {
        "application": {}, "drivers": [], "vehicles": [],
        "ifta_reports": [], "loss_runs": [], "document_types": [],
        "driver_licenses": [],
    }

    # First pass: collect all structured data
    dl_data_list = []
    for doc in documents:
        if not doc.extracted_data or not doc.classified_type:
            continue
        unified["document_types"].append(doc.classified_type)
        extracted = doc.extracted_data.get("extracted", {})

        mapping = {
            "insurance_application": ("application", None),
            "driver_list": ("drivers", "drivers"),
            "equipment_list": ("vehicles", "vehicles"),
            "ifta_report": ("ifta_reports", None),
            "loss_run": ("loss_runs", None),
        }
        if doc.classified_type in mapping:
            key, sub_key = mapping[doc.classified_type]
            if sub_key:
                unified[key].extend(extracted.get(sub_key, []))
            elif isinstance(unified[key], list):
                # For IFTA: ensure states_traveled exists from jurisdictions
                if doc.classified_type == "ifta_report" and "states_traveled" not in extracted:
                    jurs = extracted.get("jurisdictions", [])
                    if jurs and isinstance(jurs, list):
                        extracted["states_traveled"] = list({
                            j.get("state", "") for j in jurs if isinstance(j, dict) and j.get("state")
                        })
                unified[key].append(extracted)
            else:
                unified[key] = extracted
        elif doc.classified_type == "drivers_license":
            dl_data_list.append(extracted)

    # Second pass: MERGE DL data into existing drivers by license number
    # This prevents duplicates (5 roster + 5 DL images ≠ 10 drivers)
    for dl in dl_data_list:
        dl_lic = (dl.get("license_number") or "").strip().upper().replace(" ", "")
        matched = False
        if dl_lic:
            for driver in unified["drivers"]:
                roster_lic = str(driver.get("license_number") or driver.get("cdl_number") or "")
                roster_lic = roster_lic.strip().upper().replace(" ", "")
                if roster_lic == dl_lic:
                    # Enrich existing driver with DL verification data
                    driver["dl_verified"] = True
                    driver["dl_license_status"] = dl.get("license_status")
                    driver["dl_expiration"] = dl.get("expiration_date")
                    driver["dl_class"] = dl.get("license_class")
                    driver["dl_endorsements"] = dl.get("endorsements")
                    driver["dl_restrictions"] = dl.get("restrictions")
                    driver["dl_is_commercial"] = dl.get("is_commercial")
                    matched = True
                    break

        if not matched:
            # Driver not in roster — add as new (rare case)
            unified["drivers"].append({
                "name": dl.get("driver_name"),
                "date_of_birth": dl.get("date_of_birth"),
                "age": dl.get("age"),
                "license_number": dl.get("license_number"),
                "license_state": dl.get("license_state"),
                "license_class": dl.get("license_class"),
                "dl_verified": True,
                "source": "driver_license_image",
            })

        unified["driver_licenses"].append(dl)

    return unified


def _audit(db, submission_id: str, action: str, details: str, step: int = 0) -> None:
    db.add(AuditLog(
        submission_id=submission_id,
        action=action,
        details=details,
        step_number=step if step > 0 else None,
    ))
