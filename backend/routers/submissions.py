"""
Submissions Router — API endpoints with input validation guardrails.
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db, Submission, Document, AnalysisResult, RuleResult, AuditLog
from models.schemas import (
    SubmissionResponse, SubmissionDetailResponse, DocumentResponse,
    AnalysisResultResponse, RuleResultResponse, AuditLogResponse, DashboardStats,
)
# NOTE: services.pipeline is imported lazily in _run_pipeline_lazy() below
# to avoid loading heavy AI/document processing modules at startup.
from config import settings
from utils.validators import (
    validate_file_type, validate_file_size, validate_submission_limits,
    sanitize_filename, compute_file_hash, check_duplicates,
)
from utils.s3_storage import upload_to_s3

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("/upload", response_model=SubmissionResponse)
async def upload_submission(
    files: List[UploadFile] = File(...),
    email_from: Optional[str] = Form(None),
    email_subject: Optional[str] = Form(None),
    email_body: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Upload documents to create a new submission with validation guardrails."""
    # ── Guardrail 1: File count limits ──
    valid, msg = validate_submission_limits(len(files))
    if not valid:
        raise HTTPException(422, msg)

    # ── Read all files + validate ──
    file_data = []
    errors = []

    for i, file in enumerate(files):
        content = await file.read()
        filename = file.filename or f"file_{i}"

        # Guardrail 2: File type check
        valid, msg = validate_file_type(filename)
        if not valid:
            errors.append(f"{filename}: {msg}")
            continue

        # Guardrail 3: File size check
        valid, msg = validate_file_size(len(content))
        if not valid:
            errors.append(f"{filename}: {msg}")
            continue

        file_data.append({
            "filename": filename,
            "content": content,
            "hash": compute_file_hash(content),
        })

    if errors and not file_data:
        raise HTTPException(422, f"All files rejected: {'; '.join(errors)}")

    # ── Guardrail 4: Deduplicate ──
    hashes = [f["hash"] for f in file_data]
    dup_indices = check_duplicates(hashes)
    if dup_indices:
        dup_names = [file_data[i]["filename"] for i in dup_indices]
        logger.warning(f"Removing {len(dup_indices)} duplicate file(s): {dup_names}")
        file_data = [f for i, f in enumerate(file_data) if i not in dup_indices]

    # ── Create submission ──
    submission_id = str(uuid.uuid4())
    folder = os.path.join(settings.LOCAL_STORAGE_PATH, "submissions", submission_id)
    os.makedirs(folder, exist_ok=True)

    submission = Submission(
        id=submission_id,
        email_from=email_from or "UI Upload",
        email_subject=email_subject or f"Submission {submission_id[:8]}",
        email_body=email_body,
        status="received",
        received_at=datetime.now(timezone.utc),
    )
    db.add(submission)

    for fd in file_data:
        safe_name = sanitize_filename(fd["filename"])
        path = os.path.join(folder, safe_name)
        with open(path, "wb") as f:
            f.write(fd["content"])

        ext = os.path.splitext(safe_name)[1].lower()
        type_map = {
            ".pdf": "pdf", ".xlsx": "xlsx", ".xls": "xls",
            ".docx": "docx", ".png": "image", ".jpg": "image",
            ".jpeg": "image", ".csv": "csv", ".txt": "text",
        }

        # Upload to S3 for durable storage (non-blocking, falls back to local)
        content_types = {
            "pdf": "application/pdf", "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        s3_key = upload_to_s3(
            fd["content"], submission_id, safe_name,
            content_type=content_types.get(type_map.get(ext, ""), "application/octet-stream"),
        )

        db.add(Document(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            filename=safe_name,
            original_filename=fd["filename"],
            file_path=path,
            file_type=type_map.get(ext, "unknown"),
            file_size=len(fd["content"]),
            storage_type="s3" if s3_key else "local",
            processing_status="pending",
        ))

    details = f"Uploaded {len(file_data)} document(s) via UI"
    if errors:
        details += f" ({len(errors)} rejected)"
    if dup_indices:
        details += f" ({len(dup_indices)} duplicates removed)"

    db.add(AuditLog(
        submission_id=submission_id,
        action="submission_created",
        details=details,
        step_number=0,
    ))
    db.commit()
    db.refresh(submission)

    return _to_response(submission, len(file_data))


@router.post("/{submission_id}/process")
async def process_submission(
    submission_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger the full processing pipeline."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")

    if submission.status == "processing":
        raise HTTPException(409, "Submission is already being processed")

    submission.status = "processing"
    db.add(AuditLog(
        submission_id=submission_id,
        action="pipeline_started",
        details="Pipeline initiated",
        step_number=0,
    ))
    db.commit()

    def _run_pipeline_lazy(sid):
        from services.pipeline import run_pipeline
        run_pipeline(sid)

    background_tasks.add_task(_run_pipeline_lazy, submission_id)
    return {"status": "processing", "submission_id": submission_id}


@router.get("", response_model=List[SubmissionResponse])
async def list_submissions(db: Session = Depends(get_db)):
    submissions = db.query(Submission).order_by(Submission.created_at.desc()).all()
    return [
        _to_response(s, db.query(Document).filter(Document.submission_id == s.id).count())
        for s in submissions
    ]


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: Session = Depends(get_db)):
    q = db.query(Submission)
    return DashboardStats(
        total_submissions=q.count(),
        pending=q.filter(Submission.status == "received").count(),
        processing=q.filter(Submission.status == "processing").count(),
        complete=q.filter(Submission.status == "complete").count(),
        accepted=q.filter(Submission.overall_decision == "accept").count(),
        declined=q.filter(Submission.overall_decision == "decline").count(),
        referred=q.filter(Submission.overall_decision == "refer").count(),
    )


