"""
Application Settings Management using Pydantic Settings
Provides environment variable parsing, validation, and type-safe defaults across InboxPilot AI.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base Directory of the Project
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Application Info
    PROJECT_NAME: str = "InboxPilot AI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Server Specs
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Database Settings
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/inboxpilot.db"

    # Ollama LLM Settings
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"

    # Gmail OAuth Credentials & Scope
    GMAIL_CREDENTIALS_FILE: str = str(BASE_DIR / "credentials.json")
    GMAIL_TOKEN_FILE: str = str(BASE_DIR / "token.json")
    GMAIL_SCOPES: List[str] = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.readonly"
    ]

    # Priority & Threshold Configuration
    HIGH_PRIORITY_THRESHOLD: int = 75
    IMMEDIATE_PRIORITY_THRESHOLD: int = 95
    IMPORTANT_PRIORITY_THRESHOLD: int = 80
    NIGHT_SUMMARY_THRESHOLD: int = 60
    OPPORTUNITY_SCORE_THRESHOLD: int = 80

    # User Info & Automation Schedule Settings
    USER_GMAIL_ADDRESS: str = "pravalikamoraboyina21@gmail.com"
    MORNING_ROUTINE_TIME: str = "06:00"
    EVENING_ROUTINE_TIME: str = "21:00"
    LIVE_SCAN_INTERVAL_MINUTES: int = 5
    EMAIL_CHECK_INTERVAL_SECONDS: int = 60

    # Voice / Speech Settings
    VOICE_ENABLED: bool = True
    VOICE_LANG: str = "en"
    VOICE_TLD: str = "com"

    # Mobile Integration Settings (Telegram & ntfy.sh)
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    TELEGRAM_ENABLED: bool = True
    NTFY_TOPIC: str = "inbox_alerts"
    NTFY_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instantiate singleton settings object
settings = Settings()
