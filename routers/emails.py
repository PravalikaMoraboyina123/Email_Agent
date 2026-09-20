"""
Email Management & Interaction REST API Endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.session import get_db
from models.domain import EmailRecord
from models.schemas import EmailResponseSchema
from services.learning_service import learning_service
from services.gmail_service import gmail_service
from utils.logger import logger

router = APIRouter(prefix="/emails", tags=["Emails"])


@router.get("/", response_model=List[EmailResponseSchema])
def list_emails(
    category: Optional[str] = Query(None, description="Filter by category"),
    important_only: bool = Query(False, description="Filter only high-priority/important emails"),
    unopened_only: bool = Query(False, description="Filter only unopened emails"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """
    Lists processed email records with optional filtering.
    """
    query = db.query(EmailRecord)
    if category:
        query = query.filter(EmailRecord.category == category)
    if important_only:
        query = query.filter(EmailRecord.is_important == True)
    if unopened_only:
        query = query.filter(EmailRecord.opened_status == False)

    records = query.order_by(EmailRecord.created_at.desc()).limit(limit).all()
    return records


@router.get("/{email_id}", response_model=EmailResponseSchema)
def get_email_detail(email_id: int, db: Session = Depends(get_db)):
    """
    Fetches detailed analysis for a specific email ID.
    """
    record = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Email record not found")
    return record


@router.post("/{email_id}/interact")
def record_email_interaction(
    email_id: int,
    action: str = Query(..., description="Action taken: 'Opened', 'Applied', 'Completed', 'Ignored', 'Dismissed'"),
    db: Session = Depends(get_db)
):
    """
    Records user interaction (e.g. user opened or ignored email).
    Triggers adaptive learning to boost/penalize priority score for future emails.
    """
    record = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Email record not found")

    # Record feedback & retrain dynamic weights
    learning_service.record_user_interaction(db, email_id, action)

    # Optionally sync read state back to Gmail
    if action in ["Opened", "Applied", "Completed"]:
        try:
            gmail_service.mark_as_read(record.gmail_id)
        except Exception as e:
            logger.warning(f"Could not update read state in Gmail: {e}")

    return {
        "status": "success",
        "email_id": email_id,
        "action_recorded": action,
        "message": f"Recorded action '{action}'. Priority engine updated."
    }
