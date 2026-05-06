import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LLMError
from app.core.security import get_current_user
from app.db.database import get_async_session, get_or_create_user
from app.models.answer import Answer as AnswerModel
from app.models.question import Question as QuestionModel
from app.models.report import Report as ReportModel
from app.models.resume import Resume as ResumeModel
from app.models.score import Score as ScoreModel
from app.models.session import Session as SessionModel
from app.models.user import User as UserModel
from app.schemas import (
    AudioData,
    CandidateProfile,
    CompletedAnswerData,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    EvaluateAnswerRequest,
    EvaluateData,
    EvaluationFeedback,
    EvaluationLatency,
    EvaluationScores,
    FinalReportRequest,
    FollowUp,
    GenerateQuestionRequest,
    HistoryData,
    HistoryItem,
    LatencyState,
    Pagination,
    QuestionDetail,
    QuestionResponseData,
    QuestionReviewItem,
    ReportData,
    ScoreBreakdown,
    ScorecardData,
    SessionData,
    SessionDetailData,
    SessionLimits,
    SessionNextAction,
    StartInterviewRequest,
    SuccessResponse,
    TranscriptItem,
    TranscribeData,
    not_implemented,
)
from app.services.llm_service import LLMService
from app.services.session_service import SESSION_EXPIRY_MINUTES, SessionService
from app.services.speech_service import SpeechService
from app.services.voice_access_service import get_voice_access_for_question
from app.services.voice_service import VoiceService

router = APIRouter(prefix="/interview", tags=["Interviews"])
logger = logging.getLogger("interviewos.tts")
voice_service = VoiceService()
llm_service = LLMService()
speech_service = SpeechService()
session_service = SessionService()
MAX_QUESTIONS_PER_SESSION = 5

MOCK_QUESTIONS = [
    {
        "text": "Can you explain how you would design a backend API that handles validation, authentication, and database writes?",
        "type": "technical",
        "focus_areas": ["API design", "validation", "authentication", "database", "error handling"],
    },
    {
        "text": "Your experience includes CI/CD pipelines. How did you handle test flakiness in automated suites?",
        "type": "technical",
        "focus_areas": ["test automation", "CI/CD", "flaky tests", "debugging", "stability"],
    },
    {
        "text": "How would you approach debugging a memory leak in a long-running Python service?",
        "type": "technical",
        "focus_areas": ["debugging", "memory management", "profiling", "Python", "monitoring"],
    },
    {
        "text": "Describe a time you had to make a tradeoff between code quality and delivery speed.",
        "type": "behavioral",
        "focus_areas": ["decision making", "tradeoffs", "communication", "ownership", "pragmatism"],
    },
    {
        "text": "How do you ensure database queries stay performant as data grows?",
        "type": "technical",
        "focus_areas": ["database", "indexing", "query optimization", "scaling", "monitoring"],
    },
]


def _status_value(value: object) -> str:
    return getattr(value, "value", value) if value is not None else ""


async def _load_resume_profile(db: AsyncSession, resume_id: UUID | None) -> dict | None:
    if not resume_id:
        return None
    result = await db.execute(select(ResumeModel).where(ResumeModel.id == resume_id))
    resume = result.scalar_one_or_none()
    if resume and isinstance(resume.parsed_profile, dict):
        return resume.parsed_profile
    return None


def _mock_question(sequence: int) -> dict:
    question_payload = MOCK_QUESTIONS[(sequence - 1) % len(MOCK_QUESTIONS)]
    return {
        "question_text": question_payload["text"],
        "question_type": question_payload["type"],
        "difficulty": "medium",
        "expected_focus_areas": question_payload["focus_areas"],
        "time_limit_seconds": settings.FREE_MAX_AUDIO_SECONDS,
        "prompt_version": "mock_question_v1.0",
    }


def _sanitize_question_result(question_result: dict, *, difficulty: str, mode: str) -> dict:
    question_text = question_result.get("question_text")
    if isinstance(question_text, str) and llm_service._looks_structured_text(question_text):
        return llm_service._coerce_question_result_from_text(
            question_text,
            difficulty=question_result.get("difficulty", difficulty),
            mode=mode,
        )
    return question_result


