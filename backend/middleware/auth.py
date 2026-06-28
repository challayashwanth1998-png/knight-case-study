"""
API Key Authentication Middleware.

Protects sensitive endpoints with X-API-Key header validation.
Can be disabled via REQUIRE_API_KEY=false in .env for development.

Public endpoints (health, docs, static) are always accessible.
"""
import os
import secrets
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("knight.auth")

# ── Configuration ────────────────────────────────────────────
# If no API key is set, auto-generate one and log it at startup
_configured_key = os.environ.get("KNIGHT_API_KEY", "")
_require_auth = os.environ.get("REQUIRE_API_KEY", "false").lower() == "true"

if _require_auth and not _configured_key:
    _configured_key = secrets.token_urlsafe(32)
    logger.warning(f"No KNIGHT_API_KEY set. Auto-generated key: {_configured_key}")

# Endpoints that never require auth
PUBLIC_PATHS = {
    "/api/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

PUBLIC_PREFIXES = (
    "/architecture",
    "/_next",
    "/static",
)


class ApiKeyMiddleware(BaseHTTPMiddleware):
    """
    Validates X-API-Key header on protected endpoints.

    - Returns 401 for missing key
    - Returns 403 for invalid key
    - Passes through for public endpoints
    - Disabled when REQUIRE_API_KEY=false (default for dev)
    """

    async def dispatch(self, request: Request, call_next):
        # Skip auth if disabled
        if not _require_auth:
            return await call_next(request)

        path = request.url.path

        # Public endpoints — no auth required
        if path in PUBLIC_PATHS or path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        # GET on non-mutating list endpoints — allow without auth for demo
        if request.method == "GET" and path.startswith("/api/submissions"):
            return await call_next(request)

        # Check API key
        api_key = request.headers.get("X-API-Key", "")

        if not api_key:
            logger.warning(f"Missing API key on {request.method} {path}")
            return JSONResponse(
                status_code=401,
                content={"detail": "API key required. Provide X-API-Key header."},
            )

        if not secrets.compare_digest(api_key, _configured_key):
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Invalid API key from {client_ip} on {request.method} {path}")
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid API key."},
            )

        return await call_next(request)
