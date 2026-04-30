from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import SessionStatusEnum

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.question import Question
    from app.models.report import Report
    from app.models.resume import Resume
    from app.models.score import Score
    from app.models.usage_event import UsageEvent
    from app.models.user import User


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    resume_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("resumes.id"),
        nullable=True,
    )
    interview_type: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(Text, nullable=False)
    target_role: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_company: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SessionStatusEnum] = mapped_column(
        Enum(SessionStatusEnum),
        server_default=text("'in_progress'"),
        nullable=False,
    )
    current_sequence: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")
    resume: Mapped[Optional["Resume"]] = relationship(back_populates="sessions")
    questions: Mapped[list["Question"]] = relationship(back_populates="session")
    answers: Mapped[list["Answer"]] = relationship(back_populates="session")
    scores: Mapped[list["Score"]] = relationship(back_populates="session")
    report: Mapped[Optional["Report"]] = relationship(back_populates="session", uselist=False)
    usage_events: Mapped[list["UsageEvent"]] = relationship(back_populates="session")
