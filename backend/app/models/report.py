from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, Text, Uuid, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.user import User


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("session_id", name="uq_reports_session_id"),)

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
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id"),
        nullable=False,
    )
    overall_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    score_breakdown: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    weaknesses: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    recommended_topics: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(
        JSONBType,
        nullable=True,
    )
    question_reviews: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    transcript: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    prompt_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # Soft delete: application queries must filter WHERE deleted_at IS NULL
    # Hard delete not performed; use deleted_at IS NOT NULL to find deleted records
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    session: Mapped["Session"] = relationship(back_populates="report")
    user: Mapped["User"] = relationship(back_populates="reports")
