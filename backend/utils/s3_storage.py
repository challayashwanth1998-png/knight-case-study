"""
AWS S3 storage helper for document uploads.
Provides upload, download, and URL generation for submission documents.
"""
import logging
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

S3_BUCKET = "knight-insurance-docs-264787847844"
S3_REGION = "us-east-1"

# Lazy client
_s3_client = None


def _get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=S3_REGION,
            config=BotoConfig(retries={"max_attempts": 3, "mode": "adaptive"}),
        )
    return _s3_client


def upload_to_s3(
    file_content: bytes,
    submission_id: str,
    filename: str,
    content_type: str = "application/octet-stream",
) -> Optional[str]:
    """
    Upload a file to S3 and return the S3 key.
    Returns None if upload fails (falls back to local storage).
    """
    s3_key = f"submissions/{submission_id}/{filename}"
    try:
        client = _get_client()
        client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type,
        )
        logger.info(f"Uploaded to S3: s3://{S3_BUCKET}/{s3_key} ({len(file_content)} bytes)")
        return s3_key
    except ClientError as e:
        logger.warning(f"S3 upload failed for {s3_key}: {e}. Using local storage only.")
        return None
    except Exception as e:
        logger.warning(f"S3 upload error for {s3_key}: {e}. Using local storage only.")
        return None


def download_from_s3(s3_key: str) -> Optional[bytes]:
    """Download a file from S3. Returns None if not found."""
    try:
        client = _get_client()
        response = client.get_object(Bucket=S3_BUCKET, Key=s3_key)
        return response["Body"].read()
    except ClientError:
        return None


def get_presigned_url(s3_key: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a presigned URL for temporary access to an S3 object."""
    try:
        client = _get_client()
        return client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": s3_key},
            ExpiresIn=expires_in,
        )
    except ClientError:
        return None
