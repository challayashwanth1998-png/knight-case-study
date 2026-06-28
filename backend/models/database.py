"""
Knight Insurance — Database Models (SQLAlchemy)
Supports SQLite for local dev, PostgreSQL (RDS) for production.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, String, Text, Integer, Float,
    DateTime, JSON, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from config import settings

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Submission(Base):
    """A single insurance submission (one email with attachments)."""
    __tablename__ = "submissions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email_from = Column(String(255), nullable=True)
    email_subject = Column(String(500), nullable=True)
    email_body = Column(Text, nullable=True)
    email_date = Column(DateTime, nullable=True)

    # Processing status
    status = Column(
        String(20),
        default="received",
        # received -> processing -> analyzed -> complete -> error
    )
    overall_decision = Column(String(20), nullable=True)  # accept, decline, refer
    decision_reason = Column(Text, nullable=True)

    # Timestamps
    received_at = Column(DateTime, default=utcnow)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # AI Metrics
    ai_input_tokens = Column(Integer, default=0)
    ai_output_tokens = Column(Integer, default=0)
    ai_cost_usd = Column(Float, default=0.0)
    ai_calls_count = Column(Integer, default=0)
    processing_duration_ms = Column(Integer, nullable=True)

    # Relationships
    documents = relationship("Document", back_populates="submission", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="submission", cascade="all, delete-orphan")
    rule_results = relationship("RuleResult", back_populates="submission", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="submission", cascade="all, delete-orphan")


class Document(Base):
    """A single document/attachment within a submission."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)

    # File info
    filename = Column(String(500), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)  # S3 key or local path
    file_type = Column(String(50), nullable=False)  # pdf, xlsx, png, jpg, docx
    file_size = Column(Integer, nullable=True)
    storage_type = Column(String(10), default="local")  # local or s3

    # Classification
    classified_type = Column(String(50), nullable=True)
    # insurance_application, driver_list, equipment_list, ifta_report,
    # loss_run, motor_vehicle_record, drivers_license, other
    classification_confidence = Column(Float, nullable=True)

    # Extracted content
    extracted_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    quality_score = Column(Float, nullable=True)  # 0.0 to 1.0

    # Processing
    processing_status = Column(String(20), default="pending")
    # pending -> extracting -> classifying -> extracted -> error
    processing_error = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="documents")


class AnalysisResult(Base):
    """AI-powered analysis results for a submission."""
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)

    # Analysis outputs
    summary = Column(Text, nullable=True)
    business_profile = Column(JSON, nullable=True)
    completeness_report = Column(JSON, nullable=True)
    conflicts = Column(JSON, nullable=True)  # Array of conflict objects
    risk_assessment = Column(JSON, nullable=True)
    recommendations = Column(JSON, nullable=True)  # Array of recommendation objects
    confidence_score = Column(Float, nullable=True)

    # Extracted unified data
    unified_business_info = Column(JSON, nullable=True)
    unified_drivers = Column(JSON, nullable=True)
    unified_vehicles = Column(JSON, nullable=True)
    unified_ifta = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    submission = relationship("Submission", back_populates="analysis_results")


class RuleResult(Base):
    """Individual business rule evaluation result."""
    __tablename__ = "rule_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)

    rule_id = Column(String(20), nullable=False)       # e.g., "ELIG-001"
    rule_name = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)       # eligibility, driver, exposure, submission
    result = Column(String(20), nullable=False)         # PASS, FAIL, WARNING, INFO, SKIP
    severity = Column(String(20), nullable=False)       # critical, high, medium, low
    details = Column(Text, nullable=True)
    data_used = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=utcnow)

    submission = relationship("Submission", back_populates="rule_results")


class AuditLog(Base):
    """Audit trail for all actions on a submission."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    submission_id = Column(String(36), ForeignKey("submissions.id"), nullable=False)

    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    step_number = Column(Integer, nullable=True)  # Pipeline step 1-6
    timestamp = Column(DateTime, default=utcnow)

    submission = relationship("Submission", back_populates="audit_logs")


# --- Database Engine & Session ---

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for FastAPI route injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
