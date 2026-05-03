import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_start_interview_creates_session():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "session_id" in data["data"]
    assert data["data"]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_question_creates_db_row():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )
        session_id = start.json()["data"]["session_id"]

        response = await client.post(
            "/api/interview/question",
            json={"session_id": session_id, "mode": "first", "include_voice": False},
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    assert response.json()["data"]["question"]["sequence"] == 1


@pytest.mark.asyncio
async def test_history_returns_in_progress():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )
        response = await client.get(
            "/api/interview/history?status=in_progress",
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["items"]) > 0
    assert data["data"]["items"][0]["status"] == "in_progress"


@pytest.mark.asyncio
async def test_completed_session_not_in_recovery():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start = await client.post(
            "/api/interview/start",
            json={"interview_type": "sde", "difficulty": "medium", "question_count": 5},
            headers={"Authorization": "Bearer mock_token"},
        )
        session_id = start.json()["data"]["session_id"]

        await client.post(
            f"/api/interview/{session_id}/complete",
            headers={"Authorization": "Bearer mock_token"},
        )

        response = await client.get(
            "/api/interview/history?status=in_progress",
            headers={"Authorization": "Bearer mock_token"},
        )

    items = response.json()["data"]["items"]
    session_ids = [item["session_id"] for item in items]
    assert session_id not in session_ids