def _mock_evaluation() -> dict:
    return {
        "scores": {
            "technical_correctness": 8,
            "clarity": 7,
            "depth": 8,
            "confidence": 7,
            "relevance": 9,
            "structure": 7,
            "communication": 7,
            "conciseness": 6,
            "example_quality": 8,
            "overall": 7.5,
        },
        "feedback": {
            "summary": "Strong answer with good coverage of the topic. You demonstrated solid understanding of the core concepts.",
            "strengths": [
                "Clear explanation of the approach",
                "Identified key considerations",
                "Connected answer to real-world context",
            ],
            "improvements": [
                "Could include a specific real-world example",
                "Answer could be more concise",
                "Consider mentioning edge cases",
            ],
            "ideal_answer_points": [
                "Define the problem scope clearly",
                "Describe the chosen approach and why",
                "Mention error handling and edge cases",
                "Reference a concrete example or project",
                "Summarize with a clear conclusion",
            ],
            "missed_points": [
                "A concrete example from production experience",
                "Specific trade-offs or edge cases",
            ],
            "suggested_better_answer": (
                "I would structure the answer by defining the problem, outlining the "
                "approach, discussing trade-offs, and closing with a real example."
            ),
        },
        "follow_up": {
            "recommended": True,
            "reason": "A follow-up would help validate the candidate with a concrete example.",
            "question_text": "Can you give a specific example from your experience where you applied this approach?",
        },
    }


def _mock_report() -> dict:
    return {
        "overall_score": 7.6,
        "score_breakdown": {
            "technical": 7.8,
            "communication": 7.2,
            "confidence": 7.0,
            "problem_solving": 8.0,
            "role_fit": 7.9,
        },
        "summary": (
            "Strong performance across technical and reasoning areas. "
            "You demonstrated solid backend API understanding and good "
            "problem-solving instincts. Communication was generally clear, "
            "but answers can be more structured and concise in places."
        ),
        "strengths": [
            "Solid understanding of backend API design principles",
            "Good reasoning about system trade-offs",
            "Consistent relevance to the question asked",
            "Able to connect answers to CI/CD and reliability concerns",
        ],
        "weaknesses": [
            "Answers could benefit from more concrete project examples",
            "STAR-style structure would improve behavioral answers",
            "Some answers ran slightly long — practice conciseness",
        ],
        "recommended_topics": [
            "System design fundamentals",
            "Behavioral STAR method",
            "Database indexing and query optimization",
            "CI/CD observability and metrics",
            "API rate limiting patterns",
        ],
    }


def _score_to_evaluation_payload(
    score: ScoreModel,
    session_id: UUID,
    question_id: UUID,
    answer_id: UUID,
) -> EvaluateData:
    feedback_json = score.feedback_json if isinstance(score.feedback_json, dict) else {}
    return EvaluateData(
        score_id=score.id,
        session_id=session_id,
        question_id=question_id,
        answer_id=answer_id,
        scores=EvaluationScores(
            technical_correctness=score.technical_score,
            clarity=score.clarity_score,
            depth=score.depth_score,
            confidence=score.confidence_score,
            relevance=score.relevance_score,
            structure=score.structure_score,
            communication=score.communication_score,
            conciseness=score.conciseness_score,
            example_quality=score.example_quality_score,
            overall=float(score.overall_score) if score.overall_score is not None else None,
        ),
        feedback=EvaluationFeedback(
            summary=feedback_json.get("summary", score.feedback_text or ""),
            strengths=list(feedback_json.get("strengths", [])),
            improvements=list(feedback_json.get("improvements", [])),
            ideal_answer_points=list(feedback_json.get("ideal_answer_points", [])),
            missed_points=list(feedback_json.get("missed_points", [])),
            suggested_better_answer=feedback_json.get("suggested_better_answer", ""),
        ),
        follow_up=FollowUp(
            recommended=False,
            reason="",
            question_text=None,
        ),
        latency=EvaluationLatency(evaluation_ms=0),
    )


