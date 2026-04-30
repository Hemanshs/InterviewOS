from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.question import Question
    from app.models.score import Score
    from app.models.session import Session


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    question_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("questions.id"),
        nullable=False,
    )
    session_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("sessions.id"),
        nullable=False,
    )
    transcript: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filler_word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_audio_deleted: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    question: Mapped["Question"] = relationship(back_populates="answer")
    session: Mapped["Session"] = relationship(back_populates="answers")
    score: Mapped[Optional["Score"]] = relationship(back_populates="answer", uselist=False)
