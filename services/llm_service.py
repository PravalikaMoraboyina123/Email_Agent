"""
Ollama Local LLM Service Wrapper
Communicates with local Ollama service for structured JSON extraction and briefing generation.
"""

import json
import re
import requests
from typing import Dict, Any, Optional
from config.settings import settings
from models.schemas import EmailAnalysisSchema, CategoryEnum
from prompts.email_prompts import (
    EMAIL_ANALYSIS_SYSTEM_PROMPT,
    EMAIL_ANALYSIS_USER_PROMPT,
    MORNING_BRIEFING_PROMPT,
    EVENING_BRIEFING_PROMPT
)
from utils.logger import logger


class OllamaLLMService:
    """
    Robust local LLM wrapper interfacing with Ollama endpoint (Free & Local).
    """

    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    def check_ollama_health(self) -> Dict[str, Any]:
        """
        Checks connectivity to local Ollama LLM endpoint.
        """
        try:
            res = requests.get(f"{self.base_url}/api/version", timeout=3)
            if res.status_code == 200:
                return {"available": True, "version": res.json().get("version", "unknown"), "model": self.model}
            return {"available": False, "reason": f"HTTP {res.status_code}", "model": self.model}
        except Exception as e:
            return {"available": False, "reason": str(e), "model": self.model}

    def _call_ollama(self, prompt: str, system_prompt: Optional[str] = None, json_mode: bool = True) -> str:
        """
        Executes HTTP call to local Ollama endpoint (tries /api/generate and /api/chat).
        """
        # 1. Try /api/generate endpoint
        generate_endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "top_p": 0.9
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
        if json_mode:
            payload["format"] = "json"

        try:
            response = requests.post(generate_endpoint, json=payload, timeout=45)
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "").strip()
        except Exception:
            pass

        # 2. Try /api/chat endpoint as fallback
        chat_endpoint = f"{self.base_url}/api/chat"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        chat_payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        if json_mode:
            chat_payload["format"] = "json"

        try:
            response = requests.post(chat_endpoint, json=chat_payload, timeout=45)
            response.raise_for_status()
            result = response.json()
            message = result.get("message", {})
            return message.get("content", "").strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with Ollama server at {self.base_url}: {e}")
            raise RuntimeError(f"Ollama connection error. Ensure Ollama is running (`ollama serve`): {e}")

    def analyze_email(self, sender: str, subject: str, body: str, received_at: str) -> EmailAnalysisSchema:
        """
        Parses an incoming raw email into structured Pydantic analysis.
        """
        user_prompt = EMAIL_ANALYSIS_USER_PROMPT.format(
            sender=sender,
            subject=subject,
            received_at=str(received_at),
            body=body[:2500]  # Truncate extremely long raw emails to fit context
        )

        try:
            raw_response = self._call_ollama(
                prompt=user_prompt,
                system_prompt=EMAIL_ANALYSIS_SYSTEM_PROMPT,
                json_mode=True
            )
            parsed_data = self._clean_and_parse_json(raw_response)

            # Validate against Pydantic schema
            analysis = EmailAnalysisSchema(**parsed_data)

            # Set importance threshold based on score or category
            if analysis.priority_score >= settings.HIGH_PRIORITY_THRESHOLD or analysis.category in [
                CategoryEnum.PLACEMENT, CategoryEnum.INTERNSHIP, CategoryEnum.JOB_OPPORTUNITY, CategoryEnum.INTERVIEW
            ]:
                analysis.is_important = True

            return analysis

        except Exception as e:
            logger.warning(f"Failed structured LLM analysis via Ollama ({e}). Triggering rule-based fallback...")
            return self._fallback_rule_analysis(sender, subject, body)

    def generate_morning_briefing_script(self, emails_summary_list: list) -> str:
        """
        Generates a concise spoken morning script for unread important emails.
        """
        if not emails_summary_list:
            return "Good morning. You have no urgent unread emails today. Have a productive day ahead!"

        # Create structured per-email summaries for spoken delivery
        detailed_parts = []
        for idx, e in enumerate(emails_summary_list, 1):
            sender_name = e.get('sender', '').split('<')[0].strip()
            item_str = f"Email {idx}: {e.get('category', 'Notice')} from {sender_name}. {e.get('summary', '')}"
            if e.get('deadline') and e.get('deadline') != 'Check email body':
                item_str += f" Deadline: {e['deadline']}."
            if e.get('recommended_action'):
                item_str += f" I recommend: {e['recommended_action']}."
            detailed_parts.append(item_str)

        detailed_text = " ".join(detailed_parts)

        formatted_emails = "\n".join([
            f"- Category: {e['category']} | Sender: {e['sender']} | Subject: {e['subject']} | Summary: {e['summary']} | Deadline: {e.get('deadline', 'None')} | Recommendation: {e.get('recommended_action', 'Review')}"
            for e in emails_summary_list
        ])
        prompt = MORNING_BRIEFING_PROMPT.format(emails_data=formatted_emails)

        try:
            res = self._call_ollama(prompt=prompt, json_mode=False)
            if res and len(res.strip()) > 10:
                return res
        except Exception as e:
            logger.warning(f"Using rich fallback morning briefing script generator: {e}")

        # High quality fallback script
        script = f"Good morning. You have {len(emails_summary_list)} important emails today. {detailed_text}"
        return script

    def generate_evening_briefing_script(self, daily_stats: dict, unread_important: list) -> str:
        """
        Generates a concise spoken evening review script for 9 PM routine.
        """
        stats_text = ", ".join([f"{count} {cat}" for cat, count in daily_stats.items()]) or "no emails"
        
        unopened_parts = []
        for idx, e in enumerate(unread_important, 1):
            item_str = f"Item {idx}: {e['subject']}."
            if e.get('deadline'):
                item_str += f" Deadline: {e['deadline']}."
            unopened_parts.append(item_str)

        unopened_details = " ".join(unopened_parts)
        data_str = f"Received Today: {stats_text}\nUnopened Important Emails:\n{unopened_details}"
        prompt = EVENING_BRIEFING_PROMPT.format(emails_data=data_str)

        try:
            res = self._call_ollama(prompt=prompt, json_mode=False)
            if res and len(res.strip()) > 10:
                return res
        except Exception as e:
            logger.warning(f"Using rich fallback evening briefing script generator: {e}")

        if unread_important:
            script = f"Good evening. Today you received {stats_text}. You have not opened: {unopened_details} I recommend reviewing these before sleeping."
        else:
            script = f"Good evening. Today you received {stats_text}. All important emails have been reviewed."
        return script

    def _clean_and_parse_json(self, raw_str: str) -> Dict[str, Any]:
        """
        Cleans markdown wrappers ```json ... ``` and extracts pure JSON dict.
        """
        cleaned = re.sub(r"^```json\s*", "", raw_str.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"^```\s*", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

        # Find first '{' and last '}'
        start_idx = cleaned.find('{')
        end_idx = cleaned.rfind('}')
        if start_idx != -1 and end_idx != -1:
            cleaned = cleaned[start_idx:end_idx + 1]

        return json.loads(cleaned)

    def _fallback_rule_analysis(self, sender: str, subject: str, body: str) -> EmailAnalysisSchema:
        """
        Rule-based heuristic fallback if local LLM is offline or output is malformed.
        """
        combined = f"{subject} {body}".lower()

        category = CategoryEnum.OTHERS
        priority = 30
        opportunity = 20
        is_important = False
        recommended = "Review email"

        if any(w in combined for w in ["placement", "campus recruitment", "hiring", "apply now"]):
            category = CategoryEnum.PLACEMENT
            priority = 90
            opportunity = 90
            is_important = True
            recommended = "Review placement details and submit application."
        elif any(w in combined for w in ["internship", "stipend", "intern"]):
            category = CategoryEnum.INTERNSHIP
            priority = 85
            opportunity = 85
            is_important = True
            recommended = "Apply for internship."
        elif any(w in combined for w in ["interview", "assessment", "test link", "coding challenge"]):
            category = CategoryEnum.INTERVIEW
            priority = 95
            opportunity = 95
            is_important = True
            recommended = "Prepare and complete assessment."
        elif any(w in combined for w in ["unsub", "discount", "sale", "newsletter", "promotions"]):
            category = CategoryEnum.ADVERTISEMENT
            priority = 5
            opportunity = 0
            is_important = False
            recommended = "Ignore advertisement."

        return EmailAnalysisSchema(
            priority_score=priority,
            category=category,
            summary=f"Notice regarding {subject[:50]}",
            deadline="Check email body",
            action_required="Action required based on message details.",
            opportunity_score=opportunity,
            reason="Rule-based heuristic estimation.",
            estimated_time="10 minutes",
            recommended_action=recommended,
            is_important=is_important
        )


# Singleton LLM Service instance
llm_service = OllamaLLMService()