@router.post("/start", response_model=SuccessResponse[SessionData])
async def start_interview(
    body: StartInterviewRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    if body.interview_type == "jd_based" and not (body.job_description or "").strip():
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="job_description is required for jd_based interviews",
                )
            ).model_dump(),
        )

    user_id = await get_or_create_user(db, str(current_user))
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(str(current_user)))
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="Authenticated user record could not be created",
                )
            ).model_dump(),
        )

    if str(getattr(user.plan, "value", user.plan)) == "free" and user.free_interview_used:
        return JSONResponse(
            status_code=429,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.RATE_LIMIT_EXCEEDED,
                    message="You have used your free interview. Upgrade to continue.",
                    details={"upgrade_required": True},
                )
            ).model_dump(),
        )

    if body.resume_id:
        resume_profile = await _load_resume_profile(db, body.resume_id)
        if body.interview_type == "resume_based" and not resume_profile:
            return JSONResponse(
                status_code=400,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.VALIDATION_ERROR,
                        message="resume_id is required for resume_based interviews and must refer to a parsed resume",
                    )
                ).model_dump(),
            )
    elif body.interview_type == "resume_based":
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="resume_id is required for resume_based interviews",
                )
            ).model_dump(),
        )

    db_session = await session_service.create_session(
        db,
        user_id=user_id,
        resume_id=str(body.resume_id) if body.resume_id else None,
        interview_type=body.interview_type,
        difficulty=body.difficulty,
        target_role=body.target_role or "",
        target_company=body.target_company or "",
        job_description=body.job_description or "",
        question_count=body.question_count,
        voice_enabled=body.voice_enabled,
    )

    if str(getattr(user.plan, "value", user.plan)) == "free":
        await db.execute(
            sa_update(UserModel)
            .where(UserModel.id == UUID(str(current_user)))
            .values(free_interview_used=True)
        )
        await db.commit()

    return SuccessResponse(
        data=SessionData(
            session_id=db_session.id,
            resume_id=body.resume_id,
            interview_type=db_session.interview_type,
            difficulty=db_session.difficulty,
            target_role=db_session.target_role,
            target_company=db_session.target_company,
            voice_enabled=body.voice_enabled,
            question_count=body.question_count,
            status=_status_value(db_session.status),
            started_at=db_session.started_at,
            limits=SessionLimits(
                max_questions=db_session.question_count,
                max_answer_duration_seconds=settings.FREE_MAX_AUDIO_SECONDS,
            ),
            next_action=SessionNextAction(
                type="generate_question",
                endpoint="/api/interview/question",
            ),
            expires_at=db_session.expires_at,
        ),
        message="Interview session started",
    )


