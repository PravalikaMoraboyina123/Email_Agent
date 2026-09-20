"""
Adaptive Learning Engine for InboxPilot AI.
Adjusts priority weights dynamically based on historical user interactions (Open vs Ignore behavior).
"""

from sqlalchemy.orm import Session
from models.domain import UserPreference, EmailRecord
from utils.logger import logger


class LearningService:
    """
    Self-learning engine updating priority modifiers based on user interaction feedback.
    """

    def record_user_interaction(self, db: Session, email_id: int, action: str) -> None:
        """
        Updates preference weights when user interacts with an email ('Opened', 'Applied', 'Ignored').
        """
        record = db.query(EmailRecord).filter(EmailRecord.id == email_id).first()
        if not record:
            return

        category = record.category
        sender_domain = self._extract_domain(record.sender)

        # Update category level preferences
        self._update_preference_weight(db, key_type="category", key_value=category, action=action)

        # Update sender domain level preferences if valid domain exists
        if sender_domain:
            self._update_preference_weight(db, key_type="sender", key_value=sender_domain, action=action)

        # Mark email record status
        record.opened_status = (action in ["Opened", "Applied", "Completed"])
        record.action_taken = action
        db.commit()
        logger.info(f"Learned from user interaction: Action '{action}' on email '{record.subject}' ({category}).")

    def adjust_priority_score(self, db: Session, category: str, sender: str, base_score: int) -> int:
        """
        Applies learned weight modifiers to base LLM priority score.
        """
        sender_domain = self._extract_domain(sender)
        total_modifier = 0.0

        # Category modifier
        cat_pref = db.query(UserPreference).filter(
            UserPreference.key_type == "category",
            UserPreference.key_value == category
        ).first()
        if cat_pref:
            total_modifier += cat_pref.priority_modifier

        # Sender modifier
        if sender_domain:
            sender_pref = db.query(UserPreference).filter(
                UserPreference.key_type == "sender",
                UserPreference.key_value == sender_domain
            ).first()
            if sender_pref:
                total_modifier += sender_pref.priority_modifier

        adjusted = max(0, min(100, int(base_score + total_modifier)))
        if total_modifier != 0:
            logger.info(f"Priority adjusted by dynamic weight ({total_modifier:+.1f}): Base {base_score} -> Adjusted {adjusted}")

        return adjusted

    def _update_preference_weight(self, db: Session, key_type: str, key_value: str, action: str) -> None:
        """
        Increases or decreases weight based on user open/ignore count.
        """
        pref = db.query(UserPreference).filter(
            UserPreference.key_type == key_type,
            UserPreference.key_value == key_value
        ).first()

        if not pref:
            pref = UserPreference(
                key_type=key_type,
                key_value=key_value,
                priority_modifier=0.0,
                open_count=0,
                ignore_count=0
            )
            db.add(pref)

        if action in ["Opened", "Applied", "Completed"]:
            pref.open_count += 1
            pref.priority_modifier = min(30.0, pref.priority_modifier + 4.0)  # Boost priority
        elif action in ["Ignored", "Dismissed"]:
            pref.ignore_count += 1
            pref.priority_modifier = max(-30.0, pref.priority_modifier - 4.0)  # Penalize priority

        db.commit()

    def _extract_domain(self, sender_string: str) -> str:
        """
        Extracts domain name from sender header (e.g., 'Microsoft Careers <recruiting@microsoft.com>' -> 'microsoft.com').
        """
        if "@" in sender_string:
            domain = sender_string.split("@")[-1].strip(">").strip().lower()
            return domain
        return sender_string.lower()


learning_service = LearningService()
