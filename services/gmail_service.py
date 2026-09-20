"""
Gmail API Service with Google OAuth 2.0 Flow.
Handles continuous headless token refreshing, mail fetching, and email body decoding.
"""

import os
import base64
from pathlib import Path
from typing import List, Dict, Any, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build, Resource

from config.settings import settings
from utils.logger import logger


class GmailService:
    """
    Gmail API reader & state manager using official Google OAuth 2.0.
    """

    def __init__(self):
        self.credentials_file = settings.GMAIL_CREDENTIALS_FILE
        self.token_file = settings.GMAIL_TOKEN_FILE
        self.scopes = settings.GMAIL_SCOPES
        self._service: Optional[Resource] = None

    def get_credentials(self) -> Credentials:
        """
        Loads saved OAuth tokens or initiates OAuth authorization flow if missing/invalid.
        Saves tokens back to token.json for continuous background usage.
        """
        creds = None
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
            except Exception as e:
                logger.warning(f"Invalid or corrupted token file found: {e}")

        # If credentials don't exist or are invalid
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("OAuth access token expired. Refreshing token silently...")
                    creds.refresh(Request())
                    logger.info("OAuth token successfully refreshed.")
                except Exception as e:
                    logger.error(f"Failed to refresh OAuth token: {e}. Re-authorization required.")
                    creds = None

            if not creds:
                if not os.path.exists(self.credentials_file):
                    logger.error(f"Missing OAuth credentials file at '{self.credentials_file}'. Please place credentials.json from Google Cloud Console.")
                    raise FileNotFoundError(
                        f"Missing '{self.credentials_file}'. Download OAuth Desktop Credentials from Google Cloud Console."
                    )

                logger.info("Initiating local Google OAuth Desktop authorization flow...")
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_file, self.scopes)
                creds = flow.run_local_server(port=0)
                logger.info("OAuth Authorization successful!")

            # Save refreshed credentials to disk
            with open(self.token_file, "w") as token:
                token.write(creds.to_json())
                logger.info(f"Saved updated OAuth token to {self.token_file}")

        return creds

    def check_connection(self) -> Dict[str, Any]:
        """
        Checks Gmail API connectivity and OAuth authorization status.
        """
        try:
            if not os.path.exists(self.credentials_file):
                return {"connected": False, "reason": "Missing credentials.json"}
            if not os.path.exists(self.token_file):
                return {"connected": False, "reason": "Missing token.json"}
            creds = self.get_credentials()
            if creds and creds.valid:
                return {"connected": True, "reason": "OAuth token authorized"}
            return {"connected": False, "reason": "OAuth token invalid"}
        except Exception as e:
            return {"connected": False, "reason": str(e)}

    def get_service(self) -> Resource:
        """
        Returns authenticated Gmail API service resource instance.
        """
        if not self._service:
            creds = self.get_credentials()
            self._service = build("gmail", "v1", credentials=creds)
        return self._service

    def fetch_unread_emails(self, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Fetches unread emails from user's Gmail inbox.
        """
        service = self.get_service()
        try:
            results = service.users().messages().list(
                userId="me",
                q="is:unread",
                maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            logger.info(f"Fetched {len(messages)} unread messages from Gmail.")

            detailed_messages = []
            for msg in messages:
                full_msg = self.get_email_details(msg["id"])
                if full_msg:
                    detailed_messages.append(full_msg)

            return detailed_messages

        except Exception as e:
            logger.error(f"Failed to fetch unread emails from Gmail API: {e}")
            return []

    def get_email_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches full payload metadata and decodes email body for a given message ID.
        """
        service = self.get_service()
        try:
            msg = service.users().messages().get(
                userId="me",
                id=message_id,
                format="full"
            ).execute()

            payload = msg.get("payload", {})
            headers = payload.get("headers", [])

            subject = "No Subject"
            sender = "Unknown Sender"
            date_str = ""
            received_dt = None

            for header in headers:
                name = header.get("name", "").lower()
                if name == "subject":
                    subject = header.get("value", "")
                elif name == "from":
                    sender = header.get("value", "")
                elif name == "date":
                    date_str = header.get("value", "")
                    try:
                        from email.utils import parsedate_to_datetime
                        received_dt = parsedate_to_datetime(date_str)
                    except Exception:
                        from datetime import datetime, timezone
                        received_dt = datetime.now(timezone.utc)

            body = self._extract_body(payload)
            snippet = msg.get("snippet", "")

            return {
                "gmail_id": msg.get("id"),
                "thread_id": msg.get("threadId"),
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "body": body if body else snippet,
                "received_at": received_dt or date_str
            }

        except Exception as e:
            logger.error(f"Error fetching message ID {message_id}: {e}")
            return None

    def mark_as_read(self, message_id: str) -> bool:
        """
        Removes the 'UNREAD' label from specified email message in Gmail.
        """
        service = self.get_service()
        try:
            service.users().messages().modify(
                userId="me",
                id=message_id,
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logger.info(f"Marked email {message_id} as READ in Gmail.")
            return True
        except Exception as e:
            logger.error(f"Failed to mark email {message_id} as read: {e}")
            return False

    def _extract_body(self, payload: dict) -> str:
        """
        Recursively parses MIME payload parts to extract plain text email content.
        """
        body = ""
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType")
                body_data = part.get("body", {}).get("data")
                if mime_type == "text/plain" and body_data:
                    body += base64.urlsafe_b64decode(body_data.encode("ASCII")).decode("utf-8", errors="ignore")
                elif "parts" in part:
                    body += self._extract_body(part)
        else:
            body_data = payload.get("body", {}).get("data")
            if body_data:
                body = base64.urlsafe_b64decode(body_data.encode("ASCII")).decode("utf-8", errors="ignore")

        return body.strip()


# Singleton instance
gmail_service = GmailService()
