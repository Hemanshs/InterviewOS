from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TranscribeData(BaseModel):
    answer_id: UUID
    session_id: UUID
    question_id: UUID
    transcript: str
    duration_seconds: Optional[int] = None
    word_count: Optional[int] = None
    filler_word_count: Optional[int] = None
    raw_audio_deleted: bool
