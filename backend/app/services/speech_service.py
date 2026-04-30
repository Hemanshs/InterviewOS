from app.core.config import settings

USE_MOCK = settings.USE_MOCK_AI


class SpeechService:
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        session_id: str,
        question_id: str,
    ) -> dict:
        """
        TODO: Call OpenAI Whisper API or Deepgram.
        openai.audio.transcriptions.create(
            model="whisper-1",
            file=("answer.webm", audio_bytes, "audio/webm")
        )
        Validate duration <= 60s before sending.
        Delete raw audio after transcription.
        """
        if USE_MOCK:
            return self._mock_transcription()
        raise NotImplementedError("Real implementation not built yet")

    def _mock_transcription(self) -> dict:
        return {
            "transcript": "I would approach this by first identifying the bottleneck using profiling tools, then applying appropriate caching strategies and database query optimization.",
            "duration_seconds": 18,
            "word_count": 32,
            "filler_word_count": 1,
        }
