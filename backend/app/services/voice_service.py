import hashlib

from app.core.config import settings

USE_MOCK = settings.USE_MOCK_AI


class VoiceService:
    INTERVIEWER_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

    async def generate_question_audio(
        self,
        question_text: str,
        voice_id: str | None = None,
    ) -> str:
        """
        TODO: Call ElevenLabs TTS API.
        POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
        Headers: xi-api-key: settings.ELEVENLABS_API_KEY
        Body: {"text": voice_ready_text, "model_id": "eleven_monolingual_v1"}
        Upload audio to S3/Supabase storage.
        Return public audio_url.

        TTS CACHING: Before calling ElevenLabs, check cache:
        cache_key = sha256(question_text + voice_id)
        If cached audio_url exists for cache_key, return it immediately.
        """
        if USE_MOCK:
            return self._mock_audio_url(question_text)
        raise NotImplementedError("Real implementation not built yet")

    async def rewrite_for_voice(self, question_text: str) -> str:
        """
        TODO: Call llm_service with build_voice_rewrite_prompt(question_text).
        Make question sound natural when spoken aloud.
        """
        if USE_MOCK:
            return question_text
        raise NotImplementedError("Real implementation not built yet")

    def _mock_audio_url(self, question_text: str) -> str:
        h = hashlib.md5(question_text.encode()).hexdigest()[:8]
        return f"https://mock-audio.interviewos.dev/question_{h}.mp3"
