"""
Telegram Mobile Voice Bot & Remote Control Service for InboxPilot AI.
Sends text notifications and voice audio messages directly to the user's phone via Telegram.
"""

import os
import tempfile
import requests
from typing import Optional
from gtts import gTTS

from config.settings import settings
from utils.logger import logger


class TelegramService:
    """
    Service for pushing voice audio messages and text alerts to user's mobile Telegram app.
    """

    def __init__(self):
        self.token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.enabled = settings.TELEGRAM_ENABLED and bool(self.token) and bool(self.chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.token}"

    def send_text_message(self, message_text: str, parse_mode: str = "Markdown") -> bool:
        """
        Sends formatted text message to user's Telegram app on mobile.
        """
        if not self.enabled:
            logger.info("[TELEGRAM SKIPPED] Token or Chat ID not configured in .env.")
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message_text,
            "parse_mode": parse_mode
        }

        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                logger.info("[TELEGRAM PUSH SENT] Text message delivered to phone.")
                return True
            else:
                logger.warning(f"Telegram text message failed: HTTP {res.status_code} - {res.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending Telegram text message: {e}")
            return False

    def send_voice_message(self, text: str, caption: Optional[str] = None) -> bool:
        """
        Synthesizes text into a voice audio file and uploads it as a Telegram Voice Message to phone.
        """
        if not self.enabled:
            logger.info("[TELEGRAM VOICE SKIPPED] Token or Chat ID not configured.")
            return False

        temp_audio_path = None
        try:
            # 1. Synthesize audio file via gTTS
            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as fp:
                temp_audio_path = fp.name

            tts = gTTS(text=text, lang=settings.VOICE_LANG, tld=settings.VOICE_TLD, slow=False)
            tts.save(temp_audio_path)

            # 2. Upload voice message to Telegram via sendVoice API
            url = f"{self.base_url}/sendVoice"
            payload = {"chat_id": self.chat_id}
            if caption:
                payload["caption"] = caption[:1024]

            with open(temp_audio_path, "rb") as voice_file:
                files = {"voice": voice_file}
                res = requests.post(url, data=payload, files=files, timeout=30)

            if res.status_code == 200:
                logger.info("[TELEGRAM VOICE SENT] Voice audio message delivered to mobile phone!")
                return True
            else:
                logger.warning(f"Telegram voice upload failed: HTTP {res.status_code} - {res.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram voice message: {e}")
            return False
        finally:
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                except Exception:
                    pass

    def send_email_alert(self, email_data: dict) -> bool:
        """
        Sends structured mobile alert for urgent emails.
        """
        if not self.enabled:
            return False

        category = email_data.get("category", "General")
        subject = email_data.get("subject", "No Subject")
        sender = email_data.get("sender", "Unknown")
        summary = email_data.get("summary", "")
        priority = email_data.get("priority_score", 0)
        opportunity = email_data.get("opportunity_score", 0)

        msg = (
            f"🚨 *URGENT EMAIL ALERT*\n\n"
            f"📌 *Category*: `{category}`\n"
            f"👤 *From*: {sender}\n"
            f"✉️ *Subject*: {subject}\n\n"
            f"📝 *Summary*: {summary}\n\n"
            f"📊 *Priority Score*: `{priority}/100` | *Opportunity*: `{opportunity}/100`\n"
            f"💡 *Action*: {email_data.get('recommended_action', 'Review immediately')}"
        )

        # Send text alert
        self.send_text_message(msg)

        # Send voice audio message of the alert text
        voice_text = f"New {category} alert from {sender}. Subject: {subject}. Summary: {summary}"
        return self.send_voice_message(voice_text, caption=f"🔊 Voice Alert: {subject}")


# Singleton Telegram Service Instance
telegram_service = TelegramService()
