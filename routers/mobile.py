"""
FastAPI Router for Mobile Web PWA & Phone Speech Integration.
Serves mobile dashboard for phones and handles speech payloads.
"""

from pathlib import Path
from fastapi import APIRouter, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from agents.email_agent import agent
from services.voice_service import voice_service
from services.telegram_service import telegram_service
from services.push_service import push_service

router = APIRouter(prefix="/mobile", tags=["Mobile Integration"])

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/", response_class=HTMLResponse)
def get_mobile_dashboard(request: Request):
    """
    Renders mobile-optimized PWA Web Dashboard for phone browsers.
    """
    return templates.TemplateResponse(request=request, name="mobile.html")


@router.post("/send-voice-to-phone")
def send_voice_to_phone(background_tasks: BackgroundTasks):
    """
    Triggers sending the spoken morning briefing voice message directly to user's phone via Telegram & ntfy.sh.
    """
    res = agent.run_morning_routine()
    briefing_text = res.get("briefing_text", "")

    if briefing_text:
        # Dispatch to Telegram voice uploader and ntfy.sh push notification in background
        background_tasks.add_task(telegram_service.send_voice_message, briefing_text, "🔊 Daily Email Briefing")
        background_tasks.add_task(push_service.send_push_notification, "InboxPilot AI Morning Briefing", briefing_text)

    return {
        "status": "success",
        "message": "Voice briefing dispatched to mobile phone!",
        "briefing_text": briefing_text
    }