@router.post(
    "/question",
    response_model=SuccessResponse[QuestionResponseData],
    summary="Generate next interview question with optional voice",
)
async def generate_question(
    body: GenerateQuestionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))
    user_result = await db.execute(select(UserModel).where(UserModel.id == UUID(user_id)))
    user = user_result.scalar_one_or_none()
    db_session = await session_service.get_session(db, str(body.session_id))

    if not user:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {"code": "USER_NOT_FOUND", "message": "User not found"},
            },
        )

    if not db_session:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            },
        )

    if str(db_session.user_id) != user_id:
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {"code": "SESSION_NOT_FOUND", "message": "Session not found"},
            },
        )

    if await session_service.is_session_expired(db_session):
        await session_service.mark_expired(db, str(body.session_id))
        raise HTTPException(
            status_code=410,
            detail={
                "success": False,
                "error": {"code": "SESSION_EXPIRED", "message": "Session has expired"},
            },
        )

    if _status_value(db_session.status) == "completed":
        raise HTTPException(
            status_code=409,
            detail={
                "success": False,
                "error": {
                    "code": "SESSION_ALREADY_COMPLETED",
                    "message": "Session is already completed",
                },
            },
        )

    existing_questions = await session_service.get_questions_for_session(db, str(body.session_id))
    sequence = len(existing_questions) + 1
    session_question_limit = min(db_session.question_count, MAX_QUESTIONS_PER_SESSION)

    if sequence > session_question_limit:
        raise HTTPException(
            status_code=429,
            detail={
                "success": False,
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Maximum questions reached for this session",
                    "details": {
                        "max_questions": session_question_limit,
                        "current_questions": len(existing_questions),
                    },
                },
            },
        )

    candidate_profile = await _load_resume_profile(db, db_session.resume_id)
    previous_questions = [q.question_text for q in existing_questions]
    previous_scores_rows = []
    if existing_questions:
        score_result = await db.execute(
            select(ScoreModel)
            .where(ScoreModel.session_id == db_session.id)
            .order_by(ScoreModel.created_at)
        )
        previous_scores_rows = list(score_result.scalars().all())

    previous_answer_transcript = ""
    if body.previous_answer_id:
        cached_answer = speech_service.get_cached_transcription(body.previous_answer_id)
        if cached_answer:
            previous_answer_transcript = cached_answer.get("transcript", "")
        else:
            answer_result = await db.execute(
                select(AnswerModel).where(AnswerModel.id == body.previous_answer_id)
            )
            answer_row = answer_result.scalar_one_or_none()
            if answer_row and answer_row.transcript:
                previous_answer_transcript = answer_row.transcript

    if settings.USE_MOCK_LLM:
        question_result = _mock_question(sequence)
    else:
        try:
            question_result = await llm_service.generate_question(
                mode=body.mode if body.mode else ("first" if sequence == 1 else "next"),
                sequence=sequence,
                interview_type=db_session.interview_type,
                difficulty=db_session.difficulty,
                question_count=session_question_limit,
                target_role=db_session.target_role or "",
                target_company=db_session.target_company or "",
                candidate_profile=candidate_profile,
                job_analysis={
                    "job_description": db_session.job_description,
                    "target_role": db_session.target_role,
                    "target_company": db_session.target_company,
                },
                previous_questions=previous_questions,
                previous_scores=[
                    {
                        "overall": float(score.overall_score) if score.overall_score is not None else None,
                        "technical_correctness": score.technical_score,
                        "clarity": score.clarity_score,
                        "depth": score.depth_score,
                        "confidence": score.confidence_score,
                        "relevance": score.relevance_score,
                        "structure": score.structure_score,
                        "communication": score.communication_score,
                        "conciseness": score.conciseness_score,
                        "example_quality": score.example_quality_score,
                    }
                    for score in previous_scores_rows
                ],
                previous_answer_transcript=previous_answer_transcript,
                evaluation_feedback=(
                    previous_scores_rows[-1].feedback_text if previous_scores_rows else ""
                ),
            )
        except LLMError as exc:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.LLM_FAILED,
                        message=exc.message,
                    )
                ).model_dump(),
            )

    question_result = _sanitize_question_result(
        question_result,
        difficulty=db_session.difficulty,
        mode=body.mode if body.mode else ("first" if sequence == 1 else "next"),
    )

    voice_access = get_voice_access_for_question(user, sequence)
    audio_data = AudioData(enabled=False)
    completed_steps = ["question_generated"]
    elevenlabs_called = False
    if body.include_voice:
        if voice_access["provider"] == "elevenlabs":
            elevenlabs_called = True
            try:
                tts_result = await voice_service.generate_question_audio(
                    question_text=question_result["question_text"]
                )
                audio_data = AudioData(
                    enabled=True,
                    provider="elevenlabs",
                    audio_url=tts_result["audio_url"],
                    duration_seconds=tts_result["duration_seconds"],
                    cached=tts_result["cached"],
                    label=voice_access["label"],
                    upgrade_required=False,
                    browser_speech_text=None,
                )
                completed_steps.append("voice_generated")
            except Exception as exc:
                logger.warning("Question TTS generation failed: %s", exc)
                audio_data = AudioData(
                    enabled=True,
                    provider="browser",
                    audio_url=None,
                    duration_seconds=None,
                    cached=False,
                    label="Standard Voice",
                    upgrade_required=False if str(getattr(user.plan, "value", user.plan)) == "pro" else voice_access["upgrade_required"],
                    browser_speech_text=question_result["question_text"],
                )
        elif voice_access["provider"] == "browser":
            audio_data = AudioData(
                enabled=True,
                provider="browser",
                audio_url=None,
                duration_seconds=None,
                cached=False,
                label="Standard Voice",
                upgrade_required=True,
                browser_speech_text=question_result["question_text"],
            )
    else:
        audio_data = AudioData(
            enabled=False,
            provider=None,
            audio_url=None,
            duration_seconds=None,
            cached=False,
            label="",
            upgrade_required=False,
            browser_speech_text=None,
        )

    logger.info(
        "voice_access user_id=%s plan=%s question_sequence=%s voice_provider=%s elevenlabs_called=%s cached=%s",
        user_id,
        str(getattr(user.plan, "value", user.plan)),
        sequence,
        audio_data.provider,
        elevenlabs_called,
        audio_data.cached,
    )

    db_question = await session_service.create_question(
        db,
        session_id=str(body.session_id),
        sequence=sequence,
        question_text=question_result["question_text"],
        question_type=question_result.get("question_type", "technical"),
        expected_focus_areas=question_result.get("expected_focus_areas", []),
        audio_url=audio_data.audio_url,
        prompt_version=question_result.get("prompt_version", "first_question_v1.0"),
    )

    question_detail = QuestionDetail(
        question_id=db_question.id,
        sequence=sequence,
        type=db_question.question_type,
        difficulty=question_result.get("difficulty", db_session.difficulty),
        question_text=db_question.question_text,
        expected_focus_areas=list(db_question.expected_focus_areas or []),
        time_limit_seconds=question_result.get(
            "time_limit_seconds", settings.FREE_MAX_AUDIO_SECONDS
        ),
        audio=audio_data,
    )

    return SuccessResponse(
        data=QuestionResponseData(
            session_id=body.session_id,
            question=question_detail,
            latency_state=LatencyState(
                current="ready_for_answer",
                completed_steps=completed_steps,
            ),
        ),
        message="Question generated successfully",
    )


