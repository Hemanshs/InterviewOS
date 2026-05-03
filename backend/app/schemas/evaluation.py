from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


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


class EvaluationScores(BaseModel):
    technical_correctness: Optional[int] = None
    clarity: Optional[int] = None
    depth: Optional[int] = None
    confidence: Optional[int] = None
    relevance: Optional[int] = None
    structure: Optional[int] = None
    communication: Optional[int] = None
    conciseness: Optional[int] = None
    example_quality: Optional[int] = None
    overall: Optional[float] = None


class EvaluationFeedback(BaseModel):
    summary: str
    strengths: list[str] = []
    improvements: list[str] = []
    ideal_answer_points: list[str] = []
    missed_points: list[str] = []
    suggested_better_answer: str = ""


class FollowUp(BaseModel):
    recommended: bool
    reason: str = ""
    question_text: Optional[str] = None


class EvaluationLatency(BaseModel):
    evaluation_ms: int


class EvaluateData(BaseModel):
    score_id: UUID
    session_id: UUID
    question_id: UUID
    answer_id: UUID
    scores: EvaluationScores
    feedback: EvaluationFeedback
    follow_up: FollowUp
    latency: EvaluationLatency

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_shape(cls, data):
        if not isinstance(data, dict) or "feedback" in data:
            return data

        legacy_scores = data.get("scores", {})
        return {
            **data,
            "scores": {
                "technical_correctness": legacy_scores.get("technical_score"),
                "clarity": legacy_scores.get("clarity_score"),
                "depth": legacy_scores.get("depth_score"),
                "confidence": legacy_scores.get("confidence_score"),
                "relevance": legacy_scores.get("relevance_score"),
                "structure": legacy_scores.get("structure_score"),
                "communication": legacy_scores.get("communication_score"),
                "conciseness": legacy_scores.get("conciseness_score"),
                "example_quality": legacy_scores.get("example_quality_score"),
                "overall": legacy_scores.get("overall_score"),
            },
            "feedback": {
                "summary": data.get("feedback_text", ""),
                "strengths": data.get("strengths", []),
                "improvements": data.get("improvements", []),
                "ideal_answer_points": [],
                "missed_points": [],
                "suggested_better_answer": "",
            },
            "follow_up": {
                "recommended": bool(data.get("follow_up_question")),
                "reason": "",
                "question_text": data.get("follow_up_question"),
            },
            "latency": {"evaluation_ms": 0},
        }


class FinalReportRequest(BaseModel):
    session_id: UUID
    include_transcript: bool = True
    include_recommendations: bool = True


class ScoreBreakdown(BaseModel):
    technical: float
    communication: float
    confidence: float
    problem_solving: float
    role_fit: float

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_breakdown(cls, data):
        if not isinstance(data, dict):
            return data

        if "problem_solving" in data and "role_fit" in data:
            return data

        return {
            **data,
            "problem_solving": data.get("problem_solving", data.get("clarity", data.get("technical", 0.0))),
            "role_fit": data.get("role_fit", data.get("overall", data.get("technical", 0.0))),
        }


class QuestionReviewItem(BaseModel):
    question_id: str
    sequence: int
    question_text: str
    answer_id: str
    overall_score: float
    feedback_summary: str


class TranscriptItem(BaseModel):
    question: str
    answer: str


class ReportData(BaseModel):
    report_id: UUID
    session_id: UUID
    status: str = "completed"
    overall_score: float
    score_breakdown: ScoreBreakdown
    summary: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommended_topics: list[str] = Field(default_factory=list)
    question_reviews: list[QuestionReviewItem] = Field(default_factory=list)
    transcript: Optional[list[TranscriptItem]] = None
    created_at: datetime


class ScorecardData(ReportData):
    pass
