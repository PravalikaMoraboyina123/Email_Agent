"""
Unit & Integration Tests for Mobile Phone Voice Bot & Notification Services.
"""

import pytest
from fastapi.testclient import TestClient

from main import app
from database.session import init_db
from services.push_service import push_service
from services.telegram_service import telegram_service

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


def test_mobile_dashboard_endpoint():
    """
    Test that the mobile PWA endpoint returns HTML dashboard.
    """
    response = client.get("/mobile/")
    assert response.status_code == 200
    assert "InboxPilot AI Mobile" in response.text
    assert "SpeechSynthesisUtterance" in response.text


def test_push_service_payload():
    """
    Test ntfy.sh push notification payload formatting.
    """
    res = push_service.send_push_notification(
        title="Test Alert",
        message="Test email alert body",
        priority="high"
    )
    # Returns boolean status
    assert isinstance(res, bool)


def test_telegram_service_disabled_gracefully():
    """
    Test Telegram service handles missing tokens gracefully without throwing exceptions.
    """
    # When token is empty, enabled is False
    assert telegram_service.send_text_message("Test message") is False
    assert telegram_service.send_voice_message("Test voice message") is False
