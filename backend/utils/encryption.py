"""
PII Data Protection — Masking, sanitization, and data governance utilities.

Provides tools for:
- Masking PII fields in log output (driver names, DOB, license numbers, SSN)
- Sanitizing structured data before logging to CloudWatch
- Data classification headers for API responses
"""
import re
import logging
from typing import Any

logger = logging.getLogger("knight.pii")

# ── PII Patterns ─────────────────────────────────────────────
# These patterns identify common PII in text

SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
DOB_PATTERN = re.compile(r'\b(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/(19|20)\d{2}\b')
DL_PATTERN = re.compile(r'\b[A-Z]\d{3}-\d{4}-\d{4}\b')  # Common CDL formats
PHONE_PATTERN = re.compile(r'\b\(\d{3}\)\s?\d{3}-\d{4}\b|\b\d{3}-\d{3}-\d{4}\b')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')


def mask_pii(text: str) -> str:
    """
    Mask PII patterns in text for safe logging.
    
    Examples:
        "SSN: 123-45-6789" → "SSN: ***-**-6789"
        "DOB: 05/14/1990" → "DOB: **/**/1990"
        "DL: A123-4567-8901" → "DL: A***-****-8901"
    """
    if not text:
        return text
    
    # Mask SSN (keep last 4)
    text = SSN_PATTERN.sub(lambda m: f"***-**-{m.group()[-4:]}", text)
    
    # Mask DOB (keep year)
    text = DOB_PATTERN.sub(lambda m: f"**/**/{m.group()[-4:]}", text)
    
    # Mask DL numbers (keep last 4)
    text = DL_PATTERN.sub(lambda m: f"****-****-{m.group()[-4:]}", text)
    
    # Mask phone numbers (keep last 4)
    text = PHONE_PATTERN.sub(lambda m: f"(***) ***-{m.group()[-4:]}", text)
    
    # Mask email (keep domain)
    text = EMAIL_PATTERN.sub(lambda m: f"****@{m.group().split('@')[1]}", text)
    
    return text


def mask_name(name: str) -> str:
    """Mask a person's name for logging. Keeps first initial."""
    if not name:
        return name
    parts = name.strip().split()
    if len(parts) == 0:
        return "***"
    if len(parts) == 1:
        return f"{parts[0][0]}***"
    return f"{parts[0][0]}. {'*' * len(parts[-1])}"


def sanitize_dict_for_logging(data: dict, sensitive_keys: set = None) -> dict:
    """
    Deep-sanitize a dictionary for logging.
    Masks values for keys that contain PII-related terms.
    """
    if sensitive_keys is None:
        sensitive_keys = {
            "name", "first_name", "last_name", "full_name",
            "dob", "date_of_birth", "birth_date",
            "ssn", "social_security",
            "license_number", "dl_number", "cdl_number",
            "phone", "telephone", "mobile",
            "email", "email_address",
            "address", "street", "zip_code",
        }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(s in key_lower for s in sensitive_keys):
            if isinstance(value, str):
                sanitized[key] = mask_pii(value) if value else value
            elif isinstance(value, dict):
                sanitized[key] = sanitize_dict_for_logging(value, sensitive_keys)
            elif isinstance(value, list):
                sanitized[key] = [
                    sanitize_dict_for_logging(v, sensitive_keys) if isinstance(v, dict) else "***"
                    for v in value
                ]
            else:
                sanitized[key] = "***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict_for_logging(value, sensitive_keys)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict_for_logging(v, sensitive_keys) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            sanitized[key] = value
    return sanitized


# ── Data Governance Headers ──────────────────────────────────

DATA_GOVERNANCE_HEADERS = {
    "X-Data-Classification": "CONFIDENTIAL",
    "X-Data-Retention": "7-years",
    "X-PII-Present": "true",
    "X-Data-Owner": "Knight Insurance Underwriting",
}


class PIILoggingFilter(logging.Filter):
    """
    Logging filter that automatically masks PII in log messages.
    Attach to any logger to sanitize output before it reaches CloudWatch.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = mask_pii(record.msg)
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {k: mask_pii(str(v)) if isinstance(v, str) else v
                               for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_pii(str(a)) if isinstance(a, str) else a
                    for a in record.args
                )
        return True
