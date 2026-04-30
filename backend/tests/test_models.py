import uuid
from decimal import Decimal

import pytest
import pytest_asyncio
from sqlalchemy import MetaData
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.models.answer import Answer
from app.models.question import Question
from app.models.report import Report
from app.models.score import Score
from app.models.session import Session
from app.models.user import User

# Note: SQLite is used only for lightweight model tests here.
# PostgreSQL remains the source of truth for production DDL and migrations.
# SQLite constraint behavior can differ from PostgreSQL, so migration validation
# should still be performed against Postgres before relying on these checks.


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    metadata = MetaData()

    for table in Base.metadata.sorted_tables:
        cloned_table = table.to_metadata(metadata)
        for column in cloned_table.columns:
            if column.server_default is not None and "gen_random_uuid()" in str(column.server_default.arg):
                column.server_default = None

    async with engine.begin() as connection:
        await connection.run_sync(metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db_session:
        yield db_session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user_instance_defaults(session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="candidate@example.com",
    )

    session.add(user)
    await session.commit()
    await session.refresh(user)

    assert user.email == "candidate@example.com"
    assert user.plan.value == "free"
    assert user.free_interview_used is False
    assert user.interviews_today == 0
    assert user.created_at is not None
    assert user.deleted_at is None


@pytest.mark.asyncio
async def test_create_session_with_nullable_resume_id(session: AsyncSession):
    user = User(
        id=uuid.uuid4(),
        email="session-user@example.com",
    )
    session.add(user)
    await session.flush()

    interview_session = Session(
        id=uuid.uuid4(),
        user_id=user.id,
        resume_id=None,
        interview_type="backend",
        difficulty="medium",
    )

    session.add(interview_session)
    await session.commit()
    await session.refresh(interview_session)

    assert interview_session.resume_id is None
    assert interview_session.status.value == "in_progress"
    assert interview_session.current_sequence == 0


@pytest.mark.asyncio
async def test_score_check_constraint_rejects_value_11(session: AsyncSession):
    user = User(id=uuid.uuid4(), email="score-user@example.com")
    session.add(user)
    await session.flush()

    interview_session = Session(
        id=uuid.uuid4(),
        user_id=user.id,
        resume_id=None,
        interview_type="backend",
        difficulty="hard",
    )
    session.add(interview_session)
    await session.flush()

    question = Question(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        sequence=1,
        question_text="Explain database indexing.",
        question_type="technical",
        prompt_version="v1",
    )
    session.add(question)
    await session.flush()

    answer = Answer(
        id=uuid.uuid4(),
        question_id=question.id,
        session_id=interview_session.id,
        transcript="Indexes improve lookup performance.",
    )
    session.add(answer)
    await session.flush()

    invalid_score = Score(
        id=uuid.uuid4(),
        session_id=interview_session.id,
        question_id=question.id,
        answer_id=answer.id,
        technical_score=11,
        clarity_score=8,
        depth_score=7,
        confidence_score=6,
        relevance_score=9,
        structure_score=8,
        communication_score=7,
        conciseness_score=8,
        example_quality_score=7,
        overall_score=Decimal("8.10"),
        prompt_version="v1",
    )

    session.add(invalid_score)

    with pytest.raises(IntegrityError):
        await session.commit()

    await session.rollback()


@pytest.mark.asyncio
async def test_prompt_version_columns_are_required(session: AsyncSession):
    assert Question.__table__.c.prompt_version.nullable is False
    assert Score.__table__.c.prompt_version.nullable is False
    assert Report.__table__.c.prompt_version.nullable is False
