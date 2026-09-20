"""
Free Mobile Push Notification Service for InboxPilot AI using ntfy.sh
Sends instant pub/sub push notifications to Android / iOS devices.
"""

import requests
import base64
from config.settings import settings
from utils.logger import logger


class PushService:
    """
    Free Push Notification Service using ntfy.sh.
    """

    @property
    def topic(self) -> str:
        return (settings.NTFY_TOPIC or "inbox_alerts").lower()

    @property
    def enabled(self) -> bool:
        return settings.NTFY_ENABLED

    @property
    def base_url(self) -> str:
        return f"https://ntfy.sh/{self.topic}"

    def send_push_notification(
        self,
        title: str,
        message: str,
        priority: str = "high",
        tags: str = "briefcase,email"
    ) -> bool:
        """
        Sends an instant push notification to the user's mobile device.
        """
        if not self.enabled:
            return False

        # Encode title to RFC 2047 utf-8 base64 if it contains non-ASCII characters
        try:
            title.encode('ascii')
            safe_title = title
        except UnicodeEncodeError:
            encoded_title = base64.b64encode(title.encode('utf-8')).decode('ascii')
            safe_title = f"=?utf-8?B?{encoded_title}?="

        headers = {
            "Title": safe_title,
            "Priority": priority,  # max, high, default, low, min
            "Tags": tags,
            "Actions": "view, Listen Aloud on Phone, http://10.215.22.1:8000/mobile, clear=true"
        }

        try:
            response = requests.post(self.base_url, data=message.encode("utf-8"), headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"[MOBILE PUSH SENT] Title: '{title}' to ntfy.sh/{self.topic}")
                return True
            else:
                logger.warning(f"Failed to send mobile push notification: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Error sending mobile push notification via ntfy.sh: {e}")
            return False


# Singleton Push Service Instance
push_service = PushService()
