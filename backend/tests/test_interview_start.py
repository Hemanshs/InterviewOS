import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_start_interview_with_resume_id(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", True)
    minimal_pdf = b"%PDF-1.4\n%%EOF"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        upload = await client.post(
            "/api/resume/upload",
            files={"file": ("resume.pdf", minimal_pdf, "application/pdf")},
            headers={"Authorization": "Bearer mock_token"},
        )
        resume_id = upload.json()["data"]["resume_id"]

        response = await client.post(
            "/api/interview/start",
            json={
                "resume_id": resume_id,
                "interview_type": "backend",
                "difficulty": "medium",
                "job_description": "Looking for a backend engineer with FastAPI and PostgreSQL experience.",
                "target_company": "Amazon",
                "target_role": "Backend Engineer",
                "question_count": 5,
                "voice_enabled": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert "session_id" in data
    assert data["resume_id"] == resume_id
    assert data["status"] == "in_progress"
    assert data["interview_type"] == "backend"
    assert data["difficulty"] == "medium"
    assert data["question_count"] == 5
    assert data["voice_enabled"] is True
    assert data["limits"]["max_questions"] == 5
    assert data["limits"]["max_answer_duration_seconds"] == 60
    assert data["next_action"]["type"] == "generate_question"
    assert data["next_action"]["endpoint"] == "/api/interview/question"


@pytest.mark.asyncio
async def test_start_interview_without_resume_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "easy",
                "target_role": "Software Engineer",
                "question_count": 3,
                "voice_enabled": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["resume_id"] is None
    assert data["interview_type"] == "sde"
    assert data["difficulty"] == "easy"
    assert data["question_count"] == 3
    assert data["voice_enabled"] is False
    assert data["status"] == "in_progress"


@pytest.mark.asyncio
async def test_start_interview_jd_based_requires_job_description():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "jd_based",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_start_interview_response_shape_matches_api_design():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "behavioral",
                "difficulty": "hard",
                "target_company": "Google",
                "question_count": 5,
                "voice_enabled": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    for field in [
        "session_id",
        "status",
        "interview_type",
        "difficulty",
        "question_count",
        "started_at",
        "limits",
        "next_action",
    ]:
        assert field in data, f"Missing field: {field}"
