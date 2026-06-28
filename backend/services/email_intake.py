"""
Knight Insurance — Email Intake Service
Handles two modes:
  1. Simulated upload via REST API (drag & drop)
  2. AWS SES inbound email via S3 trigger
  3. IMAP polling (bonus — real email monitoring)
"""
import os
import uuid
import email
import logging
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime, timezone

import boto3
from config import settings

logger = logging.getLogger(__name__)


class EmailIntakeService:
    """Handles email/document intake from multiple sources."""

    def __init__(self):
        self.storage_path = settings.LOCAL_STORAGE_PATH
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize S3 client if AWS is configured
        self.s3_client = None
        if settings.AWS_ACCESS_KEY_ID:
            try:
                self.s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
            except Exception as e:
                logger.warning(f"Could not initialize S3 client: {e}")
        else:
            # Try default credentials
            try:
                self.s3_client = boto3.client("s3", region_name=settings.AWS_REGION)
            except Exception:
                pass

    def create_submission_folder(self, submission_id: str) -> str:
        """Create a local folder for a submission's documents."""
        folder = os.path.join(self.storage_path, "submissions", submission_id)
        os.makedirs(folder, exist_ok=True)
        return folder

    def save_uploaded_file(self, submission_id: str, filename: str,
                           file_content: bytes) -> Tuple[str, str]:
        """
        Save an uploaded file locally and optionally to S3.

        Returns:
            Tuple of (local_path, s3_key_or_empty)
        """
        folder = self.create_submission_folder(submission_id)

        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        local_path = os.path.join(folder, safe_filename)

        # Save locally
        with open(local_path, "wb") as f:
            f.write(file_content)

        logger.info(f"Saved file: {local_path} ({len(file_content)} bytes)")

        # Upload to S3 if available
        s3_key = ""
        if self.s3_client:
            try:
                s3_key = f"submissions/{submission_id}/{safe_filename}"
                self.s3_client.put_object(
                    Bucket=settings.S3_BUCKET_DOCUMENTS,
                    Key=s3_key,
                    Body=file_content,
                    ContentType=self._get_content_type(safe_filename)
                )
                logger.info(f"Uploaded to S3: s3://{settings.S3_BUCKET_DOCUMENTS}/{s3_key}")
            except Exception as e:
                logger.warning(f"S3 upload failed (continuing with local): {e}")
                s3_key = ""

        return local_path, s3_key

    def process_ses_email(self, s3_bucket: str, s3_key: str) -> dict:
        """
        Process an inbound email from AWS SES (stored in S3).

        Returns:
            Dict with email metadata and list of saved attachment paths
        """
        if not self.s3_client:
            raise RuntimeError("S3 client not available")

        # Download raw email from S3
        response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
        raw_email = response["Body"].read()

        # Parse email
        msg = email.message_from_bytes(raw_email)

        email_from = msg.get("From", "unknown")
        email_subject = msg.get("Subject", "No Subject")
        email_date = msg.get("Date")
        email_body = ""

        submission_id = str(uuid.uuid4())
        saved_files = []

        # Extract body and attachments
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            if content_type == "text/plain" and "attachment" not in disposition:
                email_body += part.get_payload(decode=True).decode("utf-8", errors="replace")
            elif "attachment" in disposition or content_type.startswith(("application/", "image/")):
                filename = part.get_filename()
                if filename:
                    file_content = part.get_payload(decode=True)
                    if file_content:
                        local_path, s3_path = self.save_uploaded_file(
                            submission_id, filename, file_content
                        )
                        saved_files.append({
                            "filename": filename,
                            "local_path": local_path,
                            "s3_key": s3_path,
                            "size": len(file_content)
                        })

        return {
            "submission_id": submission_id,
            "email_from": email_from,
            "email_subject": email_subject,
            "email_body": email_body,
            "email_date": email_date,
            "attachments": saved_files
        }

    def check_imap_inbox(self) -> List[dict]:
        """
        Poll IMAP inbox for new emails with attachments.
        Returns list of processed email dicts.
        """
        if not all([settings.IMAP_HOST, settings.IMAP_USERNAME, settings.IMAP_PASSWORD]):
            logger.warning("IMAP not configured. Skipping inbox check.")
            return []

        try:
            from imapclient import IMAPClient

            with IMAPClient(settings.IMAP_HOST, port=settings.IMAP_PORT, ssl=True) as client:
                client.login(settings.IMAP_USERNAME, settings.IMAP_PASSWORD)
                client.select_folder("INBOX")

                # Search for unread emails
                messages = client.search(["UNSEEN"])
                results = []

                for msg_id in messages:
                    raw = client.fetch([msg_id], ["RFC822"])
                    raw_email = raw[msg_id][b"RFC822"]
                    msg = email.message_from_bytes(raw_email)

                    email_from = msg.get("From", "unknown")
                    email_subject = msg.get("Subject", "No Subject")
                    email_body = ""
                    submission_id = str(uuid.uuid4())
                    saved_files = []

                    for part in msg.walk():
                        content_type = part.get_content_type()
                        disposition = str(part.get("Content-Disposition", ""))

                        if content_type == "text/plain" and "attachment" not in disposition:
                            payload = part.get_payload(decode=True)
                            if payload:
                                email_body += payload.decode("utf-8", errors="replace")
                        elif "attachment" in disposition or content_type.startswith(("application/", "image/")):
                            filename = part.get_filename()
                            if filename:
                                file_content = part.get_payload(decode=True)
                                if file_content:
                                    local_path, s3_path = self.save_uploaded_file(
                                        submission_id, filename, file_content
                                    )
                                    saved_files.append({
                                        "filename": filename,
                                        "local_path": local_path,
                                        "s3_key": s3_path,
                                        "size": len(file_content)
                                    })

                    if saved_files:  # Only process emails with attachments
                        results.append({
                            "submission_id": submission_id,
                            "email_from": email_from,
                            "email_subject": email_subject,
                            "email_body": email_body,
                            "attachments": saved_files
                        })

                    # Mark as read
                    client.set_flags([msg_id], [b"\\Seen"])

                return results

        except Exception as e:
            logger.error(f"IMAP check failed: {e}")
            return []

    def get_s3_download_url(self, s3_key: str, expiry: int = 3600) -> Optional[str]:
        """Generate a pre-signed URL for downloading a file from S3."""
        if not self.s3_client:
            return None
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": settings.S3_BUCKET_DOCUMENTS, "Key": s3_key},
                ExpiresIn=expiry
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            return None

    def _sanitize_filename(self, filename: str) -> str:
        """Make a filename safe for the filesystem."""
        # Keep original name but ensure it's safe
        safe = filename.replace("/", "_").replace("\\", "_")
        return safe

    def _get_content_type(self, filename: str) -> str:
        """Determine content type from filename."""
        ext = Path(filename).suffix.lower()
        types = {
            ".pdf": "application/pdf",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".csv": "text/csv",
        }
        return types.get(ext, "application/octet-stream")
