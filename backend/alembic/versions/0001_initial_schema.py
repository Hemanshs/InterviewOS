"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-30 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

planenum = postgresql.ENUM("free", "pro", "team", name="planenum", create_type=False)
sessionstatusenum = postgresql.ENUM(
    "in_progress",
    "completed",
    "abandoned",
    "expired",
    name="sessionstatusenum",
    create_type=False,
)


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    planenum.create(op.get_bind(), checkfirst=True)
    sessionstatusenum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("plan", planenum, server_default=sa.text("'free'"), nullable=False),
        sa.Column("free_interview_used", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("interviews_today", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("file_name", sa.Text(), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("parsed_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("interview_type", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.Text(), nullable=False),
        sa.Column("target_role", sa.Text(), nullable=True),
        sa.Column("target_company", sa.Text(), nullable=True),
        sa.Column("job_description", sa.Text(), nullable=True),
        sa.Column("status", sessionstatusenum, server_default=sa.text("'in_progress'"), nullable=False),
        sa.Column("current_sequence", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("question_type", sa.Text(), nullable=False),
        sa.Column("expected_focus_areas", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("filler_word_count", sa.Integer(), nullable=True),
        sa.Column("raw_audio_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "reports",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("score_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("strengths", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("weaknesses", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recommended_topics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("question_reviews", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("transcript", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", name="uq_reports_session_id"),
    )
    op.create_table(
        "usage_events",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("model_name", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("audio_duration_seconds", sa.Integer(), nullable=True),
        sa.Column("estimated_cost_usd", sa.Numeric(precision=10, scale=6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "scores",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("answer_id", sa.Uuid(), nullable=False),
        sa.Column("technical_score", sa.Integer(), nullable=True),
        sa.Column("clarity_score", sa.Integer(), nullable=True),
        sa.Column("depth_score", sa.Integer(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("relevance_score", sa.Integer(), nullable=True),
        sa.Column("structure_score", sa.Integer(), nullable=True),
        sa.Column("communication_score", sa.Integer(), nullable=True),
        sa.Column("conciseness_score", sa.Integer(), nullable=True),
        sa.Column("example_quality_score", sa.Integer(), nullable=True),
        sa.Column("overall_score", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("feedback_text", sa.Text(), nullable=True),
        sa.Column("prompt_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 0 AND technical_score <= 10)",
            name="ck_scores_technical_score_range",
        ),
        sa.CheckConstraint(
            "clarity_score IS NULL OR (clarity_score >= 0 AND clarity_score <= 10)",
            name="ck_scores_clarity_score_range",
        ),
        sa.CheckConstraint(
            "depth_score IS NULL OR (depth_score >= 0 AND depth_score <= 10)",
            name="ck_scores_depth_score_range",
        ),
        sa.CheckConstraint(
            "confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 10)",
            name="ck_scores_confidence_score_range",
        ),
        sa.CheckConstraint(
            "relevance_score IS NULL OR (relevance_score >= 0 AND relevance_score <= 10)",
            name="ck_scores_relevance_score_range",
        ),
        sa.CheckConstraint(
            "structure_score IS NULL OR (structure_score >= 0 AND structure_score <= 10)",
            name="ck_scores_structure_score_range",
        ),
        sa.CheckConstraint(
            "communication_score IS NULL OR (communication_score >= 0 AND communication_score <= 10)",
            name="ck_scores_communication_score_range",
        ),
        sa.CheckConstraint(
            "conciseness_score IS NULL OR (conciseness_score >= 0 AND conciseness_score <= 10)",
            name="ck_scores_conciseness_score_range",
        ),
        sa.CheckConstraint(
            "example_quality_score IS NULL OR (example_quality_score >= 0 AND example_quality_score <= 10)",
            name="ck_scores_example_quality_score_range",
        ),
        sa.ForeignKeyConstraint(["answer_id"], ["answers.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("scores")
    op.drop_table("usage_events")
    op.drop_table("reports")
    op.drop_table("answers")
    op.drop_table("questions")
    op.drop_table("sessions")
    op.drop_table("resumes")
    op.drop_table("users")
    sessionstatusenum.drop(op.get_bind(), checkfirst=True)
    planenum.drop(op.get_bind(), checkfirst=True)
