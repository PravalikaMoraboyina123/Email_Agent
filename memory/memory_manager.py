"""
Memory Manager for Email History Deduplication & State Context.
Prevents processing identical emails twice and maintains audit history in SQLite.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.domain import EmailRecord, RoutineLog
from models.schemas import EmailAnalysisSchema
from utils.logger import logger


class MemoryManager:
    """
    State and memory manager backing InboxPilot AI actions.
    """

    def is_email_processed(self, db: Session, gmail_id: str) -> bool:
        """
        Checks if an email with given Gmail ID has already been ingested into SQLite.
        """
        exists = db.query(EmailRecord).filter(EmailRecord.gmail_id == gmail_id).first() is not None
        return exists

    def save_email_record(
        self,
        db: Session,
        gmail_id: str,
        thread_id: Optional[str],
        sender: str,
        subject: str,
        snippet: str,
        received_at,
        analysis: EmailAnalysisSchema,
        voice_sent: bool = False
    ) -> EmailRecord:
        """
        Persists email record and AI analysis results to SQLite database.
        """
        record = EmailRecord(
            gmail_id=gmail_id,
            thread_id=thread_id,
            sender=sender,
            subject=subject,
            snippet=snippet,
            received_at=received_at,
            priority_score=analysis.priority_score,
            category=analysis.category.value,
            summary=analysis.summary,
            deadline=analysis.deadline,
            action_required=analysis.action_required,
            opportunity_score=analysis.opportunity_score,
            reason=analysis.reason,
            estimated_time=analysis.estimated_time,
            recommended_action=analysis.recommended_action,
            is_important=analysis.is_important,
            opened_status=False,
            action_taken="Pending",
            voice_sent=voice_sent,
            notification_status="Spoken" if voice_sent else "Pending"
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        logger.info(f"Persisted email record (ID: {record.id}, Gmail ID: {gmail_id}, Category: {record.category}) to memory.")
        return record

    def get_unread_important_emails(self, db: Session, limit: int = 10) -> List[EmailRecord]:
        """
        Fetches unopened important emails for morning briefings.
        """
        return db.query(EmailRecord).filter(
            EmailRecord.is_important == True,
            EmailRecord.opened_status == False
        ).order_by(EmailRecord.priority_score.desc()).limit(limit).all()

    def get_missed_important_emails(self, db: Session) -> List[EmailRecord]:
        """
        Fetches unopened important emails that were processed and remain unread/unacted.
        """
        return db.query(EmailRecord).filter(
            EmailRecord.is_important == True,
            EmailRecord.opened_status == False
        ).order_by(EmailRecord.priority_score.desc()).all()

    def get_total_stats(self, db: Session) -> dict:
        """
        Returns total processed emails and total important emails count.
        """
        total = db.query(EmailRecord).count()
        important = db.query(EmailRecord).filter(EmailRecord.is_important == True).count()
        return {"total_processed": total, "total_important": important}

    def get_today_emails(self, db: Session) -> List[EmailRecord]:
        """
        Fetches emails processed since the start of the current local day.
        """
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day)
        return db.query(EmailRecord).filter(
            EmailRecord.created_at >= start_of_day
        ).order_by(EmailRecord.created_at.desc()).all()

    def get_recent_emails(self, db: Session, hours: int = 24) -> List[EmailRecord]:
        """
        Fetches emails processed during the requested recent time window.
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        return db.query(EmailRecord).filter(
            EmailRecord.created_at >= cutoff
        ).order_by(EmailRecord.created_at.desc()).all()

    def log_routine_execution(self, db: Session, routine_type: str, count: int, speech: str, spoken: bool = True) -> RoutineLog:
        """
        Records routine execution log in database.
        """
        log = RoutineLog(
            routine_type=routine_type,
            emails_processed=count,
            summary_briefing=speech,
            spoken=spoken
        )
        db.add(log)
        db.commit()
        return log


memory_manager = MemoryManager()
