import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_response_body_matches_exact_schema():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/health")

    assert response.json() == {
        "success": True,
        "data": {
            "status": "ok",
            "service": "interviewos-api",
            "version": "1.0.0",
        },
        "message": "Service is running",
    }


@pytest.mark.asyncio
async def test_health_returns_json_content_type():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/health")

    assert response.headers["content-type"] == "application/json"


@pytest.mark.asyncio
async def test_deep_health_returns_database_and_mock_mode_checks():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/health/deep")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    checks = payload["data"]["checks"]
    assert checks["database"] == "ok"
    assert "mock_mode" in checks
