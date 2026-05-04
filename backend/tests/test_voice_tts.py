import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import get_current_user
from app.main import app
from app.services.voice_service import VoiceService, _tts_cache
from app.core.config import settings
from app.core.exceptions import VoiceGenerationError


@pytest.fixture(autouse=True)
def configure_voice_test_environment(monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", True)
    monkeypatch.setattr(settings, "TTS_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")
    _tts_cache.clear()
    stable_user_id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: stable_user_id
    yield
    _tts_cache.clear()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_mock_tts_returns_correct_shape():
    service = VoiceService()

    result = await service.generate_question_audio("Test question text")

    assert set(result.keys()) == {"audio_url", "duration_seconds", "cached", "enabled"}
    assert result["audio_url"].startswith("https://")
    assert result["enabled"] is True
    assert result["cached"] is False


@pytest.mark.asyncio
async def test_tts_cache_hit_on_second_call():
    service = VoiceService()

    first = await service.generate_question_audio("Tell me about your backend architecture.")
    second = await service.generate_question_audio("Tell me about your backend architecture.")

    assert first["cached"] is False
    assert second["cached"] is True
    assert first["audio_url"] == second["audio_url"]


@pytest.mark.asyncio
async def test_different_texts_produce_different_urls():
    service = VoiceService()

    first = await service.generate_question_audio("Explain API authentication.")
    second = await service.generate_question_audio("Explain database indexing.")

    assert first["audio_url"] != second["audio_url"]


@pytest.mark.asyncio
async def test_duration_estimate_is_reasonable():
    service = VoiceService()

    result = await service.generate_question_audio("one two three four five six seven eight nine ten")

    assert 2.0 <= result["duration_seconds"] <= 8.0


@pytest.mark.asyncio
async def test_post_question_with_include_voice_true():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        start_response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": True,
            },
        )
        session_id = start_response.json()["data"]["session_id"]
        response = await client.post(
            "/api/interview/question",
            json={
                "session_id": session_id,
                "mode": "first",
                "include_voice": True,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["question"]["audio"]["enabled"] is True
    assert payload["data"]["question"]["audio"]["audio_url"].startswith("https://")
    assert payload["data"]["question"]["audio"]["duration_seconds"] > 0
    assert payload["data"]["latency_state"]["current"] == "ready_for_answer"
    assert "voice_generated" in payload["data"]["latency_state"]["completed_steps"]


@pytest.mark.asyncio
async def test_post_question_with_include_voice_false():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        start_response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": False,
            },
        )
        session_id = start_response.json()["data"]["session_id"]
        response = await client.post(
            "/api/interview/question",
            json={
                "session_id": session_id,
                "mode": "first",
                "include_voice": False,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["question"]["audio"]["enabled"] is False
    assert payload["data"]["question"]["audio"]["audio_url"] is None
    assert "voice_generated" not in payload["data"]["latency_state"]["completed_steps"]


@pytest.mark.asyncio
async def test_question_response_has_correct_structure():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        start_response = await client.post(
            "/api/interview/start",
            json={
                "interview_type": "sde",
                "difficulty": "medium",
                "question_count": 5,
                "voice_enabled": True,
            },
        )
        session_id = start_response.json()["data"]["session_id"]
        response = await client.post(
            "/api/interview/question",
            json={
                "session_id": session_id,
                "mode": "first",
                "include_voice": True,
            },
        )

    assert response.status_code == 200
    data = response.json()["data"]
    question = data["question"]
    assert "session_id" in data
    assert "question_id" in question
    assert "sequence" in question
    assert "type" in question
    assert "difficulty" in question
    assert "question_text" in question
    assert "expected_focus_areas" in question
    assert "time_limit_seconds" in question
    assert "audio" in question
    assert "latency_state" in data


@pytest.mark.asyncio
async def test_missing_elevenlabs_api_key_raises_in_real_mode(monkeypatch):
    service = VoiceService()
    monkeypatch.setattr(settings, "USE_MOCK_TTS", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")

    with pytest.raises(VoiceGenerationError, match="ELEVENLABS_API_KEY"):
        await service._real_generate("test", "voice_id", "cache_key")
