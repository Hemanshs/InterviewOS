import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


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
