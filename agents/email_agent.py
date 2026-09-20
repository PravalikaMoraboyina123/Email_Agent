"""
InboxPilot AI Agent - Core Orchestrator
Coordinates Gmail ingestion, local Ollama LLM intelligence, SQLite memory persistence, 
voice notifications, adaptive learning, and routine briefings.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from database.session import SessionLocal
from services.gmail_service import gmail_service
from services.llm_service import llm_service
from services.voice_service import voice_service
from services.learning_service import learning_service
from services.telegram_service import telegram_service
from services.push_service import push_service
from memory.memory_manager import memory_manager
from config.settings import settings
from utils.logger import logger


from datetime import datetime, timezone

class InboxPilotAgent:
    """
    Autonomous Personal AI Email Agent.
    """

    def __init__(self):
        self.last_scan_time: Optional[datetime] = None

    def process_new_emails(self) -> Dict[str, Any]:
        """
        Scans Gmail for unread emails, analyzes them with Ollama, stores memory,
        and triggers voice notifications based on decision engine thresholds.
        """
        logger.info("--- Starting Gmail Scanning Routine ---")
        self.last_scan_time = datetime.now(timezone.utc)
        db: Session = SessionLocal()
        processed_count = 0
        important_count = 0

        try:
            raw_emails = gmail_service.fetch_unread_emails(max_results=15)
            logger.info(f"Retrieved {len(raw_emails)} unread messages from Gmail.")

            for email in raw_emails:
                gmail_id = email["gmail_id"]

                # 1. Deduplication Memory Check
                if memory_manager.is_email_processed(db, gmail_id):
                    logger.debug(f"Email {gmail_id} already processed. Skipping.")
                    continue

                # 2. Ollama LLM Analysis
                logger.info(f"Analyzing Email [{gmail_id}] From: '{email['sender']}' | Subject: '{email['subject']}'")
                analysis = llm_service.analyze_email(
                    sender=email["sender"],
                    subject=email["subject"],
                    body=email["body"],
                    received_at=email["received_at"]
                )

                # 3. Dynamic Priority Adjustment via Learning Service
                analysis.priority_score = learning_service.adjust_priority_score(
                    db=db,
                    category=analysis.category.value,
                    sender=email["sender"],
                    base_score=analysis.priority_score
                )

                # 4. Multi-Tier Decision Engine Threshold Evaluation
                is_immediate = (
                    analysis.priority_score >= settings.IMMEDIATE_PRIORITY_THRESHOLD or
                    (analysis.opportunity_score >= settings.OPPORTUNITY_SCORE_THRESHOLD and 
                     analysis.category.value in ["Placement", "Internship", "Job Opportunity", "Interview"])
                ) and analysis.category.value != "Advertisement"

                if analysis.priority_score >= settings.IMPORTANT_PRIORITY_THRESHOLD or is_immediate:
                    analysis.is_important = True

                # 5. Immediate Spoken Notification for Urgent Items
                voice_sent = False
                if is_immediate:
                    spoken_alert = self._build_live_speech_alert(email, analysis)
                    voice_service.speak(spoken_alert, priority=True)

                    # Dispatch mobile voice & push notification
                    telegram_service.send_email_alert({
                        "category": analysis.category.value,
                        "sender": email["sender"],
                        "subject": email["subject"],
                        "summary": analysis.summary,
                        "priority_score": analysis.priority_score,
                        "opportunity_score": analysis.opportunity_score,
                        "recommended_action": analysis.recommended_action
                    })
                    push_service.send_push_notification(
                        title=f"🚨 {analysis.category.value}: {email['subject']}",
                        message=f"{analysis.summary}\nAction: {analysis.recommended_action}"
                    )

                    voice_sent = True
                    important_count += 1

                # 6. Persist to Memory Database
                memory_manager.save_email_record(
                    db=db,
                    gmail_id=gmail_id,
                    thread_id=email.get("thread_id"),
                    sender=email["sender"],
                    subject=email["subject"],
                    snippet=email["snippet"],
                    received_at=email.get("received_at"),
                    analysis=analysis,
                    voice_sent=voice_sent
                )

                processed_count += 1

            logger.info(f"--- Completed Email Scanning: Processed {processed_count} new emails ({important_count} urgent spoken alerts) ---")
            return {
                "status": "success",
                "processed_count": processed_count,
                "important_count": important_count
            }

        except Exception as e:
            logger.error(f"Error executing email processing pipeline: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            db.close()

    def run_morning_routine(self) -> Dict[str, Any]:
        """
        Morning 6:00 AM Routine: Connects to Gmail, processes unread emails,
        compiles morning briefing for unread important items, and speaks summary aloud.
        """
        logger.info("================ Running Morning Routine (6:00 AM) ================")
        # 1. First process any incoming emails
        self.process_new_emails()

        db: Session = SessionLocal()
        try:
            # 2. Fetch all unopened important emails
            unread_important = memory_manager.get_unread_important_emails(db, limit=10)

            emails_data = [
                {
                    "subject": record.subject,
                    "sender": record.sender,
                    "category": record.category,
                    "summary": record.summary,
                    "deadline": record.deadline,
                    "recommended_action": record.recommended_action
                }
                for record in unread_important
            ]

            # 3. Generate audio briefing text via Ollama
            briefing_text = llm_service.generate_morning_briefing_script(emails_data)

            # 4. Speak Morning Briefing & Send Mobile Voice Audio
            voice_service.speak(briefing_text, priority=True)
            telegram_service.send_voice_message(briefing_text, caption="🌅 Morning Email Briefing")
            push_service.send_push_notification("🌅 Morning Briefing", briefing_text)

            # 5. Audit Log
            memory_manager.log_routine_execution(
                db=db,
                routine_type="Morning Briefing",
                count=len(unread_important),
                speech=briefing_text,
                spoken=True
            )

            logger.info("================ Morning Routine Completed ================")
            return {
                "briefing_text": briefing_text,
                "important_emails_count": len(unread_important)
            }

        finally:
            db.close()

    def run_evening_routine(self) -> Dict[str, Any]:
        """
        Evening 9:00 PM Routine: Generates today's email summary, identifies uncompleted
        important tasks/deadlines, and speaks night briefing.
        """
        logger.info("================ Running Evening Routine (9:00 PM) ================")
        self.process_new_emails()

        db: Session = SessionLocal()
        try:
            today_records = memory_manager.get_today_emails(db)
            unread_important = memory_manager.get_unread_important_emails(db)

            # Calculate category statistics
            daily_stats = {}
            for record in today_records:
                daily_stats[record.category] = daily_stats.get(record.category, 0) + 1

            unread_data = [
                {"subject": r.subject, "deadline": r.deadline or "Soon"}
                for r in unread_important
            ]

            briefing_text = llm_service.generate_evening_briefing_script(
                daily_stats=daily_stats,
                unread_important=unread_data
            )

            voice_service.speak(briefing_text, priority=True)

            memory_manager.log_routine_execution(
                db=db,
                routine_type="Evening Briefing",
                count=len(today_records),
                speech=briefing_text,
                spoken=True
            )

            logger.info("================ Evening Routine Completed ================")
            return {
                "briefing_text": briefing_text,
                "total_today": len(today_records),
                "unopened_important": len(unread_important)
            }

        finally:
            db.close()

    def _build_live_speech_alert(self, email: dict, analysis: Any) -> str:
        """
        Constructs a crisp, natural spoken notification string for immediate alerts.
        """
        category_name = analysis.category.value if hasattr(analysis.category, "value") else str(analysis.category)
        if category_name in ["Placement", "Internship", "Job Opportunity", "Interview"]:
            alert = f"New {category_name.lower()} opportunity detected from {email['sender'].split('<')[0]}. {analysis.summary} Recommended action: {analysis.recommended_action}."
        else:
            alert = f"Important {category_name.lower()} received regarding {email['subject']}. {analysis.summary}"

        return alert


agent = InboxPilotAgent()
