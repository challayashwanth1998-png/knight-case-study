"""
Security Middleware — Headers, Rate Limiting, Request Tracking, Logging.

Provides enterprise-grade security hardening for all HTTP responses:
- Security headers (OWASP recommended)
- Sliding-window rate limiting per client IP
- Unique request ID for traceability
- Structured request/response logging with timing
"""
import time
import uuid
import logging
from collections import defaultdict
from threading import Lock
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

logger = logging.getLogger("knight.security")

# ──────────────────────────────────────────────────────────────
# 1. Security Headers Middleware
# ──────────────────────────────────────────────────────────────

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self' *; "
        "frame-src 'self'"
    ),
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds OWASP-recommended security headers to every response."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


# ──────────────────────────────────────────────────────────────
# 2. Rate Limiting Middleware
# ──────────────────────────────────────────────────────────────

class RateLimiter:
    """Sliding-window rate limiter per client IP."""

    def __init__(self, general_limit: int = 120, upload_limit: int = 10, window_seconds: int = 60):
        self.general_limit = general_limit
        self.upload_limit = upload_limit
        self.window = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _cleanup(self, key: str, now: float):
        """Remove timestamps outside the current window."""
        cutoff = now - self.window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def is_allowed(self, client_ip: str, path: str) -> tuple[bool, int, int]:
        """
        Check if request is allowed.
        Returns (allowed, remaining, limit).
        """
        now = time.time()

        # Determine limit based on endpoint
        is_sensitive = any(p in path for p in ["/upload", "/process", "/delete"])
        limit = self.upload_limit if is_sensitive else self.general_limit
        key = f"{client_ip}:{'sensitive' if is_sensitive else 'general'}"

        with self._lock:
            self._cleanup(key, now)
            count = len(self._requests[key])

            if count >= limit:
                return False, 0, limit

            self._requests[key].append(now)
            return True, limit - count - 1, limit


_rate_limiter = RateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforces per-IP rate limits with standard rate limit headers."""

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ("/api/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed, remaining, limit = _rate_limiter.is_allowed(client_ip, request.url.path)

        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response


# ──────────────────────────────────────────────────────────────
# 3. Request ID Middleware
# ──────────────────────────────────────────────────────────────

class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attaches a unique X-Request-ID to every request/response for traceability."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:12])
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ──────────────────────────────────────────────────────────────
# 4. Request Logging Middleware
# ──────────────────────────────────────────────────────────────

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs every API request with method, path, status, duration, and client IP."""

    # Skip logging for noisy endpoints
    SKIP_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.SKIP_PATHS:
            return await call_next(request)

        start = time.time()
        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "-")

        try:
            response = await call_next(request)
            duration = (time.time() - start) * 1000  # ms

            logger.info(
                f"{request.method} {request.url.path} "
                f"→ {response.status_code} "
                f"({duration:.0f}ms) "
                f"[ip={client_ip} rid={request_id}]"
            )
            response.headers["X-Response-Time"] = f"{duration:.0f}ms"
            return response

        except Exception as e:
            duration = (time.time() - start) * 1000
            logger.error(
                f"{request.method} {request.url.path} "
                f"→ ERROR ({duration:.0f}ms) "
                f"[ip={client_ip} rid={request_id}]: {e}"
            )
            raise
