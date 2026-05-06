import hashlib
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.exceptions import VoiceGenerationError

# In-memory TTS cache for Phase 2.2.
# Phase 2.3: replace with DB-backed cache using a tts_cache table.
_tts_cache: dict[str, dict] = {}
AUDIO_DIR = Path(__file__).resolve().parents[2] / "static" / "audio"
DEFAULT_VOICE_SETTINGS = {
    "stability": 0.5,
    "similarity_boost": 0.75,
}


def _make_cache_key(
    question_text: str,
    voice_id: str,
    model_id: str | None = None,
    voice_settings: dict[str, Any] | None = None,
) -> str:
    """
    Cache key = sha256(question_text + voice_id).
    Matches cost-control.md Section 9.2 TTS caching strategy.
    """
    effective_model_id = model_id or settings.ELEVENLABS_MODEL_ID
    effective_voice_settings = voice_settings or DEFAULT_VOICE_SETTINGS
    voice_settings_blob = ",".join(
        f"{key}={effective_voice_settings[key]}" for key in sorted(effective_voice_settings)
    )
    raw = f"{question_text}:{voice_id}:{effective_model_id}:{voice_settings_blob}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _estimate_duration(text: str) -> float:
    """
    Estimate audio duration from word count.
    Formula: word_count / 2.5 (average speaking rate = 2.5 words/second).
    """
    word_count = len(text.split())
    return round(word_count / 2.5, 1)


def _audio_path(cache_key: str) -> Path:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    return AUDIO_DIR / f"{cache_key[:32]}.mp3"


def _audio_url(cache_key: str) -> str:
    base_url = settings.PUBLIC_BACKEND_URL.rstrip("/")
    return f"{base_url}/static/audio/{cache_key[:32]}.mp3"


class VoiceService:
    def __init__(self):
        self.voice_id = settings.ELEVENLABS_VOICE_ID

    async def generate_question_audio(
        self,
        question_text: str,
        voice_id: str | None = None,
    ) -> dict:
        """
        Main TTS entry point.
        Returns dict with audio_url, duration_seconds, cached.

        Cache check happens before any provider call.
        If USE_MOCK_TTS=true: return mock audio URL.
        If USE_MOCK_TTS=false: call real ElevenLabs API.
        """
        effective_voice_id = voice_id or self.voice_id
        cache_key = _make_cache_key(
            question_text,
            effective_voice_id,
            settings.ELEVENLABS_MODEL_ID,
            DEFAULT_VOICE_SETTINGS,
        )

        if settings.TTS_CACHE_ENABLED and cache_key in _tts_cache:
            cached = _tts_cache[cache_key]
            return {
                "audio_url": cached["audio_url"],
                "duration_seconds": cached["duration_seconds"],
                "cached": True,
                "enabled": True,
            }

        if settings.TTS_CACHE_ENABLED and not settings.USE_MOCK_TTS:
            file_path = _audio_path(cache_key)
            if file_path.exists():
                audio_url = _audio_url(cache_key)
                duration = _estimate_duration(question_text)
                _tts_cache[cache_key] = {
                    "audio_url": audio_url,
                    "duration_seconds": duration,
                }
                return {
                    "audio_url": audio_url,
                    "duration_seconds": duration,
                    "cached": True,
                    "enabled": True,
                }

        if settings.USE_MOCK_TTS:
            result = self._mock_generate(question_text, cache_key)
        else:
            result = await self._real_generate(
                question_text,
                effective_voice_id,
                DEFAULT_VOICE_SETTINGS,
                cache_key,
            )

        if settings.TTS_CACHE_ENABLED:
            _tts_cache[cache_key] = {
                "audio_url": result["audio_url"],
                "duration_seconds": result["duration_seconds"],
            }

        return result

    async def _real_generate(
        self,
        question_text: str,
        voice_id: str,
        voice_settings: dict[str, Any] | str | None = None,
        cache_key: str | None = None,
    ) -> dict:
        """
        Real ElevenLabs TTS generation.
        Only called when USE_MOCK_TTS=false and ELEVENLABS_API_KEY is set.

        TODO Phase 2.3:
        - Upload generated audio to Supabase Storage / S3
        - Return permanent public URL instead of temp URL
        - Store cache entry in DB tts_cache table for persistence across restarts
        """
        if isinstance(voice_settings, str) and cache_key is None:
            cache_key = voice_settings
            voice_settings = None

        if not settings.ELEVENLABS_API_KEY:
            raise VoiceGenerationError(
                "ELEVENLABS_API_KEY is required when USE_MOCK_TTS=false"
            )

        effective_voice_settings = voice_settings or DEFAULT_VOICE_SETTINGS
        effective_cache_key = cache_key or _make_cache_key(
            question_text,
            voice_id,
            settings.ELEVENLABS_MODEL_ID,
            effective_voice_settings,
        )

        try:
            import httpx

            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            headers = {
                "xi-api-key": settings.ELEVENLABS_API_KEY,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            }
            payload = {
                "text": question_text,
                "model_id": settings.ELEVENLABS_MODEL_ID,
                "voice_settings": effective_voice_settings,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code == 401:
                raise VoiceGenerationError("ElevenLabs authentication failed")
            if response.status_code != 200:
                raise VoiceGenerationError(
                    f"ElevenLabs returned {response.status_code}: {response.text[:200]}"
                )

            file_path = _audio_path(effective_cache_key)
            file_path.write_bytes(response.content)
            audio_url = _audio_url(effective_cache_key)
            duration = _estimate_duration(question_text)

            return {
                "audio_url": audio_url,
                "duration_seconds": duration,
                "cached": False,
                "enabled": True,
            }
        except VoiceGenerationError:
            raise
        except Exception as exc:
            raise VoiceGenerationError(f"ElevenLabs call failed: {exc}") from exc

    async def rewrite_for_voice(self, question_text: str) -> str:
        """
        TODO: Call llm_service with build_voice_rewrite_prompt(question_text).
        Make question sound natural when spoken aloud.
        """
        if settings.USE_MOCK_AI:
            return question_text
        raise NotImplementedError("Real implementation not built yet")

    def _mock_generate(self, question_text: str, cache_key: str) -> dict:
        """
        Mock TTS - no external call.
        Returns a deterministic mock URL based on cache key.
        Duration estimated from word count.
        """
        short_key = cache_key[:8]
        mock_url = f"https://mock-tts.interviewos.dev/audio/{short_key}.mp3"
        duration = _estimate_duration(question_text)

        return {
            "audio_url": mock_url,
            "duration_seconds": duration,
            "cached": False,
            "enabled": True,
        }

    def _mock_audio_url(self, question_text: str) -> str:
        """Legacy method - kept for test_services.py compatibility."""
        cache_key = _make_cache_key(question_text, self.voice_id)
        return f"https://mock-tts.interviewos.dev/audio/{cache_key[:8]}.mp3"
