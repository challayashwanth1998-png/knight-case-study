"""
Knight Insurance — Minimal FastAPI server.
All heavy imports deferred to first request to work under memory pressure.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

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
    lifespan=lifespan,
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
async def health():
    return {"status": "healthy" if _loaded else "loading", "app": "Knight Insurance"}
