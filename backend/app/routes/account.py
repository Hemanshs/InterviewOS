from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import bearer_scheme, get_current_user, get_user_email_from_token
from app.db.database import get_async_session, get_or_create_user
from app.models.answer import Answer as AnswerModel
from app.models.question import Question as QuestionModel
from app.models.report import Report as ReportModel
from app.models.resume import Resume as ResumeModel
from app.models.score import Score as ScoreModel
from app.models.session import Session as SessionModel
from app.models.usage_event import UsageEvent as UsageEventModel
from app.models.user import User as UserModel
from app.schemas import (
    DeleteAccountData,
    DeleteAccountRequest,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    UserData,
)

router = APIRouter(prefix="", tags=["account"])


@router.get("/me", response_model=SuccessResponse[UserData], tags=["Users"])
async def get_me(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    email = None
    if credentials and credentials.credentials:
        email = get_user_email_from_token(credentials.credentials)

    await get_or_create_user(db, current_user, email)
    result = await db.execute(
        select(UserModel).where(UserModel.id == UUID(str(current_user)))
    )
    user = result.scalar_one_or_none()

    return SuccessResponse(
        data=UserData(
            id=user.id,
            email=user.email,
            plan=user.plan,
            created_at=user.created_at,
            usage={
                "free_interview_used": user.free_interview_used,
                "free_interviews_total": 1,
                "remaining_free_interviews": 0 if user.free_interview_used else 1,
            },
        ),
        message="User profile retrieved",
    )


@router.delete("/account", response_model=SuccessResponse[DeleteAccountData], tags=["Users"])
async def delete_account(
    body: DeleteAccountRequest,
    current_user: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    if body.confirmation != "DELETE_MY_ACCOUNT":
        raise HTTPException(
            status_code=422,
            detail=ErrorResponse(
                error=ErrorDetail(
                    code=ErrorCode.VALIDATION_ERROR,
                    message="Account deletion requires confirmation text",
                    details={"required_confirmation": "DELETE_MY_ACCOUNT"},
                )
            ).model_dump(),
        )

    uid = UUID(str(current_user))
    await get_or_create_user(db, str(current_user))
    deleted_at = datetime.now(timezone.utc)
    session_ids = list(
        (
            await db.execute(select(SessionModel.id).where(SessionModel.user_id == uid))
        ).scalars().all()
    )

    if session_ids:
        await db.execute(delete(ScoreModel).where(ScoreModel.session_id.in_(session_ids)))
        await db.execute(delete(AnswerModel).where(AnswerModel.session_id.in_(session_ids)))
        await db.execute(delete(QuestionModel).where(QuestionModel.session_id.in_(session_ids)))

    await db.execute(delete(ReportModel).where(ReportModel.user_id == uid))
    await db.execute(delete(SessionModel).where(SessionModel.user_id == uid))
    await db.execute(delete(ResumeModel).where(ResumeModel.user_id == uid))
    await db.execute(delete(UsageEventModel).where(UsageEventModel.user_id == uid))

    user = (
        await db.execute(select(UserModel).where(UserModel.id == uid))
    ).scalar_one_or_none()
    if user is not None:
        user.deleted_at = deleted_at

    await db.commit()

    return SuccessResponse(
        data=DeleteAccountData(
            user_id=uid,
            deleted=True,
            deleted_at=deleted_at,
        ),
        message="Account deleted successfully",
    )
