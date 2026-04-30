from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Integer, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PlanEnum

if TYPE_CHECKING:
    from app.models.report import Report
    from app.models.resume import Resume
    from app.models.session import Session
    from app.models.usage_event import UsageEvent


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    plan: Mapped[PlanEnum] = mapped_column(
        Enum(PlanEnum),
        server_default=text("'free'"),
        nullable=False,
    )
    free_interview_used: Mapped[bool] = mapped_column(
        Boolean,
        server_default=text("false"),
        nullable=False,
    )
    interviews_today: Mapped[int] = mapped_column(
        Integer,
        server_default=text("0"),
        nullable=False,
    )
    # Soft delete: application queries must filter WHERE deleted_at IS NULL
    # Hard delete not performed; use deleted_at IS NOT NULL to find deleted records
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    resumes: Mapped[list["Resume"]] = relationship(back_populates="user")
    sessions: Mapped[list["Session"]] = relationship(back_populates="user")
    reports: Mapped[list["Report"]] = relationship(back_populates="user")
    usage_events: Mapped[list["UsageEvent"]] = relationship(back_populates="user")
