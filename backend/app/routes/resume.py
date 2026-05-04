import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ResumeParseError
from app.core.security import get_current_user
from app.db.database import get_async_session, get_or_create_user
from app.models.resume import Resume as ResumeModel
from app.models.user import User as UserModel
from app.schemas.common import ErrorCode, ErrorDetail, ErrorResponse, SuccessResponse
from app.schemas.resume import CandidateProfile, ResumeLatestData, ResumeUploadData
from app.services.resume_parser import ResumeParserService

router = APIRouter(prefix="/resume", tags=["Resumes"])
resume_parser = ResumeParserService()
_resume_store: dict[str, dict] = {}


@router.post(
    "/upload",
    response_model=SuccessResponse[ResumeUploadData],
    summary="Upload and parse resume PDF",
)
async def upload_resume(
    file: UploadFile = File(...),
    replace_existing: bool = Form(default=False),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    allowed_types = {"application/pdf", "application/x-pdf"}
    content_type = (file.content_type or "").lower()
    filename = file.filename or "resume.pdf"
    if content_type not in allowed_types and not filename.lower().endswith(".pdf"):
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.UNSUPPORTED_FILE_TYPE,
                    message="Only PDF files are accepted",
                    details={"received_type": content_type},
                )
            ).model_dump(),
        )

    file_bytes = await file.read()
    max_size = settings.FREE_MAX_RESUME_MB * 1024 * 1024
    if len(file_bytes) > max_size:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.FILE_TOO_LARGE,
                    message=f"Resume must be under {settings.FREE_MAX_RESUME_MB}MB",
                    details={"max_size_mb": settings.FREE_MAX_RESUME_MB},
                )
            ).model_dump(),
        )

    try:
        resume_text = await resume_parser.extract_text_from_pdf(file_bytes)
    except ResumeParseError as exc:
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message=str(exc.message),
                )
            ).model_dump(),
        )

    parse_error: str | None = None
    try:
        parsed_dict = await resume_parser.parse_resume_with_llm(resume_text)
        profile = CandidateProfile(**parsed_dict)
        parsed = True
    except Exception as exc:
        profile = None
        parsed = False
        parse_error = str(exc)

    user_id = await get_or_create_user(db, str(current_user))
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == uuid.UUID(str(current_user)))
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

    if str(getattr(user.plan, "value", user.plan)) == "free":
        count_result = await db.execute(
            select(func.count())
            .select_from(ResumeModel)
            .where(
                ResumeModel.user_id == uuid.UUID(str(current_user)),
                ResumeModel.deleted_at.is_(None),
            )
        )
        existing_count = int(count_result.scalar() or 0)
        if existing_count >= 1 and not replace_existing:
            return JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error=ErrorDetail(
                        code=ErrorCode.RATE_LIMIT_EXCEEDED,
                        message="Free plan allows 1 resume. Delete existing or set replace_existing=true.",
                    )
                ).model_dump(),
            )
        if existing_count >= 1 and replace_existing:
            existing_result = await db.execute(
                select(ResumeModel).where(
                    ResumeModel.user_id == uuid.UUID(str(current_user)),
                    ResumeModel.deleted_at.is_(None),
                )
            )
            for existing_resume in list(existing_result.scalars().all()):
                existing_resume.deleted_at = datetime.now(timezone.utc)
            await db.commit()

    resume_id = uuid.uuid4()
    created_at = datetime.now(timezone.utc)
    user_key = str(user_id)
    db_resume = ResumeModel(
        id=resume_id,
        user_id=uuid.UUID(str(user_id)),
        file_name=filename,
        file_url=f"/resumes/{resume_id}.pdf",
        parsed_profile=profile.model_dump() if profile else None,
        created_at=created_at,
    )
    db.add(db_resume)
    await db.commit()
    await db.refresh(db_resume)
    record = {
        "resume_id": str(resume_id),
        "file_name": filename,
        "file_url": f"/resumes/{resume_id}.pdf",
        "profile": profile.model_dump() if profile else None,
        "parsed": parsed,
        "created_at": created_at.isoformat(),
    }
    _resume_store[user_key] = record
    _resume_store[str(resume_id)] = record

    headers = {
        "X-RateLimit-Limit": "1",
        "X-RateLimit-Remaining": "0" if user.free_interview_used else "1",
    }

    return JSONResponse(
        status_code=200,
        headers=headers,
        content=SuccessResponse(
            data=ResumeUploadData(
                resume_id=resume_id,
                file_name=filename,
                file_url=f"/resumes/{resume_id}.pdf",
                parsed=parsed,
                profile=profile,
                created_at=created_at,
            ),
            message=(
                "Resume uploaded and parsed successfully"
                if parsed
                else f"Resume uploaded (parsing failed): {parse_error or 'Unknown parsing error'}"
            ),
        ).model_dump(mode="json"),
    )


@router.get("/latest", response_model=SuccessResponse[ResumeLatestData])
async def get_latest_resume(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await get_or_create_user(db, str(current_user))
    result = await db.execute(
        select(ResumeModel)
        .where(ResumeModel.user_id == uuid.UUID(str(user_id)))
        .where(ResumeModel.deleted_at.is_(None))
        .order_by(ResumeModel.created_at.desc())
        .limit(1)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="No resume found for this user",
                )
            ).model_dump(),
        )

    record = {
        "resume_id": str(resume.id),
        "file_name": resume.file_name,
        "profile": resume.parsed_profile,
        "created_at": resume.created_at.isoformat(),
    }
    _resume_store[str(user_id)] = {
        **record,
        "file_url": resume.file_url,
        "parsed": bool(resume.parsed_profile),
    }
    _resume_store[str(resume.id)] = _resume_store[str(user_id)]

    profile = CandidateProfile(**record["profile"]) if record.get("profile") else None
    return SuccessResponse(
        data=ResumeLatestData(
            resume_id=uuid.UUID(record["resume_id"]),
            file_name=record["file_name"],
            profile=profile,
            created_at=datetime.fromisoformat(record["created_at"]),
        ),
        message="Resume retrieved",
    )


def get_resume_profile_for_user(user_id: str) -> dict | None:
    record = _resume_store.get(str(user_id))
    return record.get("profile") if record else None


def get_resume_profile_by_id(resume_id: str) -> dict | None:
    record = _resume_store.get(str(resume_id))
    return record.get("profile") if record else None
