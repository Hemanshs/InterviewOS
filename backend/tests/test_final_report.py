import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app


@pytest.mark.asyncio
async def test_final_report_mock_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "include_transcript": True,
                "include_recommendations": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    report = data["data"]

    for field in [
        "report_id",
        "session_id",
        "status",
        "overall_score",
        "score_breakdown",
        "summary",
        "strengths",
        "weaknesses",
        "recommended_topics",
        "question_reviews",
        "created_at",
    ]:
        assert field in report, f"Missing field: {field}"

    breakdown = report["score_breakdown"]
    for field in [
        "technical",
        "communication",
        "confidence",
        "problem_solving",
        "role_fit",
    ]:
        assert field in breakdown, f"Missing breakdown field: {field}"
        assert 0 <= breakdown[field] <= 10

    assert 0 <= report["overall_score"] <= 10

    assert isinstance(report["question_reviews"], list)
    if report["question_reviews"]:
        review = report["question_reviews"][0]
        for field in [
            "question_id",
            "sequence",
            "question_text",
            "answer_id",
            "overall_score",
            "feedback_summary",
        ]:
            assert field in review

    assert report["transcript"] is not None
    assert isinstance(report["transcript"], list)


@pytest.mark.asyncio
async def test_final_report_without_transcript():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "include_transcript": False,
                "include_recommendations": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 200
    report = response.json()["data"]
    assert report["transcript"] is None


@pytest.mark.asyncio
async def test_final_report_invalid_session_uuid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={
                "session_id": "not-a-uuid",
                "include_transcript": True,
                "include_recommendations": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_final_report_missing_session_id():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={"include_transcript": True},
            headers={"Authorization": "Bearer mock_token"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_final_report_overall_score_matches_breakdown():
    """overall_score should be close to the average of breakdown scores."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "include_transcript": True,
                "include_recommendations": True,
            },
            headers={"Authorization": "Bearer mock_token"},
        )
    report = response.json()["data"]
    breakdown = report["score_breakdown"]
    avg = sum(breakdown.values()) / len(breakdown)
    assert abs(report["overall_score"] - avg) < 1.0


@pytest.mark.asyncio
async def test_final_report_real_mode_without_gemini_key_returns_clear_error(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_LLM", False)
    monkeypatch.setattr(settings, "LLM_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/interview/final-report",
            json={
                "session_id": "00000000-0000-0000-0000-000000000001",
                "include_transcript": True,
                "include_recommendations": True,
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
