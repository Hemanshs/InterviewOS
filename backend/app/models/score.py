from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.question import Question
    from app.models.session import Session


class Score(Base):
    __tablename__ = "scores"
    __table_args__ = (
        CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 0 AND technical_score <= 10)",
            name="ck_scores_technical_score_range",
        ),
        CheckConstraint(
            "clarity_score IS NULL OR (clarity_score >= 0 AND clarity_score <= 10)",
            name="ck_scores_clarity_score_range",
        ),
        CheckConstraint(
            "depth_score IS NULL OR (depth_score >= 0 AND depth_score <= 10)",
            name="ck_scores_depth_score_range",
        ),
        CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 10)",
            name="ck_scores_confidence_score_range",
        ),
        CheckConstraint(
            "relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 10)",
            name="ck_scores_relevance_score_range",
        ),
        CheckConstraint(
            "structure_score IS NULL OR (structure_score >= 0 AND structure_score <= 10)",
            name="ck_scores_structure_score_range",
        ),
        CheckConstraint(
            "communication_score IS NULL OR (communication_score >= 0 AND communication_score <= 10)",
            name="ck_scores_communication_score_range",
        ),
        CheckConstraint(
            "conciseness_score IS NULL OR (conciseness_score >= 0 AND conciseness_score <= 10)",
            name="ck_scores_conciseness_score_range",
        ),
        CheckConstraint(
            "example_quality_score IS NULL OR (example_quality_score >= 0 AND example_quality_score <= 10)",
            name="ck_scores_example_quality_score_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("sessions.id"),
        nullable=False,
    )
    question_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("questions.id"),
        nullable=False,
    )
    answer_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("answers.id"),
        nullable=False,
    )
    technical_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    clarity_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    relevance_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    structure_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    communication_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    conciseness_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    example_quality_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overall_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    feedback_json: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    feedback_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["Session"] = relationship(back_populates="scores")
    question: Mapped["Question"] = relationship(back_populates="score")
    answer: Mapped["Answer"] = relationship(back_populates="score")