@router.get("/{submission_id}", response_model=SubmissionDetailResponse)
async def get_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")

    return SubmissionDetailResponse(
        id=submission.id,
        email_from=submission.email_from,
        email_subject=submission.email_subject,
        email_body=submission.email_body,
        status=submission.status,
        overall_decision=submission.overall_decision,
        decision_reason=submission.decision_reason,
        received_at=submission.received_at,
        processed_at=submission.processed_at,
        created_at=submission.created_at,
        documents=[DocumentResponse.model_validate(d) for d in
                   db.query(Document).filter(Document.submission_id == submission_id).all()],
        analysis=_get_analysis(db, submission_id),
        rules=[RuleResultResponse.model_validate(r) for r in
               db.query(RuleResult).filter(RuleResult.submission_id == submission_id).all()],
        audit_log=[AuditLogResponse.model_validate(a) for a in
                   db.query(AuditLog).filter(AuditLog.submission_id == submission_id)
                   .order_by(AuditLog.timestamp.asc()).all()],
        ai_input_tokens=submission.ai_input_tokens or 0,
        ai_output_tokens=submission.ai_output_tokens or 0,
        ai_cost_usd=submission.ai_cost_usd or 0.0,
        ai_calls_count=submission.ai_calls_count or 0,
        processing_duration_ms=submission.processing_duration_ms,
    )


@router.delete("/{submission_id}")
async def delete_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(404, "Submission not found")
    db.delete(submission)
    db.commit()
    import shutil
    folder = os.path.join(settings.LOCAL_STORAGE_PATH, "submissions", submission_id)
    if os.path.exists(folder):
        shutil.rmtree(folder)
    return {"status": "deleted"}


@router.get("/{submission_id}/documents/{document_id}/download")
async def download_document(submission_id: str, document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(
        Document.id == document_id, Document.submission_id == submission_id
    ).first()
    if not doc or not os.path.exists(doc.file_path):
        raise HTTPException(404, "Document not found")
    return FileResponse(path=doc.file_path, filename=doc.original_filename)


# ── Rules Reference Endpoint ──────────────────────────────────

@router.get("/meta/rules")
async def get_rules_reference():
    """Return all business rules definitions for the rules viewer page."""
    from rules import RulesEngine
    engine = RulesEngine()
    return engine.get_rule_definitions()


# ── Rules Configuration Endpoints ─────────────────────────────

import json as _json

RULES_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rules_config.json")


def _load_rules_config() -> dict:
    try:
        with open(RULES_CONFIG_PATH, "r") as f:
            return _json.load(f)
    except (FileNotFoundError, _json.JSONDecodeError):
        return {"rules": {}}


def _save_rules_config(config: dict):
    with open(RULES_CONFIG_PATH, "w") as f:
        _json.dump(config, f, indent=2)


@router.get("/meta/rules-config")
async def get_rules_config():
    """Return all rules with their configuration (enabled, severity overrides)."""
    from rules import RulesEngine
    engine = RulesEngine()
    definitions = engine.get_rule_definitions()
    config = _load_rules_config()
    overrides = config.get("rules", {})

    result = []
    for rule in definitions:
        rule_id = rule["rule_id"]
        override = overrides.get(rule_id, {})
        result.append({
            **rule,
            "enabled": override.get("enabled", True),
            "severity_override": override.get("severity", None),
            "original_severity": rule["severity"],
        })
    return result


@router.put("/meta/rules-config/{rule_id}")
async def update_rule_config(rule_id: str, body: dict):
    """Update a single rule's configuration (enabled, severity)."""
    config = _load_rules_config()
    if "rules" not in config:
        config["rules"] = {}

    override = config["rules"].get(rule_id, {})
    if "enabled" in body:
        override["enabled"] = bool(body["enabled"])
    if "severity" in body:
        if body["severity"] in ("critical", "high", "medium", "low", "info"):
            override["severity"] = body["severity"]

    config["rules"][rule_id] = override
    _save_rules_config(config)
    logger.info(f"Rule config updated: {rule_id} -> {override}")
    return {"rule_id": rule_id, **override}


@router.post("/meta/rules-config/reset")
async def reset_rules_config():
    """Reset all rules to default configuration."""
    _save_rules_config({"rules": {}})
    logger.info("Rules configuration reset to defaults")
    return {"status": "reset", "message": "All rules reset to defaults"}


# ─── Helpers ─────────────────────────────────────────────────

def _to_response(s: Submission, doc_count: int) -> SubmissionResponse:
    return SubmissionResponse(
        id=s.id, email_from=s.email_from, email_subject=s.email_subject,
        email_body=s.email_body, status=s.status,
        overall_decision=s.overall_decision, decision_reason=s.decision_reason,
        received_at=s.received_at, processed_at=s.processed_at,
        created_at=s.created_at, updated_at=s.updated_at,
        document_count=doc_count,
        ai_input_tokens=s.ai_input_tokens or 0,
        ai_output_tokens=s.ai_output_tokens or 0,
        ai_cost_usd=s.ai_cost_usd or 0.0,
        ai_calls_count=s.ai_calls_count or 0,
        processing_duration_ms=s.processing_duration_ms,
    )


def _get_analysis(db: Session, submission_id: str):
    a = db.query(AnalysisResult).filter(
        AnalysisResult.submission_id == submission_id
    ).order_by(AnalysisResult.created_at.desc()).first()
    return AnalysisResultResponse.model_validate(a) if a else None
