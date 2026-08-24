"""SQLAlchemy engine, session factory, and declarative Base."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.config import get_settings
from src.db.base import Base as Base


def _get_engine():
    settings = get_settings()
    url = settings.database_url
    if settings.app_env == "production" and url.startswith("sqlite"):
        raise RuntimeError("Production requires PostgreSQL; SQLite is not allowed")
    if url.startswith("sqlite"):
        return create_engine(url, connect_args={"check_same_thread": False}, echo=False)

    try:
        eng = create_engine(url, echo=False)
        with eng.connect() as _:
            pass
        return eng
    except Exception as e:
        raise RuntimeError(f"Database connection to {url} failed") from e


engine = _get_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_db_and_tables() -> None:
    """Seed application data after Alembic has established the schema."""
    from src.db.crud import seed_default_users, seed_onboarding_steps

    # Auto seed initial data
    db = SessionLocal()
    try:
        seed_onboarding_steps(db)
        if get_settings().app_env != "production":
            seed_default_users(db)
    finally:
        db.close()
