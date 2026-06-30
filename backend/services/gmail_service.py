"""
Gmail OAuth2 Service — Handles authentication, sending, and reading emails
via the Gmail API with OAuth2 tokens.
"""
import os
import json
import base64
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Token storage path
TOKEN_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "gmail_token.json")
CREDENTIALS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "gmail_credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]


def _get_credentials() -> Optional[Credentials]:
    """Load and refresh OAuth2 credentials from stored token."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        except Exception as e:
            logger.error(f"Failed to load token: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            _save_token(creds)
            logger.info("Gmail OAuth2 token refreshed successfully")
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            creds = None

    return creds


def _save_token(creds: Credentials):
    """Persist credentials to disk."""
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())


def _get_service():
    """Build Gmail API service."""
    creds = _get_credentials()
    if not creds or not creds.valid:
        raise RuntimeError("Gmail not authenticated. Run the authorization flow first.")
    return build("gmail", "v1", credentials=creds)


def is_authenticated() -> bool:
    """Check if Gmail OAuth2 is configured and tokens are valid."""
    creds = _get_credentials()
    return creds is not None and creds.valid


def get_auth_url(client_id: str, client_secret: str, redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> str:
    """Generate the OAuth2 authorization URL for the user to visit."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    auth_url, _ = flow.authorization_url(prompt="consent", access_type="offline")
    return auth_url


def exchange_code(client_id: str, client_secret: str, code: str,
                  redirect_uri: str = "urn:ietf:wg:oauth:2.0:oob") -> dict:
    """Exchange authorization code for tokens and store them."""
    from google_auth_oauthlib.flow import Flow

    flow = Flow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        },
        scopes=SCOPES,
        redirect_uri=redirect_uri,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_token(creds)

    # Get user email
    service = build("gmail", "v1", credentials=creds)
    profile = service.users().getProfile(userId="me").execute()

    logger.info(f"Gmail OAuth2 authenticated: {profile.get('emailAddress')}")
    return {
        "status": "authenticated",
        "email": profile.get("emailAddress"),
    }


def send_email(to: str, subject: str, body: str) -> dict:
    """Send an email via Gmail API."""
    service = _get_service()

    msg = MIMEMultipart()
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    result = service.users().messages().send(
        userId="me", body={"raw": raw}
    ).execute()

    logger.info(f"Email sent via Gmail API: {result.get('id')} -> {to}")
    return {
        "status": "sent",
        "message_id": result.get("id"),
        "to": to,
    }


def get_unread_emails(max_results: int = 10) -> List[Dict]:
    """Fetch unread emails from Gmail."""
    service = _get_service()

    results = service.users().messages().list(
        userId="me",
        q="is:unread in:anywhere -from:noreply -from:no-reply -from:mailer-daemon -from:googlecloud",
        maxResults=max_results,
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg_meta in messages:
        msg = service.users().messages().get(
            userId="me", id=msg_meta["id"], format="full"
        ).execute()

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}

        email_data = {
            "id": msg_meta["id"],
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": "",
            "attachments": [],
        }

        # Extract body and attachments
        _extract_parts(service, msg_meta["id"], msg.get("payload", {}), email_data)
        emails.append(email_data)

    return emails


def _extract_parts(service, msg_id: str, payload: dict, email_data: dict):
    """Recursively extract body text and attachments from email payload."""
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})

    if mime_type == "text/plain" and not payload.get("filename"):
        data = body.get("data", "")
        if data:
            email_data["body"] += base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")

    if payload.get("filename") and body.get("attachmentId"):
        att = service.users().messages().attachments().get(
            userId="me", messageId=msg_id, id=body["attachmentId"]
        ).execute()
        email_data["attachments"].append({
            "filename": payload["filename"],
            "data": att.get("data", ""),
            "size": att.get("size", 0),
        })

    for part in payload.get("parts", []):
        _extract_parts(service, msg_id, part, email_data)


def mark_as_read(msg_id: str):
    """Mark an email as read."""
    service = _get_service()
    service.users().messages().modify(
        userId="me",
        id=msg_id,
        body={"removeLabelIds": ["UNREAD"]},
    ).execute()


def get_email_address() -> Optional[str]:
    """Get the authenticated Gmail address."""
    try:
        service = _get_service()
        profile = service.users().getProfile(userId="me").execute()
        return profile.get("emailAddress")
    except Exception:
        return None
