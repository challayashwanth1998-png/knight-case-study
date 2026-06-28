"""
Input validation guardrails for file uploads and submissions.
"""
import os
import hashlib
import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────
ALLOWED_EXTENSIONS = {
    ".pdf", ".xlsx", ".xls", ".docx", ".doc",
    ".csv", ".txt", ".png", ".jpg", ".jpeg",
    ".tiff", ".tif", ".bmp", ".gif",
}

MAX_FILE_SIZE_MB = 25
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

MAX_FILES_PER_SUBMISSION = 20

# Characters not allowed in filenames
UNSAFE_CHARS = re.compile(r'[<>:"|?*\x00-\x1f]')
PATH_TRAVERSAL = re.compile(r'\.\.[\\/]')


def validate_file_type(filename: str) -> Tuple[bool, str]:
    """Check if file extension is in the allowlist."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False, (
            f"File type '{ext}' is not allowed. "
            f"Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    return True, ""


def validate_file_size(size: int, max_mb: int = MAX_FILE_SIZE_MB) -> Tuple[bool, str]:
    """Check if file size is within limits."""
    max_bytes = max_mb * 1024 * 1024
    if size > max_bytes:
        size_mb = round(size / (1024 * 1024), 1)
        return False, f"File size ({size_mb}MB) exceeds maximum ({max_mb}MB)"
    if size == 0:
        return False, "File is empty (0 bytes)"
    return True, ""


def validate_submission_limits(file_count: int) -> Tuple[bool, str]:
    """Check if number of files is within limits."""
    if file_count == 0:
        return False, "No files provided. At least 1 file is required."
    if file_count > MAX_FILES_PER_SUBMISSION:
        return False, (
            f"Too many files ({file_count}). "
            f"Maximum {MAX_FILES_PER_SUBMISSION} files per submission."
        )
    return True, ""


def sanitize_filename(name: str) -> str:
    """Clean filename of dangerous characters."""
    # Remove path components
    name = os.path.basename(name)
    # Remove path traversal
    name = PATH_TRAVERSAL.sub("", name)
    # Remove unsafe characters
    name = UNSAFE_CHARS.sub("_", name)
    # Replace slashes
    name = name.replace("/", "_").replace("\\", "_")
    # Limit length
    if len(name) > 200:
        base, ext = os.path.splitext(name)
        name = base[:195] + ext
    return name or "unnamed_file"


def compute_file_hash(content: bytes) -> str:
    """Compute SHA-256 hash for deduplication."""
    return hashlib.sha256(content).hexdigest()


def check_duplicates(hashes: list[str]) -> list[int]:
    """Return indices of duplicate files (keeps first occurrence)."""
    seen = {}
    duplicates = []
    for i, h in enumerate(hashes):
        if h in seen:
            duplicates.append(i)
        else:
            seen[h] = i
    return duplicates
