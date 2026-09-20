"""
User Preference & Dynamic Weight Learning REST API Router
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from models.domain import UserPreference
from models.schemas import PreferenceSchema, FocusModeRequest
from config.settings import settings

router = APIRouter(prefix="/preferences", tags=["Preferences & Learning Engine"])


@router.get("/", response_model=List[PreferenceSchema])
def list_preferences(db: Session = Depends(get_db)):
    """
    Returns all learned priority modifiers by category and sender domain.
    """
    return db.query(UserPreference).order_by(UserPreference.priority_modifier.desc()).all()


@router.get("/focus-mode")
def get_focus_mode():
    """Returns the current in-memory Focus Mode state."""
    return {"focus_mode_enabled": settings.FOCUS_MODE_ENABLED}


@router.post("/focus-mode")
def set_focus_mode(request: FocusModeRequest):
    """Turn Focus Mode on/off without restarting the agent."""
    settings.FOCUS_MODE_ENABLED = request.enabled
    return {
        "focus_mode_enabled": settings.FOCUS_MODE_ENABLED,
        "message": (
            "Focus Mode enabled: important emails will be saved silently."
            if request.enabled
            else "Focus Mode disabled: important emails will be spoken immediately."
        )
    }
