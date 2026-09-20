"""
Pydantic Schemas for Data Validation, API Serialization, and Ollama JSON Parsing.
"""

from enum import Enum
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CategoryEnum(str, Enum):
    PLACEMENT = "Placement"
    INTERNSHIP = "Internship"
    JOB_OPPORTUNITY = "Job Opportunity"
    INTERVIEW = "Interview"
    OFFER_LETTER = "Offer Letter"
    COLLEGE_NOTICE = "College Notice"
    EXAM = "Exam"
    ASSIGNMENT = "Assignment"
    SCHOLARSHIP = "Scholarship"
    WORKSHOP = "Workshop"
    CERTIFICATION = "Certification"
    IMPORTANT_PERSONAL_EMAIL = "Important Personal Email"
    NEWSLETTER = "Newsletter"
    BANK = "Bank"
    BILLS = "Bills"
    SPAM = "Spam"
    ADVERTISEMENT = "Advertisement"
    OTHERS = "Others"


class EmailAnalysisSchema(BaseModel):
    """
    Structured JSON format produced by Ollama LLM for incoming emails.
    """
    priority_score: int = Field(..., ge=0, le=100, description="Priority score from 0 to 100 based on urgency and relevance.")
    category: CategoryEnum = Field(..., description="Categorization of the email message.")
    summary: str = Field(..., description="Concise 1-2 sentence summary of the email content.")
    deadline: Optional[str] = Field(None, description="Extracted application or response deadline, or None if not mentioned.")
    action_required: Optional[str] = Field(None, description="Specific action required from user, or None if informational.")
    opportunity_score: int = Field(..., ge=0, le=100, description="Career / opportunity score (0-100) considering Data Science / career fit.")
    reason: str = Field(..., description="Justification for the priority and opportunity score assigned.")
    estimated_time: Optional[str] = Field(None, description="Estimated completion time, e.g. '15 minutes' or '1 hour'.")
    recommended_action: str = Field(..., description="Specific recommendation, e.g. 'Apply today' or 'Ignore advertisement'.")
    is_important: bool = Field(False, description="True if priority exceeds notification thresholds.")


class RawEmailInput(BaseModel):
    gmail_id: str
    thread_id: Optional[str] = None
    sender: str
    subject: str
    snippet: str
    body: str
    received_at: Optional[datetime] = None


class EmailResponseSchema(BaseModel):
    id: int
    gmail_id: str
    thread_id: Optional[str] = None
    sender: str
    subject: str
    snippet: Optional[str] = None
    received_at: Optional[datetime] = None

    priority_score: int
    category: str
    summary: str
    deadline: Optional[str] = None
    action_required: Optional[str] = None
    opportunity_score: int
    reason: Optional[str] = None
    estimated_time: Optional[str] = None
    recommended_action: str
    is_important: bool

    opened_status: bool
    action_taken: str
    voice_sent: bool
    notification_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FocusModeRequest(BaseModel):
    enabled: bool = Field(..., description="Enable or disable silent Focus Mode.")


class PreferenceSchema(BaseModel):
    key_type: str
    key_value: str
    priority_modifier: float
    open_count: int
    ignore_count: int

    model_config = ConfigDict(from_attributes=True)


class BriefingResponseSchema(BaseModel):
    routine_type: str
    processed_count: int
    speech_text: str
    important_emails: List[EmailResponseSchema]
