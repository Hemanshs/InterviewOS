from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.score import Score
    from app.models.session import Session


class Question(Base):
    __tablename__ = "questions"

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
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str] = mapped_column(Text, nullable=False)
    expected_focus_areas: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONBType,
        nullable=True,
    )
    audio_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    session: Mapped["Session"] = relationship(back_populates="questions")
    answer: Mapped[Optional["Answer"]] = relationship(back_populates="question", uselist=False)
    score: Mapped[Optional["Score"]] = relationship(back_populates="question", uselist=False)
