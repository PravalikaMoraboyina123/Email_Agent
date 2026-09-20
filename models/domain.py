"""
SQLAlchemy Domain ORM Models for InboxPilot AI
Stores email analysis, memory logs, user preference feedback, and routine logs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime
from database.session import Base


def utc_now():
    return datetime.now(timezone.utc)


class EmailRecord(Base):
    """
    Stores processed email messages, AI classification, priority scores, and actions.
    """
    __tablename__ = "email_records"

    id = Column(Integer, primary_key=True, index=True)
    gmail_id = Column(String(128), unique=True, index=True, nullable=False)
    thread_id = Column(String(128), nullable=True)
    sender = Column(String(255), index=True, nullable=False)
    subject = Column(String(512), nullable=False)
    snippet = Column(Text, nullable=True)
    received_at = Column(DateTime, nullable=True)

    # Ollama AI Structure
    priority_score = Column(Integer, default=0, index=True)
    category = Column(String(64), index=True, nullable=False)
    summary = Column(Text, nullable=False)
    deadline = Column(String(128), nullable=True)
    action_required = Column(String(255), nullable=True)
    opportunity_score = Column(Integer, default=0, index=True)
    reason = Column(Text, nullable=True)
    estimated_time = Column(String(64), nullable=True)
    recommended_action = Column(Text, nullable=True)
    is_important = Column(Boolean, default=False)

    # Tracking & State Memory
    opened_status = Column(Boolean, default=False)
    action_taken = Column(String(64), default="Pending") # Pending, Opened, Applied, Dismissed
    voice_sent = Column(Boolean, default=False)
    notification_status = Column(String(64), default="Pending") # Pending, Spoken, Skipped

    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class UserPreference(Base):
    """
    Dynamic learning table for user preferences.
    Tracks positive vs negative interactions by category or sender to adjust priority dynamically.
    """
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    key_type = Column(String(32), index=True)  # 'category' or 'sender'
    key_value = Column(String(255), index=True, unique=True) # e.g., 'Placement' or 'microsoft.com'
    priority_modifier = Column(Float, default=0.0) # Weight modifier (-30.0 to +30.0)
    open_count = Column(Integer, default=0)
    ignore_count = Column(Integer, default=0)
    last_interaction = Column(DateTime, default=utc_now)


class RoutineLog(Base):
    """
    Audit log for Morning Routines, Evening Briefings, and Continuous Scans.
    """
    __tablename__ = "routine_logs"

    id = Column(Integer, primary_key=True, index=True)
    routine_type = Column(String(64), nullable=False)  # Morning Briefing, Evening Briefing, Live Scan
    emails_processed = Column(Integer, default=0)
    summary_briefing = Column(Text, nullable=True)
    spoken = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utc_now)
