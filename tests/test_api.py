"""
Integration API Tests for InboxPilot AI FastAPI Routers and Endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from database.session import init_db


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    init_db()


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "InboxPilot AI"
    assert data["status"] == "online"


def test_auth_status_endpoint():
    response = client.get("/auth/status")
    assert response.status_code == 200
    data = response.json()
    assert "authorized" in data


def test_dashboard_stats_endpoint():
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_emails_processed" in data
    assert "category_distribution" in data


def test_preferences_endpoint():
    response = client.get("/preferences/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_emails_endpoint():
    response = client.get("/emails/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_routine_logs_endpoint():
    response = client.get("/dashboard/logs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
