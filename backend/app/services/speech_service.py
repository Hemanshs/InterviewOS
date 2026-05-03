import os
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Final

from app.core.config import settings
from app.core.exceptions import TranscriptionError
from app.utils.audio_utils import count_words, detect_filler_words

_CONTENT_TYPE_SUFFIXES: Final[dict[str, str]] = {
    "audio/webm": ".webm",
    "audio/webm;codecs=opus": ".webm",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/x-m4a": ".m4a",
    "audio/m4a": ".m4a",
    "video/mp4": ".mp4",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
    "audio/mpeg": ".mp3",
    "audio/mp3": ".mp3",
}
_TRANSCRIPTION_PROMPT: Final[str] = (
    "Transcribe the spoken words in this audio exactly. Return only the transcript text. "
    "Do not summarize. Do not add commentary."
)
_TRANSCRIPTION_STORE: dict[str, dict] = {}


class SpeechService:
    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        session_id: str,
        question_id: str,
        language: str = "en",
        duration_seconds: int = 0,
        content_type: str = "audio/webm",
    ) -> dict:
        """
        Main transcription entry point.
        Branches on USE_MOCK_STT setting.
        Returns dict matching TranscribeData schema.
        """
        start_ms = int(time.time() * 1000)

        if settings.USE_MOCK_STT:
            transcript = self._mock_transcript()
        else:
            transcript = await self._real_transcribe(audio_bytes, language, content_type)

        end_ms = int(time.time() * 1000)
        transcription_ms = end_ms - start_ms

        word_count = count_words(transcript)
        filler_words = detect_filler_words(transcript)

        # TODO Phase 2.2: Replace mock answer_id with real DB insert into answers table
        # DB insert should save:
        #   session_id, question_id, transcript, duration_seconds,
        #   word_count, filler_word_count, raw_audio_deleted=True
        answer_id = uuid.uuid4()

        return {
            "answer_id": answer_id,
            "session_id": uuid.UUID(str(session_id)),
            "question_id": uuid.UUID(str(question_id)),
            "transcript": transcript,
            "language": language,
            "duration_seconds": duration_seconds,
            "word_count": word_count,
            "filler_words": filler_words,
            "raw_audio_deleted": True,
            "submitted_at": datetime.now(timezone.utc),
            "latency": {"transcription_ms": transcription_ms},
        }

    def cache_transcription(self, data: dict) -> None:
        _TRANSCRIPTION_STORE[str(data["answer_id"])] = data

    def get_cached_transcription(self, answer_id: str | uuid.UUID) -> dict | None:
        return _TRANSCRIPTION_STORE.get(str(answer_id))

    def list_cached_transcriptions(self, session_id: str | uuid.UUID) -> list[dict]:
        session_key = str(session_id)
        return [
            item for item in _TRANSCRIPTION_STORE.values()
            if str(item.get("session_id")) == session_key
        ]

    def clear_cached_session(self, session_id: str | uuid.UUID) -> None:
        session_key = str(session_id)
        stale_ids = [
            answer_id
            for answer_id, item in _TRANSCRIPTION_STORE.items()
            if str(item.get("session_id")) == session_key
        ]
        for answer_id in stale_ids:
            _TRANSCRIPTION_STORE.pop(answer_id, None)

    def _get_temp_suffix(self, content_type: str) -> str:
        normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
        return _CONTENT_TYPE_SUFFIXES.get(normalized_content_type, ".bin")

    def _normalize_content_type(self, content_type: str) -> str:
        return (content_type or "").split(";", 1)[0].strip().lower()

    def _build_gemini_client(self):
        from google import genai

        return genai.Client(api_key=settings.GEMINI_API_KEY)

    def _get_gemini_types(self):
        from google.genai import types

        return types

    async def _real_transcribe(
        self,
        audio_bytes: bytes,
        language: str,
        content_type: str = "audio/webm",
    ) -> str:
        """
        Real transcription via Gemini API.
        Only called when USE_MOCK_STT=false and STT_PROVIDER=gemini.
        """
        if settings.STT_PROVIDER != "gemini":
            raise TranscriptionError(f"Unsupported STT provider: {settings.STT_PROVIDER}")
        if not settings.GEMINI_API_KEY:
            raise TranscriptionError(
                "GEMINI_API_KEY is required when USE_MOCK_STT=false and STT_PROVIDER=gemini"
            )

        normalized_content_type = self._normalize_content_type(content_type)
        tmp_path = None
        uploaded_file = None
        try:
            types = self._get_gemini_types()

            with tempfile.NamedTemporaryFile(
                suffix=self._get_temp_suffix(content_type),
                delete=False,
            ) as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            client = self._build_gemini_client()
            async with client.aio as aclient:
                try:
                    uploaded_file = await aclient.files.upload(
                        file=tmp_path,
                        config=types.UploadFileConfig(mime_type=normalized_content_type),
                    )
                    response = await aclient.models.generate_content(
                        model=settings.GEMINI_MODEL,
                        contents=[_TRANSCRIPTION_PROMPT, uploaded_file],
                        config=types.GenerateContentConfig(
                            temperature=0,
                            response_mime_type="text/plain",
                        ),
                    )
                    transcript = (getattr(response, "text", "") or "").strip()
                    if not transcript:
                        raise TranscriptionError("Gemini transcription returned an empty transcript")
                    return transcript
                finally:
                    if uploaded_file and getattr(uploaded_file, "name", None):
                        try:
                            await aclient.files.delete(name=uploaded_file.name)
                        except Exception:
                            pass
        except Exception as e:
            if isinstance(e, TranscriptionError):
                raise
            raise TranscriptionError(f"Gemini transcription failed: {str(e)}") from e
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _mock_transcript(self) -> str:
        return (
            "I would first identify whether the issue is caused by timing, "
            "unstable selectors, shared state, or external dependencies. "
            "For timing issues, I would add explicit waits rather than fixed sleeps. "
            "For unstable selectors, I would use data-testid attributes or more "
            "resilient locator strategies. I would also ensure tests are isolated "
            "with proper setup and teardown to avoid shared state contamination."
        )

    def _mock_transcription(self) -> dict:
        """Legacy mock method kept for test_services.py compatibility."""
        transcript = self._mock_transcript()
        return {
            "transcript": transcript,
            "language": "en",
            "duration_seconds": 18,
            "word_count": count_words(transcript),
            "filler_words": detect_filler_words(transcript),
            "submitted_at": datetime.now(timezone.utc),
            "latency": {"transcription_ms": 1},
            "filler_word_count": 1,
        }
