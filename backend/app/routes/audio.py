import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import TranscriptionError
from app.core.security import get_current_user
from app.db.database import get_async_session, get_or_create_dev_user
from app.schemas.audio import TranscribeData
from app.schemas.common import ErrorCode, ErrorDetail, ErrorResponse, SuccessResponse
from app.services.session_service import SessionService
from app.services.speech_service import SpeechService
from app.utils.audio_utils import (
    validate_audio_duration,
    validate_audio_mime_type,
    validate_audio_size,
)

router = APIRouter(prefix="/audio", tags=["Audio"])
speech_service = SpeechService()
session_service = SessionService()


@router.post(
    "/transcribe",
    response_model=SuccessResponse[TranscribeData],
    summary="Transcribe candidate answer audio",
    description="Upload recorded answer audio and receive transcript with word count and filler word detection.",
)
async def transcribe_audio(
    session_id: str = Form(..., description="Active interview session ID"),
    question_id: str = Form(..., description="Question being answered"),
    duration_seconds: float = Form(..., description="Audio duration in seconds"),
    language: str = Form(default="en", description="Language code, default en"),
    audio_file: UploadFile = File(..., description="Recorded audio blob (webm, mp3, wav)"),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    try:
        validate_audio_mime_type(audio_file.content_type)

        audio_bytes = await audio_file.read()
        validate_audio_size(len(audio_bytes))
        validate_audio_duration(duration_seconds, max_seconds=60)

        try:
            uuid.UUID(str(session_id))
            uuid.UUID(str(question_id))
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": ErrorCode.VALIDATION_ERROR,
                        "message": "session_id and question_id must be valid UUIDs",
                        "details": {},
                    },
                },
            ) from exc
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)

    try:
        result = await speech_service.transcribe_audio(
            audio_bytes=audio_bytes,
            session_id=session_id,
            question_id=question_id,
            language=language,
            duration_seconds=int(duration_seconds),
            content_type=audio_file.content_type or "",
        )
    except TranscriptionError as exc:
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.TRANSCRIPTION_FAILED,
                    message=exc.message,
                )
            ).model_dump(),
        )
    speech_service.cache_transcription(result)

    user_id = await get_or_create_dev_user(db)
    try:
        db_answer = await session_service.create_answer(
            db,
            session_id=session_id,
            question_id=question_id,
            transcript=result["transcript"],
            duration_seconds=result.get("duration_seconds", 0),
            word_count=result.get("word_count", 0),
            filler_word_count=result.get("filler_words", {}).get("count", 0),
        )
        result["answer_id"] = db_answer.id
        speech_service.cache_transcription(result)
    except Exception:
        pass

    return SuccessResponse(
        data=TranscribeData(**result),
        message="Audio transcribed successfully",
    )
