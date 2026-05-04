import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/interviewos",
)
os.environ["DEBUG"] = "False"
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-secret")
os.environ.setdefault("SUPABASE_URL", "https://test-project.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("DEV_AUTH_BYPASS", "true")
os.environ.setdefault("USE_MOCK_LLM", "true")
os.environ.setdefault("USE_MOCK_STT", "true")
os.environ.setdefault("USE_MOCK_TTS", "true")

from app.db.base import Base
from app.db.database import get_async_session
from app.main import app


@pytest.fixture(autouse=False)
def dev_auth_bypass():
    with patch("app.core.config.settings.DEV_AUTH_BYPASS", True):
        with patch("app.core.config.settings.DEBUG", True):
            yield


@pytest.fixture
def mock_llm():
    with patch("app.core.config.settings.USE_MOCK_LLM", True):
        yield


@pytest.fixture
def mock_stt():
    with patch("app.core.config.settings.USE_MOCK_STT", True):
        yield


@pytest.fixture
def mock_tts():
    with patch("app.core.config.settings.USE_MOCK_TTS", True):
        yield


@pytest.fixture
def all_mocked(dev_auth_bypass, mock_llm, mock_stt, mock_tts):
    yield


@pytest_asyncio.fixture(autouse=True)
async def override_async_session_dependency():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = MetaData()

    for table in Base.metadata.sorted_tables:
        cloned_table = table.to_metadata(metadata)
        for column in cloned_table.columns:
            if column.server_default is not None and "gen_random_uuid()" in str(column.server_default.arg):
                column.server_default = None

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_async_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_async_session] = _override_get_async_session

    try:
        yield
    finally:
        app.dependency_overrides.pop(get_async_session, None)
        await engine.dispose()