@router.delete("/question/reset-mock/{session_id}", include_in_schema=False)
async def reset_mock_session(session_id: str):
    speech_service.clear_cached_session(session_id)
    return {"reset": True}


@router.post(
    "/evaluate",
    response_model=SuccessResponse[EvaluateData],
    summary="Evaluate candidate answer and return scores + feedback",
)
async def evaluate_answer(
    body: EvaluateAnswerRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    start_ms = int(time.time() * 1000)
    user_id = await get_or_create_user(db, str(current_user))
    db_session = await session_service.get_session(db, str(body.session_id))
    if db_session and str(db_session.user_id) != user_id:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.SESSION_NOT_FOUND,
                    message="Session not found",
                )
            ).model_dump(),
        )

    question_row = None
    answer_row = None
    question_text = "Question text unavailable"
    transcript = "Answer transcript unavailable"

    result = await db.execute(select(QuestionModel).where(QuestionModel.id == body.question_id))
    question_row = result.scalar_one_or_none()
    if question_row:
        question_text = question_row.question_text

    result = await db.execute(select(AnswerModel).where(AnswerModel.id == body.answer_id))
    answer_row = result.scalar_one_or_none()
    if answer_row and answer_row.transcript:
        transcript = answer_row.transcript
    else:
        cached = speech_service.get_cached_transcription(body.answer_id)
        if cached and cached.get("transcript"):
            transcript = cached["transcript"]

    if settings.USE_MOCK_LLM:
        evaluation_result = _mock_evaluation()
    else:
        try:
            evaluation_result = await llm_service.evaluate_answer(
                question_text=question_text,
                transcript=transcript,
                expected_focus_areas=list(question_row.expected_focus_areas or []) if question_row else [],
                candidate_profile=(
                    await _load_resume_profile(db, db_session.resume_id) if db_session else None
                ),
                job_analysis={
                    "job_description": db_session.job_description if db_session else None,
                    "target_role": db_session.target_role if db_session else None,
                    "target_company": db_session.target_company if db_session else None,
                },
                interview_type=db_session.interview_type if db_session else "sde",
            )
        except LLMError as exc:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.LLM_FAILED,
                        message=exc.message,
                    )
                ).model_dump(),
            )

    end_ms = int(time.time() * 1000)
    evaluation_ms = end_ms - start_ms

    if db_session and question_row and answer_row:
        db_score = await session_service.create_score(
            db,
            session_id=str(body.session_id),
            question_id=str(body.question_id),
            answer_id=str(body.answer_id),
            scores=evaluation_result["scores"],
            feedback_text=evaluation_result["feedback"].get("summary", ""),
            feedback_json=evaluation_result["feedback"],
            prompt_version="answer_evaluation_v1.0",
        )
        score_id = db_score.id
    else:
        score_id = uuid.uuid4()

    return SuccessResponse(
        data=EvaluateData(
            score_id=score_id,
            session_id=body.session_id,
            question_id=body.question_id,
            answer_id=body.answer_id,
            scores=EvaluationScores(**evaluation_result["scores"]),
            feedback=EvaluationFeedback(**evaluation_result["feedback"]),
            follow_up=FollowUp(**evaluation_result["follow_up"]),
            latency=EvaluationLatency(evaluation_ms=evaluation_ms),
        ),
        message="Answer evaluated successfully",
    )


