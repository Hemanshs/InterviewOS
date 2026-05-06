from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from app.core.config import settings
from app.core.exceptions import VoiceGenerationError
from app.services.voice_service import (
    DEFAULT_VOICE_SETTINGS,
    VoiceService,
    _audio_url,
    _make_cache_key,
    _tts_cache,
)


@pytest.fixture(autouse=True)
def clear_tts_cache():
    _tts_cache.clear()
    yield
    _tts_cache.clear()


@pytest.fixture
def voice_service():
    return VoiceService()


@pytest.mark.asyncio
async def test_mock_tts_returns_correct_shape(voice_service, monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", True)
    result = await voice_service.generate_question_audio("Test question text")
    assert result["enabled"] is True
    assert result["audio_url"].startswith("https://")
    assert isinstance(result["duration_seconds"], float)
    assert result["duration_seconds"] > 0
    assert result["cached"] is False


@pytest.mark.asyncio
async def test_mock_tts_cache_hit_on_second_call(voice_service, monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", True)
    monkeypatch.setattr(settings, "TTS_CACHE_ENABLED", True)
    r1 = await voice_service.generate_question_audio("Unique test question for cache")
    r2 = await voice_service.generate_question_audio("Unique test question for cache")
    assert r1["cached"] is False
    assert r2["cached"] is True
    assert r1["audio_url"] == r2["audio_url"]


@pytest.mark.asyncio
async def test_different_texts_produce_different_urls(voice_service, monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", True)
    r1 = await voice_service.generate_question_audio("Question A text here")
    r2 = await voice_service.generate_question_audio("Question B completely different")
    assert r1["audio_url"] != r2["audio_url"]


@pytest.mark.asyncio
async def test_real_tts_missing_api_key_raises_error(voice_service, monkeypatch):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "")
    with pytest.raises(VoiceGenerationError, match="ELEVENLABS_API_KEY"):
        await voice_service._real_generate("test", "voice_id", {}, "cache_key")


@pytest.mark.asyncio
async def test_real_tts_elevenlabs_call_success(voice_service, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "test_key_123")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", "test_voice_id")
    monkeypatch.setattr(settings, "PUBLIC_BACKEND_URL", "http://localhost:8000")
    monkeypatch.setattr("app.services.voice_service.AUDIO_DIR", tmp_path)

    fake_audio_bytes = b"ID3fake_mp3_audio_content_here"

    async def fake_post(self, url, headers=None, json=None):
        assert url == "https://api.elevenlabs.io/v1/text-to-speech/test_voice_id"
        return httpx.Response(200, content=fake_audio_bytes)

    with patch.object(httpx.AsyncClient, "post", fake_post):
        result = await voice_service._real_generate(
            question_text="Can you explain how you would design an API?",
            voice_id="test_voice_id",
            voice_settings={},
            cache_key="abc123def456789012345678901234567890",
        )

    assert result["enabled"] is True
    assert result["audio_url"].startswith("http://localhost:8000/static/audio/")
    assert result["audio_url"].endswith(".mp3")
    assert result["cached"] is False
    written_files = list(tmp_path.glob("*.mp3"))
    assert len(written_files) == 1


@pytest.mark.asyncio
async def test_real_tts_elevenlabs_401_raises_clear_error(voice_service, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", False)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "bad_key")
    monkeypatch.setattr(settings, "ELEVENLABS_VOICE_ID", "voice_id")
    monkeypatch.setattr("app.services.voice_service.AUDIO_DIR", tmp_path)

    async def fake_post(self, url, headers=None, json=None):
        return httpx.Response(401)

    with patch.object(httpx.AsyncClient, "post", fake_post):
        with pytest.raises(VoiceGenerationError, match="authentication failed"):
            await voice_service._real_generate(
                "test",
                "voice_id",
                {},
                "cache_key_32chars_minimum_here",
            )


@pytest.mark.asyncio
async def test_file_based_cache_hit(voice_service, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "USE_MOCK_TTS", False)
    monkeypatch.setattr(settings, "TTS_CACHE_ENABLED", True)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "test_key")
    monkeypatch.setattr(settings, "PUBLIC_BACKEND_URL", "http://localhost:8000")
    monkeypatch.setattr("app.services.voice_service.AUDIO_DIR", tmp_path)

    text = "File cache test question"
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    cache_key = _make_cache_key(
        text,
        voice_id,
        "eleven_multilingual_v2",
        DEFAULT_VOICE_SETTINGS,
    )

    audio_file = tmp_path / f"{cache_key[:32]}.mp3"
    audio_file.write_bytes(b"fake_mp3")

    result = await voice_service.generate_question_audio(text)
    assert result["cached"] is True
    assert result["enabled"] is True


def test_audio_url_is_absolute(monkeypatch):
    monkeypatch.setattr(settings, "PUBLIC_BACKEND_URL", "https://my-api.onrender.com")
    url = _audio_url("abc123def456789012345678901234567890")
    assert url.startswith("https://my-api.onrender.com/static/audio/")
    assert url.endswith(".mp3")
