import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.answer import Answer as AnswerModel
from app.models.question import Question as QuestionModel
from app.models.report import Report as ReportModel
from app.models.score import Score as ScoreModel
from app.models.session import Session as SessionModel

SESSION_EXPIRY_MINUTES = 30


class SessionService:
    async def create_session(
        self,
        db: AsyncSession,
        *,
        user_id: str,
        resume_id: str | None,
        interview_type: str,
        difficulty: str,
        target_role: str = "",
        target_company: str = "",
        job_description: str = "",
        question_count: int = 5,
        voice_enabled: bool = True,
    ) -> SessionModel:
        now = datetime.now(timezone.utc)
        session = SessionModel(
            id=uuid.uuid4(),
            user_id=uuid.UUID(user_id),
            resume_id=uuid.UUID(resume_id) if resume_id else None,
            interview_type=interview_type,
            difficulty=difficulty,
            target_role=target_role or None,
            target_company=target_company or None,
            job_description=job_description or None,
            question_count=question_count,
            voice_enabled=voice_enabled,
            status="in_progress",
            current_sequence=0,
            started_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(minutes=SESSION_EXPIRY_MINUTES),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_session(self, db: AsyncSession, session_id: str) -> SessionModel | None:
        result = await db.execute(
            select(SessionModel).where(SessionModel.id == uuid.UUID(session_id))
        )
        return result.scalar_one_or_none()

    async def update_last_activity(self, db: AsyncSession, session_id: str) -> None:
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(last_activity_at=datetime.now(timezone.utc))
        )
        await db.commit()

    async def is_session_expired(self, session: SessionModel) -> bool:
        now = datetime.now(timezone.utc)
        last_activity = session.last_activity_at
        if last_activity.tzinfo is None:
            last_activity = last_activity.replace(tzinfo=timezone.utc)
        return (now - last_activity).total_seconds() > SESSION_EXPIRY_MINUTES * 60

    async def mark_expired(self, db: AsyncSession, session_id: str) -> None:
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(status="expired")
        )
        await db.commit()

    async def complete_session(self, db: AsyncSession, session_id: str) -> None:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(
                status="completed",
                ended_at=now,
                last_activity_at=now,
            )
        )
        await db.commit()

    async def create_question(
        self,
        db: AsyncSession,
        *,
        session_id: str,
        sequence: int,
        question_text: str,
        question_type: str,
        expected_focus_areas: list,
        audio_url: str | None,
        prompt_version: str,
    ) -> QuestionModel:
        now = datetime.now(timezone.utc)
        question = QuestionModel(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            sequence=sequence,
            question_text=question_text,
            question_type=question_type,
            expected_focus_areas=expected_focus_areas,
            audio_url=audio_url,
            prompt_version=prompt_version,
            created_at=now,
        )
        db.add(question)
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(current_sequence=sequence, last_activity_at=now)
        )
        await db.commit()
        await db.refresh(question)
        return question

    async def get_questions_for_session(
        self, db: AsyncSession, session_id: str
    ) -> list[QuestionModel]:
        result = await db.execute(
            select(QuestionModel)
            .where(QuestionModel.session_id == uuid.UUID(session_id))
            .order_by(QuestionModel.sequence)
        )
        return list(result.scalars().all())

    async def create_answer(
        self,
        db: AsyncSession,
        *,
        session_id: str,
        question_id: str,
        transcript: str,
        duration_seconds: int,
        word_count: int,
        filler_word_count: int,
    ) -> AnswerModel:
        now = datetime.now(timezone.utc)
        answer = AnswerModel(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            question_id=uuid.UUID(question_id),
            transcript=transcript,
            duration_seconds=duration_seconds,
            word_count=word_count,
            filler_word_count=filler_word_count,
            raw_audio_deleted=True,
            submitted_at=now,
        )
        db.add(answer)
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(last_activity_at=now)
        )
        await db.commit()
        await db.refresh(answer)
        return answer

    async def get_answer_for_question(
        self, db: AsyncSession, question_id: str
    ) -> AnswerModel | None:
        result = await db.execute(
            select(AnswerModel).where(AnswerModel.question_id == uuid.UUID(question_id))
        )
        return result.scalar_one_or_none()

    async def create_score(
        self,
        db: AsyncSession,
        *,
        session_id: str,
        question_id: str,
        answer_id: str,
        scores: dict,
        feedback_text: str,
        feedback_json: dict,
        prompt_version: str,
    ) -> ScoreModel:
        now = datetime.now(timezone.utc)
        score = ScoreModel(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            question_id=uuid.UUID(question_id),
            answer_id=uuid.UUID(answer_id),
            technical_score=scores.get("technical_correctness"),
            clarity_score=scores.get("clarity"),
            depth_score=scores.get("depth"),
            confidence_score=scores.get("confidence"),
            relevance_score=scores.get("relevance"),
            structure_score=scores.get("structure"),
            communication_score=scores.get("communication"),
            conciseness_score=scores.get("conciseness"),
            example_quality_score=scores.get("example_quality"),
            overall_score=scores.get("overall"),
            feedback_text=feedback_text,
            feedback_json=feedback_json,
            prompt_version=prompt_version,
            created_at=now,
        )
        db.add(score)
        await db.execute(
            update(SessionModel)
            .where(SessionModel.id == uuid.UUID(session_id))
            .values(last_activity_at=now)
        )
        await db.commit()
        await db.refresh(score)
        return score

    async def get_score_for_answer(
        self, db: AsyncSession, answer_id: str
    ) -> ScoreModel | None:
        result = await db.execute(
            select(ScoreModel).where(ScoreModel.answer_id == uuid.UUID(answer_id))
        )
        return result.scalar_one_or_none()

    async def create_report(
        self,
        db: AsyncSession,
        *,
        session_id: str,
        user_id: str,
        overall_score: float,
        score_breakdown: dict,
        summary: str,
        strengths: list,
        weaknesses: list,
        recommended_topics: list,
        question_reviews: list,
        transcript: list | None,
        prompt_version: str,
    ) -> ReportModel:
        report = ReportModel(
            id=uuid.uuid4(),
            session_id=uuid.UUID(session_id),
            user_id=uuid.UUID(user_id),
            overall_score=overall_score,
            score_breakdown=score_breakdown,
            summary=summary,
            strengths=strengths,
            weaknesses=weaknesses,
            recommended_topics=recommended_topics,
            question_reviews=question_reviews,
            transcript=transcript,
            prompt_version=prompt_version,
            created_at=datetime.now(timezone.utc),
        )
        db.add(report)
        await db.commit()
        await db.refresh(report)
        return report

    async def get_in_progress_sessions(
        self, db: AsyncSession, user_id: str
    ) -> list[SessionModel]:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(minutes=SESSION_EXPIRY_MINUTES)
        result = await db.execute(
            select(SessionModel)
            .where(
                SessionModel.user_id == uuid.UUID(user_id),
                SessionModel.status == "in_progress",
                SessionModel.last_activity_at >= cutoff,
            )
            .order_by(SessionModel.last_activity_at.desc())
        )
        return list(result.scalars().all())

    async def get_sessions_for_user(
        self,
        db: AsyncSession,
        user_id: str,
        status: str | None = None,
    ) -> list[SessionModel]:
        query = select(SessionModel).where(SessionModel.user_id == uuid.UUID(user_id))
        if status:
            query = query.where(SessionModel.status == status)
        query = query.order_by(SessionModel.started_at.desc()).limit(20)
        result = await db.execute(query)
        return list(result.scalars().all())
