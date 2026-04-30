from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.schemas import (
    EvaluateAnswerRequest,
    EvaluateData,
    FinalReportRequest,
    GenerateQuestionRequest,
    HistoryData,
    QuestionData,
    ReportData,
    ScorecardData,
    SessionData,
    SessionDetailData,
    StartInterviewRequest,
    SuccessResponse,
    not_implemented,
)

router = APIRouter(prefix="/interview", tags=["Interviews"])


# TODO: Implement POST /api/interview/start, POST /api/interview/question, POST /api/interview/evaluate, POST /api/interview/final-report, GET /api/interview/history, GET /api/interview/{session_id}, GET /api/interview/{session_id}/scorecard, POST /api/interview/{session_id}/complete, DELETE /api/interview/{session_id}
@router.post("/start", response_model=SuccessResponse[SessionData])
async def start_interview(
    body: Optional[StartInterviewRequest] = None,
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.post("/question", response_model=SuccessResponse[QuestionData])
async def generate_question(
    body: Optional[GenerateQuestionRequest] = None,
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.post("/evaluate", response_model=SuccessResponse[EvaluateData])
async def evaluate_answer(
    body: Optional[EvaluateAnswerRequest] = None,
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.post("/final-report", response_model=SuccessResponse[ReportData])
async def generate_final_report(
    body: Optional[FinalReportRequest] = None,
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.get("/history", response_model=SuccessResponse[HistoryData])
async def get_history(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    status: Optional[str] = Query(default=None),
    interview_type: Optional[str] = Query(default=None),
    current_user=Depends(get_current_user),
):
    return not_implemented()


@router.get("/{session_id}", response_model=SuccessResponse[SessionDetailData])
async def get_session(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()


@router.get("/{session_id}/scorecard", response_model=SuccessResponse[ScorecardData])
async def get_scorecard(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()


@router.post("/{session_id}/complete", response_model=SuccessResponse[dict])
async def complete_session(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()


@router.delete("/{session_id}", response_model=SuccessResponse[dict])
async def delete_session(session_id: UUID, current_user=Depends(get_current_user)):
    return not_implemented()
