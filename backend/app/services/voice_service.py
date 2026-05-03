import hashlib

from app.core.config import settings
from app.core.exceptions import VoiceGenerationError

# In-memory TTS cache for Phase 2.2.
# Phase 2.3: replace with DB-backed cache using a tts_cache table.
_tts_cache: dict[str, dict] = {}


def _make_cache_key(question_text: str, voice_id: str) -> str:
    """
    Cache key = sha256(question_text + voice_id).
    Matches cost-control.md Section 9.2 TTS caching strategy.
    """
    raw = f"{question_text}:{voice_id}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _estimate_duration(text: str) -> float:
    """
    Estimate audio duration from word count.
    Formula: word_count / 2.5 (average speaking rate = 2.5 words/second).
    """
    word_count = len(text.split())
    return round(word_count / 2.5, 1)


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
        cache_key = _make_cache_key(question_text, effective_voice_id)

        if settings.TTS_CACHE_ENABLED and cache_key in _tts_cache:
            cached = _tts_cache[cache_key]
            return {
                "audio_url": cached["audio_url"],
                "duration_seconds": cached["duration_seconds"],
                "cached": True,
                "enabled": True,
            }

        if settings.USE_MOCK_TTS:
            result = self._mock_generate(question_text, cache_key)
        else:
            result = await self._real_generate(question_text, effective_voice_id, cache_key)

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
        cache_key: str,
    ) -> dict:
        """
        Real ElevenLabs TTS generation.
        Only called when USE_MOCK_TTS=false and ELEVENLABS_API_KEY is set.

        TODO Phase 2.3:
        - Upload generated audio to Supabase Storage / S3
        - Return permanent public URL instead of temp URL
        - Store cache entry in DB tts_cache table for persistence across restarts
        """
        if not settings.ELEVENLABS_API_KEY:
            raise VoiceGenerationError(
                "ELEVENLABS_API_KEY is not set. Set USE_MOCK_TTS=true for development."
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
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                raise VoiceGenerationError(
                    f"ElevenLabs returned {response.status_code}: {response.text[:200]}"
                )

            short_key = cache_key[:8]
            audio_url = f"https://storage.interviewos.dev/audio/{short_key}.mp3"
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
