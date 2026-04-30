from fastapi import APIRouter, Depends

from app.core.security import get_current_user
from app.schemas import SuccessResponse, not_implemented

router = APIRouter(prefix="/feedback", tags=["Evaluation"])


# TODO: Implement future feedback endpoints
@router.get("/placeholder", response_model=SuccessResponse[dict], tags=["Feedback"])
async def feedback_placeholder(current_user=Depends(get_current_user)):
    return not_implemented()
