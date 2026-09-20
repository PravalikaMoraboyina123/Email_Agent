"""
Unit & Integration Tests for InboxPilot AI System Components.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.session import Base
from models.domain import EmailRecord, UserPreference
from models.schemas import EmailAnalysisSchema, CategoryEnum
from services.learning_service import LearningService
from services.llm_service import OllamaLLMService

# Setup in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_learning_service_weight_adjustment():
    db = TestingSessionLocal()
    learning = LearningService()

    base_score = 50
    category = "Placement"
    sender = "Careers Microsoft <recruiting@microsoft.com>"

    # 1. Base score initially unchanged
    adj1 = learning.adjust_priority_score(db, category, sender, base_score)
    assert adj1 == 50

    # 2. Add preference record to database
    pref = UserPreference(key_type="category", key_value="Placement", priority_modifier=15.0)
    db.add(pref)
    db.commit()

    # 3. Adjusted score should now incorporate modifier (+15)
    adj2 = learning.adjust_priority_score(db, category, sender, base_score)
    assert adj2 == 65
    db.close()


def test_ollama_fallback_rules():
    llm = OllamaLLMService()

    # Rule fallback test for placement email
    analysis = llm._fallback_rule_analysis(
        sender="hr@microsoft.com",
        subject="Microsoft Data Science Campus Recruitment Drive",
        body="Applications open for Data Science role. Apply before deadline."
    )

    assert analysis.category == CategoryEnum.PLACEMENT
    assert analysis.priority_score >= 80
    assert analysis.is_important is True


def test_ollama_json_cleaning():
    llm = OllamaLLMService()
    raw_markdown_json = """```json
    {
      "priority_score": 90,
      "category": "Placement",
      "summary": "Campus drive details.",
      "deadline": "Tomorrow",
      "action_required": "Apply now",
      "opportunity_score": 95,
      "reason": "Top tier opportunity",
      "estimated_time": "15 min",
      "recommended_action": "Apply today",
      "is_important": true
    }
    ```"""

    cleaned_dict = llm._clean_and_parse_json(raw_markdown_json)
    assert cleaned_dict["priority_score"] == 90
    assert cleaned_dict["category"] == "Placement"
