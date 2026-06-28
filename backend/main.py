"""
Knight Insurance — FastAPI server with enterprise security middleware.
All heavy imports deferred to first request to work under memory pressure.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Security middleware
from middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    RequestIdMiddleware,
    RequestLoggingMiddleware,
)
from middleware.auth import ApiKeyMiddleware
from utils.encryption import PIILoggingFilter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# Attach PII filter to root logger — sanitizes all log output
logging.getLogger().addFilter(PIILoggingFilter())

_loaded = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _loaded
    logger.info("Starting Knight Insurance (deferred loading)...")
    # Defer all heavy imports to avoid memory pressure at startup
    try:
        from models.database import init_db
        init_db()
        logger.info("Database initialized.")

        # Initialize CloudWatch logging (non-blocking, falls back gracefully)
        try:
            from utils.cloudwatch import init_cloudwatch_logging, CloudWatchHandler
            init_cloudwatch_logging()
            cw_handler = CloudWatchHandler()
            cw_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
            logging.getLogger().addHandler(cw_handler)
            logger.info("CloudWatch logging enabled.")
        except Exception as cw_err:
            logger.warning(f"CloudWatch setup skipped: {cw_err}")

        from routers.submissions import router
        app.include_router(router)
        logger.info("Router loaded.")

        # Start email watcher (IMAP IDLE — instant processing)
        email_watcher = None
        try:
            from services.email_watcher import get_email_watcher
            email_watcher = get_email_watcher()
            email_watcher.start()
        except Exception as ew_err:
            logger.warning(f"Email watcher setup skipped: {ew_err}")

        _loaded = True
        logger.info("✅ Knight Insurance ready — security middleware active.")
    except Exception as e:
        logger.error(f"Failed to load: {e}")
        import traceback
        traceback.print_exc()
    yield
    # Shutdown
    if email_watcher:
        email_watcher.stop()
    logger.info("Shutting down.")

app = FastAPI(
    title="Knight Insurance AI Underwriting",
    version="1.0.0",
    description="AI-powered commercial trucking underwriting platform with enterprise security.",
    lifespan=lifespan,
)

# ══════════════════════════════════════════════════════════════
# Middleware Stack (order matters — outermost runs first)
# ══════════════════════════════════════════════════════════════

# 1. GZip compression — compress responses > 500 bytes (~60% smaller payloads)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 2. CORS — hardened origins (not allow_origins=["*"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://54.221.226.243:3000",
        "http://54.221.226.243",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# 3. API key authentication (disabled by default, enable with REQUIRE_API_KEY=true)
app.add_middleware(ApiKeyMiddleware)

# 4. Request logging — logs method, path, status, duration, client IP
app.add_middleware(RequestLoggingMiddleware)

# 5. Rate limiting — 120 req/min general, 10 req/min for uploads
app.add_middleware(RateLimitMiddleware)

# 6. Request ID tracking — unique ID on every request
app.add_middleware(RequestIdMiddleware)

# 7. Security headers — OWASP recommended headers on every response
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/api/health")
async def health():
    return {"status": "healthy" if _loaded else "loading", "app": "Knight Insurance"}
