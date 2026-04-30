from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.user import User


class UsageEvent(Base):
    __tablename__ = "usage_events"

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
    session_id: Mapped[UUID | None] = mapped_column(
        Uuid,
        ForeignKey("sessions.id"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    model_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    audio_duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    estimated_cost_usd: Mapped[float | None] = mapped_column(Numeric(10, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(back_populates="usage_events")
    session: Mapped[Optional["Session"]] = relationship(back_populates="usage_events")
