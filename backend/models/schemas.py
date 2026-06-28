"""
Knight Insurance — Pydantic Schemas for API requests/responses.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any
from datetime import datetime


# ─── Submission ───────────────────────────────────────────────

class SubmissionCreate(BaseModel):
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    filename: str
    original_filename: str
    file_type: str
    file_size: Optional[int] = None
    classified_type: Optional[str] = None
    classification_confidence: Optional[float] = None
    quality_score: Optional[float] = None
    processing_status: str
    extracted_data: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class RuleResultResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    category: str
    result: str
    severity: str
    details: Optional[str] = None
    data_used: Optional[Any] = None

    class Config:
        from_attributes = True


class AnalysisResultResponse(BaseModel):
    id: str
    summary: Optional[str] = None
    business_profile: Optional[Any] = None
    completeness_report: Optional[Any] = None
    conflicts: Optional[Any] = None
    risk_assessment: Optional[Any] = None
    recommendations: Optional[Any] = None
    confidence_score: Optional[float] = None
    unified_business_info: Optional[Any] = None
    unified_drivers: Optional[Any] = None
    unified_vehicles: Optional[Any] = None
    unified_ifta: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: str
    action: str
    details: Optional[str] = None
    step_number: Optional[int] = None
    timestamp: datetime

    class Config:
        from_attributes = True


# ─── AI Metrics ───────────────────────────────────────────────

class AIMetrics(BaseModel):
    ai_input_tokens: int = 0
    ai_output_tokens: int = 0
    ai_cost_usd: float = 0.0
    ai_calls_count: int = 0
    processing_duration_ms: Optional[int] = None


# ─── Submission Responses ─────────────────────────────────────

class SubmissionResponse(BaseModel):
    id: str
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    status: str
    overall_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    document_count: Optional[int] = None
    # AI Metrics
    ai_input_tokens: int = 0
    ai_output_tokens: int = 0
    ai_cost_usd: float = 0.0
    ai_calls_count: int = 0
    processing_duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


class SubmissionDetailResponse(BaseModel):
    id: str
    email_from: Optional[str] = None
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    status: str
    overall_decision: Optional[str] = None
    decision_reason: Optional[str] = None
    received_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    documents: List[DocumentResponse] = []
    analysis: Optional[AnalysisResultResponse] = None
    rules: List[RuleResultResponse] = []
    audit_log: List[AuditLogResponse] = []
    # AI Metrics
    ai_input_tokens: int = 0
    ai_output_tokens: int = 0
    ai_cost_usd: float = 0.0
    ai_calls_count: int = 0
    processing_duration_ms: Optional[int] = None

    class Config:
        from_attributes = True


# ─── Pipeline ─────────────────────────────────────────────────

class PipelineStatus(BaseModel):
    submission_id: str
    status: str
    current_step: str
    steps_completed: List[str]
    errors: List[str] = []


# ─── Stats ────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_submissions: int = 0
    pending: int = 0
    processing: int = 0
    complete: int = 0
    accepted: int = 0
    declined: int = 0
    referred: int = 0


# ─── Rules Reference ─────────────────────────────────────────

class RuleDefinition(BaseModel):
    rule_id: str
    rule_name: str
    category: str
    severity: str
    description: str


# ─── Validation Error ─────────────────────────────────────────

class ValidationErrorResponse(BaseModel):
    detail: str
    errors: List[str] = []
