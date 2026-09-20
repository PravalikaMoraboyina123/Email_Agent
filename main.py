"""
InboxPilot AI - Main Application Entrypoint
Autonomous Personal AI Email Agent with FastAPI, SQLite, Gmail OAuth, Ollama, gTTS & APScheduler.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from database.session import init_db
from scheduler.cron_scheduler import start_scheduler, stop_scheduler
from routers import auth_router, emails_router, preferences_router, dashboard_router, mobile_router
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager: Handles startup & teardown hooks.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} background engine...")

    # 1. Initialize SQLite Database Schemas
    init_db()

    # 2. Start APScheduler 24/7 Background Daemon
    start_scheduler()

    logger.info(f"{settings.PROJECT_NAME} is live! Running at http://{settings.HOST}:{settings.PORT}")

    yield  # Server handles incoming requests

    # Teardown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")
    stop_scheduler()


# Create FastAPI Instance
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Autonomous Personal AI Email Agent powered by local Ollama LLMs, Gmail API, gTTS, and APScheduler.",
    version="1.0.0",
    lifespan=lifespan
)

# Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(preferences_router)
app.include_router(dashboard_router)
app.include_router(mobile_router)


@app.get("/")
def root():
    """
    Root Endpoint - System Health Status.
    """
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "environment": settings.ENVIRONMENT,
        "ollama_model": settings.OLLAMA_MODEL,
        "docs_url": f"http://{settings.HOST}:{settings.PORT}/docs"
    }


@app.get("/health")
def health_check():
    """
    Detailed Health Check Endpoint.
    Returns status of Gmail, Ollama, APScheduler, last scan time, and database metrics.
    """
    from services.gmail_service import gmail_service
    from services.llm_service import llm_service
    from scheduler.cron_scheduler import scheduler
    from agents.email_agent import agent
    from database.session import SessionLocal
    from memory.memory_manager import memory_manager

    gmail_status = gmail_service.check_connection()
    ollama_status = llm_service.check_ollama_health()
    scheduler_running = scheduler.running if scheduler else False

    db = SessionLocal()
    try:
        stats = memory_manager.get_total_stats(db)
    finally:
        db.close()

    is_healthy = gmail_status.get("connected", False) and scheduler_running

    return {
        "status": "healthy" if is_healthy else "degraded",
        "gmail_connected": gmail_status.get("connected", False),
        "gmail_details": gmail_status.get("reason"),
        "user_email": settings.USER_GMAIL_ADDRESS,
        "ollama_available": ollama_status.get("available", False),
        "ollama_details": ollama_status,
        "scheduler_running": scheduler_running,
        "email_check_interval_seconds": settings.EMAIL_CHECK_INTERVAL_SECONDS,
        "last_scan_time": agent.last_scan_time.isoformat() if agent.last_scan_time else None,
        "total_processed_emails": stats.get("total_processed", 0),
        "total_important_emails": stats.get("total_important", 0)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
