"""
Knight Insurance — IMAP IDLE Email Watcher
Maintains a persistent connection to the mail server and reacts INSTANTLY
when a new email arrives (no polling delay). Uses IMAP IDLE (RFC 2177).
"""
import os
import uuid
import email
import logging
import threading
import time
from typing import Optional
from datetime import datetime, timezone
from email.header import decode_header

from imapclient import IMAPClient

from config import settings

logger = logging.getLogger(__name__)

# Allowed attachment extensions
ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".docx", ".doc", ".csv", ".txt", ".png", ".jpg", ".jpeg"}
MAX_ATTACHMENT_SIZE = 25 * 1024 * 1024  # 25MB


class EmailWatcher:
    """
    Watches an IMAP inbox using IDLE (push) for instant email processing.
    When a new email with attachments arrives, it creates a submission
    via the same pipeline as the UI upload.
    """

    def __init__(self):
        self.host = settings.IMAP_HOST
        self.port = settings.IMAP_PORT
        self.username = settings.IMAP_USERNAME
        self.password = settings.IMAP_PASSWORD
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._client: Optional[IMAPClient] = None

    @property
    def is_configured(self) -> bool:
        return all([self.host, self.username, self.password])

    def start(self):
        """Start the email watcher in a background thread."""
        if not self.is_configured:
            logger.warning("Email watcher not configured (IMAP_HOST/USERNAME/PASSWORD missing). Skipping.")
            return

        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True, name="email-watcher")
        self._thread.start()
        logger.info(f"📧 Email watcher started for {self.username} on {self.host}")

    def stop(self):
        """Stop the email watcher gracefully."""
        self._running = False
        if self._client:
            try:
                self._client.idle_done()
                self._client.logout()
            except Exception:
                pass
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Email watcher stopped.")

    def _watch_loop(self):
        """
        Main loop: connect → process existing unread → IDLE wait → repeat.
        Automatically reconnects on failures.
        """
        while self._running:
            try:
                self._connect()
                self._process_unread()  # Process any emails that arrived while we were disconnected
                self._idle_wait()
            except Exception as e:
                logger.error(f"Email watcher error: {e}")
                self._disconnect()
                if self._running:
                    logger.info("Reconnecting in 10 seconds...")
                    time.sleep(10)

    def _connect(self):
        """Establish IMAP connection with SSL."""
        logger.info(f"Connecting to {self.host}:{self.port}...")
        self._client = IMAPClient(self.host, port=self.port, ssl=True, timeout=30)
        self._client.login(self.username, self.password)
        self._client.select_folder("INBOX")
        logger.info(f"✅ Connected to IMAP inbox: {self.username}")

    def _disconnect(self):
        """Safely disconnect."""
        if self._client:
            try:
                self._client.logout()
            except Exception:
                pass
            self._client = None

    def _idle_wait(self):
        """
        Enter IMAP IDLE mode — the server pushes notifications instantly
        when a new email arrives. Re-enters IDLE every 4 minutes to keep
        the connection alive (most servers timeout at 5 min).
        """
        while self._running:
            self._client.idle()
            logger.debug("IDLE mode entered, waiting for new email...")

            # Wait up to 4 minutes for a new email notification
            responses = self._client.idle_check(timeout=240)

            # Exit IDLE to process
            self._client.idle_done()

            if responses:
                # New mail arrived — process it immediately
                logger.info(f"📬 IDLE notification received: {len(responses)} event(s)")
                self._process_unread()
            else:
                # Timeout — re-enter IDLE (keeps connection alive)
                logger.debug("IDLE timeout, re-entering...")

    def _process_unread(self):
        """Fetch and process all unread emails with attachments."""
        try:
            messages = self._client.search(["UNSEEN"])
            if not messages:
                return

            logger.info(f"📧 Found {len(messages)} unread email(s)")

            for msg_id in messages:
                try:
                    self._process_email(msg_id)
                except Exception as e:
                    logger.error(f"Failed to process email {msg_id}: {e}")
                    # Still mark as read to avoid infinite retries
                    self._client.set_flags([msg_id], [b"\\Seen"])

        except Exception as e:
            logger.error(f"Error fetching unread emails: {e}")

    def _process_email(self, msg_id: int):
        """Process a single email: extract attachments, create submission."""
        raw = self._client.fetch([msg_id], ["RFC822"])
        raw_email = raw[msg_id][b"RFC822"]
        msg = email.message_from_bytes(raw_email)

        # Parse headers
        email_from = self._decode_header(msg.get("From", "unknown"))
        email_subject = self._decode_header(msg.get("Subject", "No Subject"))
        email_body = ""
        attachments = []

        # Walk email parts
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))

            # Extract plain text body
            if content_type == "text/plain" and "attachment" not in disposition:
                payload = part.get_payload(decode=True)
                if payload:
                    email_body += payload.decode("utf-8", errors="replace")

            # Extract attachments
            elif "attachment" in disposition or content_type.startswith(("application/", "image/")):
                filename = part.get_filename()
                if filename:
                    filename = self._decode_header(filename)
                    ext = os.path.splitext(filename)[1].lower()

                    if ext not in ALLOWED_EXTENSIONS:
                        logger.info(f"Skipping unsupported attachment: {filename}")
                        continue

                    file_content = part.get_payload(decode=True)
                    if file_content and len(file_content) <= MAX_ATTACHMENT_SIZE:
                        attachments.append({
                            "filename": filename,
                            "content": file_content,
                        })

        if not attachments:
            logger.info(f"Email from {email_from} has no valid attachments, skipping.")
            self._client.set_flags([msg_id], [b"\\Seen"])
            return

        # Create submission
        submission_id = self._create_submission(email_from, email_subject, email_body, attachments)
        logger.info(
            f"✅ Created submission {submission_id[:8]} from email: "
            f"{email_from} — {email_subject} ({len(attachments)} attachment(s))"
        )

        # Mark as read
        self._client.set_flags([msg_id], [b"\\Seen"])

    def _create_submission(self, email_from: str, email_subject: str,
                           email_body: str, attachments: list) -> str:
        """
        Create a submission record and trigger the processing pipeline.
        This reuses the same database models and pipeline as the UI upload.
        """
        # Lazy import to avoid circular imports
        from models.database import SessionLocal, Submission, Document, AuditLog
        from utils.s3_storage import upload_to_s3
        from utils.validators import sanitize_filename, compute_file_hash

        submission_id = str(uuid.uuid4())
        folder = os.path.join(settings.LOCAL_STORAGE_PATH, "submissions", submission_id)
        os.makedirs(folder, exist_ok=True)

        db = SessionLocal()
        try:
            # Create submission record
            submission = Submission(
                id=submission_id,
                email_from=email_from,
                email_subject=email_subject,
                email_body=email_body,
                status="received",
                received_at=datetime.now(timezone.utc),
            )
            db.add(submission)

            # Save each attachment
            for att in attachments:
                safe_name = sanitize_filename(att["filename"])
                path = os.path.join(folder, safe_name)

                # Save to local disk
                with open(path, "wb") as f:
                    f.write(att["content"])

                # Upload to S3
                s3_key = upload_to_s3(att["content"], submission_id, safe_name)

                ext = os.path.splitext(safe_name)[1].lower()
                type_map = {
                    ".pdf": "pdf", ".xlsx": "xlsx", ".xls": "xls",
                    ".docx": "docx", ".png": "image", ".jpg": "image",
                    ".jpeg": "image", ".csv": "csv", ".txt": "text",
                }

                db.add(Document(
                    id=str(uuid.uuid4()),
                    submission_id=submission_id,
                    filename=safe_name,
                    original_filename=att["filename"],
                    file_path=path,
                    file_type=type_map.get(ext, "unknown"),
                    file_size=len(att["content"]),
                    storage_type="s3" if s3_key else "local",
                    processing_status="pending",
                ))

            # Audit log
            db.add(AuditLog(
                submission_id=submission_id,
                action="submission_created",
                details=f"Email intake from {email_from}: {email_subject} ({len(attachments)} files)",
            ))

            db.commit()

            # Trigger pipeline in background thread
            threading.Thread(
                target=self._run_pipeline,
                args=(submission_id,),
                daemon=True,
                name=f"pipeline-{submission_id[:8]}",
            ).start()

            return submission_id

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create submission from email: {e}")
            raise
        finally:
            db.close()

    def _run_pipeline(self, submission_id: str):
        """Run the AI processing pipeline for a submission."""
        try:
            from services.pipeline import run_pipeline
            run_pipeline(submission_id)
            logger.info(f"✅ Pipeline complete for {submission_id[:8]}")
        except Exception as e:
            logger.error(f"Pipeline failed for {submission_id[:8]}: {e}")

    def _decode_header(self, value: str) -> str:
        """Decode RFC 2047 encoded email headers."""
        if not value:
            return ""
        try:
            parts = decode_header(value)
            decoded = []
            for part, charset in parts:
                if isinstance(part, bytes):
                    decoded.append(part.decode(charset or "utf-8", errors="replace"))
                else:
                    decoded.append(part)
            return " ".join(decoded)
        except Exception:
            return str(value)


# Singleton instance
_watcher: Optional[EmailWatcher] = None


def get_email_watcher() -> EmailWatcher:
    global _watcher
    if _watcher is None:
        _watcher = EmailWatcher()
    return _watcher
