import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import ValidationError

from app.core.security import get_current_user
from app.main import app
from app.schemas import (
    DeleteAccountRequest,
    EvaluateAnswerRequest,
    ScoreDetail,
    StartInterviewRequest,
    SuccessResponse,
    UserData,
    UserUsageData,
)


def test_start_interview_request_accepts_valid_data():
    resume_id = uuid.uuid4()
    payload = StartInterviewRequest(
        resume_id=resume_id,
        interview_type="backend",
        difficulty="medium",
        job_description="Build APIs",
        target_company="Acme",
        target_role="Backend Engineer",
        question_count=5,
        voice_enabled=True,
    )

    assert payload.resume_id == resume_id
    assert payload.interview_type == "backend"
    assert payload.question_count == 5
    assert payload.voice_enabled is True


def test_start_interview_request_rejects_question_count_above_five():
    with pytest.raises(ValidationError):
        StartInterviewRequest(
            interview_type="backend",
            question_count=10,
        )


def test_evaluate_answer_request_rejects_invalid_uuid():
    with pytest.raises(ValidationError):
        EvaluateAnswerRequest(
            session_id="not-a-uuid",
            question_id=uuid.uuid4(),
            answer_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_delete_account_wrong_confirmation_returns_422():
    stable_user_id = str(uuid.uuid4())
    app.dependency_overrides[get_current_user] = lambda: stable_user_id
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.request(
            "DELETE",
            "/api/account",
            json={"confirmation": "wrong"},
        )

    app.dependency_overrides.clear()

    assert response.status_code == 422


def test_score_detail_accepts_all_score_fields():
    model = ScoreDetail(
        technical_score=8,
        clarity_score=7,
        depth_score=9,
        confidence_score=6,
        relevance_score=8,
        structure_score=7,
        communication_score=8,
        conciseness_score=6,
        example_quality_score=9,
        overall_score=7.8,
    )

    assert model.technical_score == 8
    assert model.example_quality_score == 9
    assert model.overall_score == 7.8


def test_success_response_wraps_user_data():
    user_data = UserData(
        id=uuid.uuid4(),
        email="candidate@example.com",
        plan="free",
        created_at=datetime.now(timezone.utc),
        usage=UserUsageData(
            free_interview_used=False,
            remaining_free_interviews=1,
        ),
    )

    response = SuccessResponse[UserData](data=user_data)

    assert response.success is True
    assert response.data.email == "candidate@example.com"
    assert response.message == "Request completed successfully"
