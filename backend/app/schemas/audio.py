from datetime import datetime

from pydantic import BaseModel
from uuid import UUID


class FillerWordData(BaseModel):
    count: int
    examples: list[str] = []


class TranscribeLatency(BaseModel):
    transcription_ms: int


class TranscribeData(BaseModel):
    answer_id: UUID
    session_id: UUID
    question_id: UUID
    transcript: str
    language: str = "en"
    duration_seconds: int
    word_count: int
    filler_words: FillerWordData
    raw_audio_deleted: bool
    submitted_at: datetime
    latency: TranscribeLatency
