import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_evaluate_answer_mock_success():
    """POST /api/interview/evaluate returns correct shape with mock data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/evaluate",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "question_id": "00000000-0000-0000-0000-000000000002",
                "answer_id": "00000000-0000-0000-0000-000000000003",
                "generate_follow_up": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    result = data["data"]

    assert "score_id" in result
    assert "scores" in result
    assert "feedback" in result
    assert "follow_up" in result
    assert "latency" in result

    scores = result["scores"]
    required_score_fields = [
        "technical_correctness", "clarity", "depth", "confidence",
        "relevance", "structure", "communication", "conciseness",
        "example_quality", "overall"
    ]
    for field in required_score_fields:
        assert field in scores, f"Missing score field: {field}"
        if scores[field] is not None and field != "overall":
            assert 0 <= scores[field] <= 10, f"{field} out of range"

    feedback = result["feedback"]
    assert "summary" in feedback
    assert "strengths" in feedback
    assert "improvements" in feedback
    assert "ideal_answer_points" in feedback
    assert "missed_points" in feedback
    assert "suggested_better_answer" in feedback
    assert isinstance(feedback["strengths"], list)
    assert isinstance(feedback["improvements"], list)

    assert "recommended" in result["follow_up"]
    assert "reason" in result["follow_up"]

    assert "evaluation_ms" in result["latency"]
    assert result["latency"]["evaluation_ms"] >= 0


@pytest.mark.asyncio
async def test_evaluate_answer_invalid_uuid():
    """POST /api/interview/evaluate with invalid UUIDs returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/evaluate",
            json={
                "session_id": "not-a-uuid",
                "question_id": "also-not-a-uuid",
                "answer_id": "still-not-a-uuid",
                "generate_follow_up": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_evaluate_answer_missing_required_fields():
    """POST /api/interview/evaluate without required fields returns 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/evaluate",
            json={"generate_follow_up": True},
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_evaluate_answer_overall_score_is_float():
    """overall score in response is a float between 0 and 10."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/evaluate",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "question_id": "00000000-0000-0000-0000-000000000002",
                "answer_id": "00000000-0000-0000-0000-000000000003",
                "generate_follow_up": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 200
    overall = response.json()["data"]["scores"]["overall"]
    assert isinstance(overall, (int, float))
    assert 0 <= overall <= 10


@pytest.mark.asyncio
async def test_question_generation_real_mode_without_gemini_key_returns_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
        session_id = start_response.json()["data"]["session_id"]
        response = await client.post(
            "/api/interview/question",
            json={
                "session_id": session_id,
                "mode": "first",
                "include_voice": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "LLM_FAILED"
    assert (
        payload["error"]["message"]
        == "GEMINI_API_KEY is required when USE_MOCK_LLM=false and LLM_PROVIDER=gemini"
    )


@pytest.mark.asyncio
async def test_question_generation_sanitizes_fenced_json_question_text(monkeypatch):
    from app.routes import interview as interview_route

    monkeypatch.setattr(settings, "USE_MOCK_LLM", False)

    async def fake_generate_question(**kwargs):
        return {
            "question_text": """```json
{
  "question_text": "How would you design a resilient job queue for background tasks?",
  "question_type": "system_design",
  "difficulty": "hard",
  "expected_focus_areas": ["queues", "retries", "dead letters"],
  "time_limit_seconds": 75
}
```""",
            "question_type": "technical",
            "difficulty": "medium",
            "expected_focus_areas": [],
            "time_limit_seconds": 60,
        }

    monkeypatch.setattr(interview_route.llm_service, "generate_question", fake_generate_question)
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        start_response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
        session_id = start_response.json()["data"]["session_id"]
        response = await client.post(
            "/api/interview/question",
            json={
                "session_id": session_id,
                "mode": "first",
                "include_voice": False,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 200
    question = response.json()["data"]["question"]
    assert question["question_text"] == "How would you design a resilient job queue for background tasks?"
    assert question["type"] == "system_design"
    assert question["difficulty"] == "hard"
    assert question["expected_focus_areas"] == ["queues", "retries", "dead letters"]
    assert question["time_limit_seconds"] == settings.FREE_MAX_AUDIO_SECONDS


@pytest.mark.asyncio
async def test_evaluate_answer_real_mode_without_gemini_key_returns_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/evaluate",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "question_id": "00000000-0000-0000-0000-000000000002",
                "answer_id": "00000000-0000-0000-0000-000000000003",
                "generate_follow_up": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )

    assert response.status_code == 500
    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "LLM_FAILED"
    assert (
        payload["error"]["message"]
        == "GEMINI_API_KEY is required when USE_MOCK_LLM=false and LLM_PROVIDER=gemini"
    )
