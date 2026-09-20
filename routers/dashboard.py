"""
Dashboard Control & Manual Routine Execution REST API Router
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from database.session import get_db
from models.domain import EmailRecord, RoutineLog, UserPreference
from agents.email_agent import agent

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Controls"])


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns summary statistics for dashboard displays.
    """
    total_emails = db.query(EmailRecord).count()
    important_emails = db.query(EmailRecord).filter(EmailRecord.is_important == True).count()
    unopened_important = db.query(EmailRecord).filter(EmailRecord.is_important == True, EmailRecord.opened_status == False).count()
    learned_preferences = db.query(UserPreference).count()

    categories_count = {}
    for record in db.query(EmailRecord).all():
        categories_count[record.category] = categories_count.get(record.category, 0) + 1

    return {
        "total_emails_processed": total_emails,
        "important_emails_count": important_emails,
        "unopened_important_count": unopened_important,
        "learned_preferences_count": learned_preferences,
        "category_distribution": categories_count
    }


@router.post("/trigger/scan")
def trigger_manual_scan(background_tasks: BackgroundTasks):
    """
    Triggers immediate email scan in background.
    """
    background_tasks.add_task(agent.process_new_emails)
    return {"status": "success", "message": "Triggered manual email scan in background."}


@router.post("/trigger/morning-routine")
def trigger_morning_routine(background_tasks: BackgroundTasks):
    """
    Triggers Morning 6:00 AM Routine manually.
    """
    background_tasks.add_task(agent.run_morning_routine)
    return {"status": "success", "message": "Triggered Morning Briefing Routine in background."}


@router.post("/trigger/evening-routine")
def trigger_evening_routine(background_tasks: BackgroundTasks):
    """
    Triggers Evening 9:00 PM Routine manually.
    """
    background_tasks.add_task(agent.run_evening_routine)
    return {"status": "success", "message": "Triggered Evening Briefing Routine in background."}


@router.get("/logs")
def get_routine_logs(db: Session = Depends(get_db)):
    """
    Lists audit logs for executed routines.
    """
    return db.query(RoutineLog).order_by(RoutineLog.created_at.desc()).limit(20).all()
