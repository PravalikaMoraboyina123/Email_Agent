"""
User Preference & Dynamic Weight Learning REST API Router
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.session import get_db
from models.domain import UserPreference
from models.schemas import PreferenceSchema

router = APIRouter(prefix="/preferences", tags=["Preferences & Learning Engine"])


@router.get("/", response_model=List[PreferenceSchema])
def list_preferences(db: Session = Depends(get_db)):
    """
    Returns all learned priority modifiers by category and sender domain.
    """
    return db.query(UserPreference).order_by(UserPreference.priority_modifier.desc()).all()
