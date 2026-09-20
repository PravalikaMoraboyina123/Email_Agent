"""
Unit Tests for Health Endpoint, Decision Engine Thresholds, and Category Validation.
"""

import pytest
from fastapi.testclient import TestClient
from main import app
from config.settings import settings
from models.schemas import CategoryEnum
from database.session import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from memory.memory_manager import memory_manager
from models.domain import EmailRecord

client = TestClient(app)

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_health_endpoint_structure():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "gmail_connected" in data
    assert "user_email" in data
    assert data["user_email"] == settings.USER_GMAIL_ADDRESS
    assert "email_check_interval_seconds" in data
    assert data["email_check_interval_seconds"] == settings.EMAIL_CHECK_INTERVAL_SECONDS


def test_expanded_categories():
    assert CategoryEnum.IMPORTANT_PERSONAL_EMAIL.value == "Important Personal Email"
    assert CategoryEnum.NEWSLETTER.value == "Newsletter"
    assert CategoryEnum.PLACEMENT.value == "Placement"
    assert CategoryEnum.INTERNSHIP.value == "Internship"


def test_missed_important_emails_memory_query():
    db = TestingSessionLocal()
    rec1 = EmailRecord(
        gmail_id="msg_001",
        sender="hr@microsoft.com",
        subject="Placement Offer",
        category="Placement",
        summary="Final interview clearing",
        priority_score=96,
        is_important=True,
        opened_status=False
    )
    rec2 = EmailRecord(
        gmail_id="msg_002",
        sender="promo@deals.com",
        subject="Discount Code",
        category="Advertisement",
        summary="Sale offer",
        priority_score=20,
        is_important=False,
        opened_status=False
    )
    db.add_all([rec1, rec2])
    db.commit()

    missed = memory_manager.get_missed_important_emails(db)
    assert len(missed) == 1
    assert missed[0].gmail_id == "msg_001"

    stats = memory_manager.get_total_stats(db)
    assert stats["total_processed"] == 2
    assert stats["total_important"] == 1

    db.close()
