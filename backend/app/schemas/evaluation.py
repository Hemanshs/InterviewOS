from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ScoreDetail(BaseModel):
    technical_score: Optional[int] = Field(default=None, ge=0, le=10)
    clarity_score: Optional[int] = Field(default=None, ge=0, le=10)
    depth_score: Optional[int] = Field(default=None, ge=0, le=10)
    confidence_score: Optional[int] = Field(default=None, ge=0, le=10)
    relevance_score: Optional[int] = Field(default=None, ge=0, le=10)
    structure_score: Optional[int] = Field(default=None, ge=0, le=10)
    communication_score: Optional[int] = Field(default=None, ge=0, le=10)
    conciseness_score: Optional[int] = Field(default=None, ge=0, le=10)
    example_quality_score: Optional[int] = Field(default=None, ge=0, le=10)
    overall_score: Optional[float] = None


class EvaluateAnswerRequest(BaseModel):
    session_id: UUID
    question_id: UUID
    answer_id: UUID
    generate_follow_up: bool = True


class EvaluateData(BaseModel):
    score_id: UUID
    session_id: UUID
    question_id: UUID
    answer_id: UUID
    scores: ScoreDetail
    feedback_text: str
    strengths: list[str]
    improvements: list[str]
    follow_up_question: Optional[str] = None


class FinalReportRequest(BaseModel):
    session_id: UUID
    include_transcript: bool = True
    include_recommendations: bool = True


class ScoreBreakdown(BaseModel):
    technical: Optional[float] = None
    communication: Optional[float] = None
    confidence: Optional[float] = None
    clarity: Optional[float] = None
    overall: Optional[float] = None


class QuestionReview(BaseModel):
    sequence: int
    question_text: str
    transcript: Optional[str] = None
    scores: ScoreDetail
    feedback_text: Optional[str] = None


class ReportData(BaseModel):
    report_id: UUID
    session_id: UUID
    overall_score: Optional[float] = None
    score_breakdown: ScoreBreakdown
    summary: Optional[str] = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    question_reviews: list[QuestionReview] = Field(default_factory=list)
    transcript: Optional[list[dict]] = None
    created_at: datetime


class ScorecardData(ReportData):
    pass
