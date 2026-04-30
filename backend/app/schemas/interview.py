from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StartInterviewRequest(BaseModel):
    resume_id: Optional[UUID] = None
    interview_type: Literal[
        "sde",
        "sdet",
        "backend",
        "behavioral",
        "system_design",
        "resume_based",
        "jd_based",
    ]
    difficulty: Literal["easy", "medium", "hard"] = "medium"
    job_description: Optional[str] = None
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    question_count: int = Field(default=5, ge=1, le=5)
    voice_enabled: bool = True


class SessionData(BaseModel):
    session_id: UUID
    interview_type: str
    difficulty: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    question_count: int
    voice_enabled: bool
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None


class GenerateQuestionRequest(BaseModel):
    session_id: UUID
    mode: Literal["first", "next", "follow_up"] = "next"
    previous_answer_id: Optional[UUID] = None
    include_voice: bool = True


class QuestionData(BaseModel):
    question_id: UUID
    session_id: UUID
    sequence: int
    question_text: str
    question_type: str
    audio_url: Optional[str] = None
    voice_enabled: bool
    latency_state: Optional[dict] = None


class HistoryItem(BaseModel):
    session_id: UUID
    interview_type: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    status: str
    question_count: int
    overall_score: Optional[float] = None
    started_at: datetime
    ended_at: Optional[datetime] = None


class Pagination(BaseModel):
    page: int
    limit: int
    total_items: int
    total_pages: int


class HistoryData(BaseModel):
    items: list[HistoryItem]
    pagination: Pagination


class SessionDetailData(BaseModel):
    session_id: UUID
    interview_type: str
    difficulty: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    question_count: int
    voice_enabled: bool
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    questions_answered: int
    current_sequence: int
    last_activity_at: datetime