@router.post(
    "/final-report",
    response_model=SuccessResponse[ReportData],
    summary="Generate final interview scorecard",
)
async def generate_final_report(
    body: FinalReportRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))
    db_session = await session_service.get_session(db, str(body.session_id))
    if db_session and str(db_session.user_id) != user_id:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.SESSION_NOT_FOUND,
                    message="Session not found",
                )
            ).model_dump(),
        )

    if db_session:
        question_rows = await session_service.get_questions_for_session(db, str(body.session_id))
        score_result = await db.execute(
            select(ScoreModel)
            .where(ScoreModel.session_id == db_session.id)
            .order_by(ScoreModel.created_at)
        )
        score_rows = list(score_result.scalars().all())
        answer_result = await db.execute(
            select(AnswerModel)
            .where(AnswerModel.session_id == db_session.id)
            .order_by(AnswerModel.submitted_at)
        )
        answer_rows = list(answer_result.scalars().all())
        question_index = {str(q.id): q for q in question_rows}
        answer_index = {str(a.id): a for a in answer_rows}

        question_reviews = [
            QuestionReviewItem(
                question_id=str(score.question_id),
                sequence=question_index[str(score.question_id)].sequence
                if str(score.question_id) in question_index
                else idx + 1,
                question_text=question_index[str(score.question_id)].question_text
                if str(score.question_id) in question_index
                else f"Question {idx + 1}",
                answer_id=str(score.answer_id),
                overall_score=float(score.overall_score or 0.0),
                feedback_summary=score.feedback_text or "Good answer with solid coverage of the key concepts.",
            )
            for idx, score in enumerate(score_rows)
        ]

        transcript_items = (
            [
                TranscriptItem(
                    question=question_index[str(answer.question_id)].question_text
                    if str(answer.question_id) in question_index
                    else f"Question {idx + 1}",
                    answer=answer.transcript
                    or "Answer transcript unavailable in session history.",
                )
                for idx, answer in enumerate(answer_rows)
            ]
            if body.include_transcript
            else None
        )
        all_scores = [
            {
                "technical_correctness": score.technical_score,
                "clarity": score.clarity_score,
                "depth": score.depth_score,
                "confidence": score.confidence_score,
                "relevance": score.relevance_score,
                "structure": score.structure_score,
                "communication": score.communication_score,
                "conciseness": score.conciseness_score,
                "example_quality": score.example_quality_score,
                "overall": float(score.overall_score or 0.0),
            }
            for score in score_rows
        ]
    else:
        question_reviews = []
        transcript_items = None
        all_scores = []

    if settings.USE_MOCK_LLM:
        report_result = _mock_report()
        if not question_reviews:
            question_reviews = [
                QuestionReviewItem(
                    question_id=str(uuid.uuid4()),
                    sequence=i + 1,
                    question_text=f"Question {i + 1} from your interview session",
                    answer_id=str(uuid.uuid4()),
                    overall_score=round(6.5 + (i * 0.3), 1),
                    feedback_summary="Good answer with solid coverage of the key concepts.",
                )
                for i in range(5)
            ]
        if body.include_transcript and transcript_items is None:
            transcript_items = [
                TranscriptItem(
                    question=f"Question {i + 1}",
                    answer="Answer transcript will appear here in the real implementation.",
                )
                for i in range(5)
            ]
    else:
        try:
            report_result = await llm_service.generate_final_report(
                session_id=str(body.session_id),
                question_answer_reviews=[item.model_dump() for item in question_reviews],
                all_scores=all_scores,
                all_transcripts=[
                    item.model_dump() for item in transcript_items
                ]
                if transcript_items
                else [],
                candidate_profile=(
                    await _load_resume_profile(db, db_session.resume_id) if db_session else None
                ),
                job_analysis={
                    "job_description": db_session.job_description if db_session else None,
                    "target_role": db_session.target_role if db_session else None,
                    "target_company": db_session.target_company if db_session else None,
                },
                session_metadata={
                    "session_id": str(body.session_id),
                    "question_count": len(question_reviews),
                    "include_transcript": body.include_transcript,
                },
            )
        except LLMError as exc:
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.LLM_FAILED,
                        message=exc.message,
                    )
                ).model_dump(),
            )

    report_data = ReportData(
        report_id=uuid.uuid4(),
        session_id=body.session_id,
        status="completed",
        overall_score=report_result["overall_score"],
        score_breakdown=ScoreBreakdown(**report_result["score_breakdown"]),
        summary=report_result["summary"],
        strengths=report_result["strengths"],
        weaknesses=report_result["weaknesses"],
        recommended_topics=report_result["recommended_topics"],
        question_reviews=question_reviews,
        transcript=transcript_items,
        created_at=datetime.now(timezone.utc),
    )

    if db_session:
        db_report = await session_service.create_report(
            db,
            session_id=str(body.session_id),
            user_id=user_id,
            overall_score=report_data.overall_score,
            score_breakdown=report_data.score_breakdown.model_dump(),
            summary=report_data.summary,
            strengths=report_data.strengths,
            weaknesses=report_data.weaknesses,
            recommended_topics=report_data.recommended_topics,
            question_reviews=[r.model_dump() for r in report_data.question_reviews],
            transcript=[t.model_dump() for t in report_data.transcript]
            if report_data.transcript
            else None,
            prompt_version="final_report_v1.0",
        )
        report_data.report_id = db_report.id
        await session_service.complete_session(db, str(body.session_id))

    return SuccessResponse(
        data=report_data,
        message="Final report generated successfully",
    )


