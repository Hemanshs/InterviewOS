from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Text, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.types import JSONBType

if TYPE_CHECKING:
    from app.models.session import Session
    from app.models.user import User


class Resume(Base):
    __tablename__ = "resumes"

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
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_profile: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSONBType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    # Soft delete: application queries must filter WHERE deleted_at IS NULL
    # Hard delete not performed; use deleted_at IS NOT NULL to find deleted records
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="resumes")
    sessions: Mapped[list["Session"]] = relationship(back_populates="resume")
