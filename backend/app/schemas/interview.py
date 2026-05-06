from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.audio import TranscribeData
from app.schemas.evaluation import EvaluateData, ReportData
from app.schemas.resume import CandidateProfile


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


class SessionLimits(BaseModel):
    max_questions: int
    max_answer_duration_seconds: int


class SessionNextAction(BaseModel):
    type: str
    endpoint: str


class SessionData(BaseModel):
    session_id: UUID
    resume_id: Optional[UUID] = None
    interview_type: str
    difficulty: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    voice_enabled: bool
    question_count: int
    status: str
    started_at: datetime
    limits: SessionLimits
    next_action: SessionNextAction
    expires_at: Optional[datetime] = None


class GenerateQuestionRequest(BaseModel):
    session_id: UUID
    mode: Literal["first", "next", "follow_up"] = "first"
    previous_answer_id: Optional[UUID] = None
    include_voice: bool = True
    question_count: int = Field(default=5, ge=1, le=5)


class QuestionData(BaseModel):
    question_id: UUID
    session_id: UUID
    sequence: int
    question_text: str
    question_type: str
    audio_url: Optional[str] = None
    voice_enabled: bool
    latency_state: Optional[dict] = None


class AudioData(BaseModel):
    enabled: bool
    provider: Literal["elevenlabs", "browser"] | None = None
    audio_url: Optional[str] = None
    duration_seconds: Optional[float] = None
    cached: bool = False
    label: str = ""
    upgrade_required: bool = False
    browser_speech_text: Optional[str] = None


class QuestionDetail(BaseModel):
    question_id: UUID
    sequence: int
    type: str
    difficulty: str
    question_text: str
    expected_focus_areas: list[str] = []
    time_limit_seconds: int = 60
    audio: AudioData


class LatencyState(BaseModel):
    current: str
    completed_steps: list[str] = []


class QuestionResponseData(BaseModel):
    session_id: UUID
    question: QuestionDetail
    latency_state: LatencyState


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


class CompletedAnswerData(BaseModel):
    questionNumber: int
    questionId: str
    questionText: str
    questionType: str
    answerId: str
    transcript: str
    wordCount: int
    scores: dict
    overallScore: float | None = None
    feedbackSummary: str
    strengths: list[str] = []
    improvements: list[str] = []


class SessionDetailData(BaseModel):
    session_id: UUID
    resume_id: Optional[UUID] = None
    interview_type: str
    difficulty: str
    target_role: Optional[str] = None
    target_company: Optional[str] = None
    job_description: Optional[str] = None
    question_count: int
    voice_enabled: bool
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    questions_answered: int
    current_sequence: int
    last_activity_at: datetime
    resume_profile: Optional[CandidateProfile] = None
    current_question: Optional[QuestionDetail] = None
    current_transcript: Optional[TranscribeData] = None
    current_evaluation: Optional[EvaluateData] = None
    completed_answers: list[CompletedAnswerData] = []
    final_report: Optional[ReportData] = None
