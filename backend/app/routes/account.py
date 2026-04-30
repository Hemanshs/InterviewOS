from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user
from app.schemas import (
    DeleteAccountData,
    DeleteAccountRequest,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    SuccessResponse,
    UserData,
    not_implemented,
)

router = APIRouter(prefix="", tags=["account"])


@router.get("/me", response_model=SuccessResponse[UserData], tags=["Users"])
async def get_me(current_user=Depends(get_current_user)):
    # Mock response until real account lookup is wired to the database.
    user_id = current_user if isinstance(current_user, UUID) else UUID(str(current_user))
    return SuccessResponse(
        data=UserData(
            id=user_id,
            email="candidate@example.com",
            plan="free",
            created_at=datetime.now(timezone.utc),
            usage={
                "free_interview_used": False,
                "free_interviews_total": 1,
                "remaining_free_interviews": 1,
            },
        ),
        message="User profile retrieved",
    )


@router.delete("/account", response_model=SuccessResponse[DeleteAccountData], tags=["Users"])
async def delete_account(body: DeleteAccountRequest, current_user=Depends(get_current_user)):
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
    return not_implemented()
