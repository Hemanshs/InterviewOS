from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.security import get_current_user
from typing import Annotated

from app.schemas import ResumeLatestData, ResumeUploadData, SuccessResponse, not_implemented

router = APIRouter(prefix="/resume", tags=["Resumes"])


# TODO: Implement POST /api/resume/upload, GET /api/resume/latest, DELETE /api/resume/{resume_id}
@router.post("/upload", response_model=SuccessResponse[ResumeUploadData], tags=["Resumes"])
async def upload_resume(
    file: UploadFile = File(...),
    parse_with_llm: bool = Form(default=True),
    replace_existing: bool = Form(default=False),
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.get("/latest", response_model=SuccessResponse[ResumeLatestData], tags=["Resumes"])
async def get_latest_resume(current_user=Depends(get_current_user)):
    return not_implemented()


@router.delete("/{resume_id}", response_model=SuccessResponse[dict], tags=["Resumes"])
async def delete_resume(resume_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()
