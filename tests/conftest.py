import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

_TEST_RUNTIME_DIR = Path(__file__).resolve().parent / ".runtime"
_TEST_RUNTIME_DIR.mkdir(exist_ok=True)
os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_RUNTIME_DIR / f'app-{os.getpid()}.db').as_posix()}"

from src.db import Base, SessionLocal, crud, engine  # noqa: E402
from src.db import models as db_models  # noqa: E402, F401
from src.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def test_database_schema() -> None:
    """Build the pre-pgvector application schema explicitly for API tests."""
    application_tables = [table for table in Base.metadata.sorted_tables if table.name != "document_chunks"]
    Base.metadata.create_all(bind=engine, tables=application_tables)
    original_s3_service = crud.s3_service
    crud.s3_service = SimpleNamespace(
        get_latest_version=lambda object_key: object_key,
        object_exists=lambda _object_key: False,
    )
    db = SessionLocal()
    try:
        crud.seed_onboarding_steps(db)
        crud.seed_default_users(db)
    finally:
        db.close()
    yield
    crud.s3_service = original_s3_service


@pytest_asyncio.fixture
async def client():
    """Async HTTP client for testing API endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_llm():
    """Mock LLM to avoid calling OpenAI during tests.

    Usage in test:
        def test_something(mock_llm):
            # LLM calls will return mock response instead of hitting OpenAI
            ...
    """
    mock = AsyncMock()
    mock.ainvoke.return_value = AsyncMock(content="Mocked LLM response")
    return mock
