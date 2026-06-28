"""
Knight Insurance — AI Document Classifier
Uses Google Gemini to classify documents by content, NOT by filename.
"""
import json
import logging
from typing import Tuple

from config import settings
from utils.gemini import call_gemini_json

logger = logging.getLogger(__name__)

DOCUMENT_TYPES = {
    "insurance_application": "Commercial auto / truck fleet insurance application form",
    "driver_list": "List/roster of drivers with names, DOB, license numbers, experience",
    "equipment_list": "Vehicle schedule listing trucks/trailers with year, make, model, VIN",
    "ifta_report": "IFTA (International Fuel Tax Agreement) quarterly report with state-by-state miles and fuel data",
    "loss_run": "Insurance loss runs / claims history from prior carriers",
    "motor_vehicle_record": "MVR (Motor Vehicle Record) / driving record for individual driver",
    "drivers_license": "Photo or scan of a driver's license",
    "certificate_of_insurance": "Certificate of insurance (COI) or proof of existing coverage",
    "financial_document": "Financial statement, tax return, or related financial document",
    "dot_safety_record": "DOT/FMCSA safety record or SAFER report",
    "other": "Document that does not fit any of the above categories"
}

CLASSIFICATION_PROMPT = """You are a document classification AI for a commercial auto insurance company.
Analyze the document content below and classify it into exactly ONE of these document types:

{type_descriptions}

IMPORTANT RULES:
1. Do NOT rely on the filename — filenames are often wrong or misleading.
2. Classify based ONLY on the actual content of the document.
3. A file named "Drivers.xlsx" might actually contain vehicle information — look at the data.
4. A file named "LossRuns.pdf" might contain driver information.

Document filename (for reference only, DO NOT trust this): {filename}

Document content:
---
{content}
---

Respond with a JSON object containing:
- "document_type": one of the type keys listed above
- "confidence": a number from 0 to 100 indicating your confidence
- "reasoning": a brief explanation of why you chose this classification

JSON response:"""


class DocumentClassifier:
    """Classifies documents using Google Gemini AI."""

    def __init__(self):
        self._use_retry = True

    def classify_batch(self, documents: list) -> dict:
        """
        Classify ALL documents in a single Gemini call.
        Each doc is a dict with keys: filename, text, structured_data.
        Returns: {filename: (doc_type, confidence, reasoning)}
        """
        if not documents:
            return {}

        # Build document summaries for batch classification
        doc_summaries = []
        for i, doc in enumerate(documents):
            text = (doc.get("text") or "")[:2000]  # Limit per doc for batch
            struct = doc.get("structured_data")
            summary = f"--- DOCUMENT {i+1} ---\n"
            if struct:
                struct_preview = json.dumps(struct, indent=1, default=str)[:1000]
                summary += f"STRUCTURED DATA:\n{struct_preview}\n"
            summary += f"TEXT CONTENT:\n{text}\n"
            doc_summaries.append(summary)

        all_content = "\n".join(doc_summaries)

        type_descriptions = "\n".join([
            f'- "{key}": {desc}' for key, desc in DOCUMENT_TYPES.items()
        ])

        prompt = f"""You are a document classification AI for a commercial auto insurance company.
Classify each document below into exactly ONE type based ONLY on its content.
Do NOT rely on filenames — classify based on the actual text and data.

Document types:
{type_descriptions}

{all_content}

Respond with a JSON array of objects, one per document, in order. Each object must have:
- "document_type": one of the type keys above
- "confidence": 0-100
- "reasoning": brief explanation

JSON array:"""

        try:
            results = call_gemini_json(prompt, temperature=0.1, step_name="batch_classify")
            if not isinstance(results, list):
                results = [results]

            output = {}
            for i, doc in enumerate(documents):
                if i < len(results):
                    r = results[i]
                    doc_type = r.get("document_type", "other")
                    if doc_type not in DOCUMENT_TYPES:
                        doc_type = "other"
                    confidence = float(r.get("confidence", 50)) / 100.0
                    reasoning = r.get("reasoning", "")
                    output[doc["filename"]] = (doc_type, confidence, reasoning)
                else:
                    output[doc["filename"]] = self._fallback_classify(
                        doc["filename"], doc.get("text", ""), doc.get("structured_data"))
            return output

        except Exception as e:
            logger.error(f"Batch classification failed: {e}")
            # Fallback to individual content-based classification
            output = {}
            for doc in documents:
                output[doc["filename"]] = self._fallback_classify(
                    doc["filename"], doc.get("text", ""), doc.get("structured_data"))
            return output

    def classify(self, filename: str, extracted_text: str, structured_data: dict = None) -> Tuple[str, float, str]:
        """Classify a single document based on its content (legacy method)."""
        content = extracted_text[:4000]
        if structured_data:
            struct_preview = json.dumps(structured_data, indent=2, default=str)[:2000]
            content = f"STRUCTURED DATA:\n{struct_preview}\n\nTEXT CONTENT:\n{content}"

        type_descriptions = "\n".join([
            f'- "{key}": {desc}' for key, desc in DOCUMENT_TYPES.items()
        ])

        prompt = CLASSIFICATION_PROMPT.format(
            type_descriptions=type_descriptions,
            filename=filename,
            content=content
        )

        try:
            result = call_gemini_json(prompt, temperature=0.1)
            doc_type = result.get("document_type", "other")
            confidence = float(result.get("confidence", 50))
            reasoning = result.get("reasoning", "No reasoning provided")
            if doc_type not in DOCUMENT_TYPES:
                doc_type = "other"
                confidence = min(confidence, 30)
            return doc_type, confidence / 100.0, reasoning
        except Exception as e:
            logger.error(f"Classification failed for '{filename}': {e}")
            return self._fallback_classify(filename, extracted_text, structured_data)

    def _fallback_classify(self, filename: str, text: str, structured_data: dict = None) -> Tuple[str, float, str]:
        """Simple keyword-based fallback classifier when AI is unavailable."""
        text_lower = text.lower()
        fname_lower = filename.lower()

        # Check content-based keywords
        if any(kw in text_lower for kw in ["ifta", "fuel tax", "tax rate", "fleet mpg", "gallons"]):
            return "ifta_report", 0.80, "Fallback: IFTA keywords found in content"

        if any(kw in text_lower for kw in ["truck fleet application", "general information", "commodities hauled", "description of operations"]):
            return "insurance_application", 0.80, "Fallback: Application form keywords found"

        if structured_data:
            all_headers = []
            for sheet_data in structured_data.values():
                if isinstance(sheet_data, dict) and sheet_data.get("headers"):
                    all_headers.extend([h.lower() for h in sheet_data["headers"] if h])

            header_text = " ".join(all_headers)

            if any(kw in header_text for kw in ["driver", "dob", "date of birth", "license", "cdl"]):
                return "driver_list", 0.75, "Fallback: Driver-related headers found"

            if any(kw in header_text for kw in ["vin", "vehicle", "make", "model", "vehicle type"]):
                return "equipment_list", 0.75, "Fallback: Vehicle-related headers found"

        if any(kw in text_lower for kw in ["loss run", "claims", "incurred", "paid losses"]):
            return "loss_run", 0.70, "Fallback: Loss run keywords found"

        if any(kw in text_lower for kw in ["motor vehicle record", "mvr", "violations", "driving record"]):
            return "motor_vehicle_record", 0.70, "Fallback: MVR keywords found"

        return "other", 0.30, "Fallback: No strong indicators found"
