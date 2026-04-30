from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.security import get_current_user
from app.schemas import SuccessResponse, TranscribeData, not_implemented

router = APIRouter(prefix="/audio", tags=["Audio"])


# TODO: Implement POST /api/audio/transcribe
@router.post("/transcribe", response_model=SuccessResponse[TranscribeData])
async def transcribe_audio(
    file: UploadFile = File(...),
    session_id: UUID = Form(...),
    question_id: UUID = Form(...),
    current_user=Depends(get_current_user),
):
    return not_implemented()
