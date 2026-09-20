"""
SQLAlchemy Engine and Session Factory setup for SQLite database.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from config.settings import settings
from utils.logger import logger

# Create SQLite Engine
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy ORM models."""
    pass


def get_db() -> Generator:
    """
    FastAPI Dependency to acquire DB session per request lifecycle.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize SQLite database tables if they do not exist.
    """
    try:
        logger.info("Initializing database schemas...")
        import models.domain  # Ensure models are registered
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas created successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise e