@router.get("/history", response_model=SuccessResponse[HistoryData])
async def get_history(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=SESSION_EXPIRY_MINUTES)
    await db.execute(
        sa_update(SessionModel)
        .where(
            SessionModel.user_id == UUID(user_id),
            SessionModel.status == "in_progress",
            SessionModel.last_activity_at < cutoff,
        )
        .values(status="expired")
    )
    await db.commit()

    sessions = await session_service.get_sessions_for_user(db, user_id, status=status)
    items = [
        HistoryItem(
            session_id=s.id,
            interview_type=s.interview_type,
            target_role=s.target_role,
            target_company=s.target_company,
            status=_status_value(s.status),
            question_count=s.current_sequence,
            overall_score=None,
            started_at=s.started_at,
            ended_at=s.ended_at,
        )
        for s in sessions
    ]
    paged_items = items[(page - 1) * limit : page * limit]
    total_items = len(items)
    total_pages = max(1, (total_items + limit - 1) // limit) if total_items else 1

    return SuccessResponse(
        data=HistoryData(
            items=paged_items,
            pagination=Pagination(
                page=page,
                limit=limit,
                total_items=total_items,
                total_pages=total_pages,
            ),
        ),
        message="History retrieved",
    )


@router.get("/{session_id}", response_model=SuccessResponse[SessionDetailData])
async def get_session(
    session_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))
    db_session = await session_service.get_session(db, str(session_id))
    if not db_session or str(db_session.user_id) != user_id:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.SESSION_NOT_FOUND,
                    message="Session not found",
                )
            ).model_dump(),
        )

    question_rows = await session_service.get_questions_for_session(db, str(session_id))
    answer_result = await db.execute(
        select(AnswerModel)
        .where(AnswerModel.session_id == db_session.id)
        .order_by(AnswerModel.submitted_at)
    )
    answer_rows = list(answer_result.scalars().all())
    score_result = await db.execute(
        select(ScoreModel)
        .where(ScoreModel.session_id == db_session.id)
        .order_by(ScoreModel.created_at)
    )
    score_rows = list(score_result.scalars().all())
    report_result = await db.execute(
        select(ReportModel).where(ReportModel.session_id == db_session.id)
    )
    report_row = report_result.scalar_one_or_none()

    question_by_id = {str(row.id): row for row in question_rows}
    answer_by_question_id = {str(row.question_id): row for row in answer_rows}
    score_by_answer_id = {str(row.answer_id): row for row in score_rows}

    latest_question = question_rows[-1] if question_rows else None
    latest_answer = (
        answer_by_question_id.get(str(latest_question.id)) if latest_question else None
    )
    latest_score = (
        score_by_answer_id.get(str(latest_answer.id))
        if latest_answer is not None
        else None
    )

    current_question = None
    current_transcript = None
    current_evaluation = None

    if latest_question is not None:
        current_question = QuestionDetail(
            question_id=latest_question.id,
            sequence=latest_question.sequence,
            type=latest_question.question_type,
            difficulty=db_session.difficulty,
            question_text=latest_question.question_text,
            expected_focus_areas=list(latest_question.expected_focus_areas or []),
            time_limit_seconds=settings.FREE_MAX_AUDIO_SECONDS,
            audio=AudioData(
                enabled=bool(latest_question.audio_url),
                audio_url=latest_question.audio_url,
                duration_seconds=None,
                cached=False,
            ),
        )

    if latest_answer is not None:
        cached = speech_service.get_cached_transcription(str(latest_answer.id))
        filler_count = latest_answer.filler_word_count or 0
        current_transcript = TranscribeData(
            answer_id=latest_answer.id,
            session_id=db_session.id,
            question_id=latest_answer.question_id,
            transcript=latest_answer.transcript or "",
            language=(cached or {}).get("language", "en"),
            duration_seconds=latest_answer.duration_seconds or 0,
            word_count=latest_answer.word_count or 0,
            filler_words={
                "count": filler_count,
                "examples": ((cached or {}).get("filler_words", {}) or {}).get("examples", []),
            },
            raw_audio_deleted=latest_answer.raw_audio_deleted,
            submitted_at=latest_answer.submitted_at,
            latency={"transcription_ms": (cached or {}).get("latency", {}).get("transcription_ms", 0)},
        )

    if latest_score is not None and latest_answer is not None:
        current_evaluation = _score_to_evaluation_payload(
            latest_score,
            db_session.id,
            latest_question.id,
            latest_answer.id,
        )

    completed_answers: list[CompletedAnswerData] = []
    for question_row in question_rows[:-1] if latest_question is not None else question_rows:
        answer_row = answer_by_question_id.get(str(question_row.id))
        if answer_row is None:
            continue
        score_row = score_by_answer_id.get(str(answer_row.id))
        if score_row is None:
            continue
        evaluation_payload = _score_to_evaluation_payload(
            score_row,
            db_session.id,
            question_row.id,
            answer_row.id,
        )
        completed_answers.append(
            CompletedAnswerData(
                questionNumber=question_row.sequence,
                questionId=str(question_row.id),
                questionText=question_row.question_text,
                questionType=question_row.question_type,
                answerId=str(answer_row.id),
                transcript=answer_row.transcript or "",
                wordCount=answer_row.word_count or 0,
                scores=evaluation_payload.scores.model_dump(),
                overallScore=evaluation_payload.scores.overall,
                feedbackSummary=evaluation_payload.feedback.summary,
                strengths=evaluation_payload.feedback.strengths,
                improvements=evaluation_payload.feedback.improvements,
            )
        )

    final_report = None
    if report_row is not None:
        final_report = ReportData(
            report_id=report_row.id,
            session_id=report_row.session_id,
            status="completed",
            overall_score=float(report_row.overall_score),
            score_breakdown=ScoreBreakdown(**(report_row.score_breakdown or {})),
            summary=report_row.summary,
            strengths=list(report_row.strengths or []),
            weaknesses=list(report_row.weaknesses or []),
            recommended_topics=list(report_row.recommended_topics or []),
            question_reviews=[
                QuestionReviewItem(**item)
                for item in list(report_row.question_reviews or [])
            ],
            transcript=(
                [TranscriptItem(**item) for item in list(report_row.transcript or [])]
                if report_row.transcript
                else None
            ),
            created_at=report_row.created_at,
        )

    resume_profile = await _load_resume_profile(db, db_session.resume_id)

    return SuccessResponse(
        data=SessionDetailData(
            session_id=db_session.id,
            resume_id=db_session.resume_id,
            interview_type=db_session.interview_type,
            difficulty=db_session.difficulty,
            target_role=db_session.target_role,
            target_company=db_session.target_company,
            job_description=db_session.job_description,
            question_count=db_session.question_count,
            voice_enabled=db_session.voice_enabled,
            status=_status_value(db_session.status),
            started_at=db_session.started_at,
            expires_at=db_session.expires_at,
            questions_answered=len(answer_rows),
            current_sequence=db_session.current_sequence,
            last_activity_at=db_session.last_activity_at,
            resume_profile=CandidateProfile(**resume_profile) if resume_profile else None,
            current_question=current_question,
            current_transcript=current_transcript,
            current_evaluation=current_evaluation,
            completed_answers=completed_answers,
            final_report=final_report,
        ),
        message="Session retrieved",
    )


@router.get("/{session_id}/scorecard", response_model=SuccessResponse[ScorecardData])
async def get_scorecard(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()


@router.post("/{session_id}/complete", response_model=SuccessResponse[dict])
async def complete_session(
    session_id: UUID,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))
    db_session = await session_service.get_session(db, str(session_id))
    if not db_session or str(db_session.user_id) != user_id:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.SESSION_NOT_FOUND,
                    message="Session not found",
                )
            ).model_dump(),
        )

    await session_service.complete_session(db, str(session_id))
    return SuccessResponse(data={"completed": True}, message="Session completed")


@router.delete("/{session_id}", response_model=SuccessResponse[dict])
async def delete_session(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()
