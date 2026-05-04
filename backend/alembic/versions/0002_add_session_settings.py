"""add session question_count and voice_enabled

Revision ID: 0002_add_session_settings
Revises: 0001_initial_schema
Create Date: 2026-05-04
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_add_session_settings"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("question_count", sa.Integer(), nullable=False, server_default="5"),
    )
    op.add_column(
        "sessions",
        sa.Column("voice_enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )


def downgrade() -> None:
    op.drop_column("sessions", "voice_enabled")
    op.drop_column("sessions", "question_count")
