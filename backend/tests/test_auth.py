import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import MetaData, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app.db.base import Base
from app.models.user import User


@pytest.mark.asyncio
async def test_health_works_without_auth():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_protected_route_without_token_returns_401(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", False)
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_protected_route_with_invalid_token_returns_401(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", False)
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_dev_bypass_allows_access(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/me",
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_free_tier_second_interview_blocked(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert r1.status_code == 200

        r2 = await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )
    assert r2.status_code == 429
    assert r2.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_deleted_account_can_recreate_same_identity(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "DEV_AUTH_BYPASS", True)
    monkeypatch.setattr(settings, "REQUIRE_AUTH", True)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.request(
            "DELETE",
            "/api/account",
            json={"confirmation": "DELETE_MY_ACCOUNT"},
            headers={"Authorization": "Bearer mock_token"},
        )
        assert response.status_code == 200

        me = await client.get(
            "/api/me",
            headers={"Authorization": "Bearer mock_token"},
        )

    assert me.status_code == 200
    assert me.json()["success"] is True


@pytest.mark.asyncio
async def test_deleted_email_can_recreate_but_preserves_free_limit(monkeypatch):
    from app.db.database import get_or_create_user

    original_user_id = "00000000-0000-0000-0000-000000000001"
    replacement_user_id = "00000000-0000-0000-0000-000000000099"
    email = "locked@example.com"

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

    async with session_factory() as db:
        await get_or_create_user(db, original_user_id, email)
        user = (
            await db.execute(select(User).where(User.id == uuid.UUID(original_user_id)))
        ).scalar_one()
        user.deleted_at = user.created_at
        user.free_interview_used = True
        await db.commit()

    async with session_factory() as db:
        recreated_user_id = await get_or_create_user(db, replacement_user_id, email)
        recreated_user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()

    assert recreated_user_id == replacement_user_id
    assert str(recreated_user.id) == replacement_user_id
    assert recreated_user.deleted_at is None
    assert recreated_user.free_interview_used is True
    await engine.dispose()
