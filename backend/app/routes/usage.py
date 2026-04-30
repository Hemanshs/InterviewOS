from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas import SuccessResponse, UsageData, not_implemented
from app.services.usage_service import UsageService

router = APIRouter(prefix="", tags=["Users"])
usage_service = UsageService()


# TODO: Implement GET /api/usage
@router.get("/usage", response_model=SuccessResponse[UsageData], tags=["Users"])
async def get_usage(current_user=Depends(get_current_user)):
    data = await usage_service.get_usage_status(user_id=current_user, db=None)
    return SuccessResponse(data=UsageData(**data), message="Usage status retrieved")
