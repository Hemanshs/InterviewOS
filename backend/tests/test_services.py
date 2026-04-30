import pytest

from app.schemas.audio import TranscribeData
from app.schemas.evaluation import EvaluateData, ReportData
from app.schemas.interview import QuestionData
from app.schemas.resume import CandidateProfile
from app.schemas.usage import UsageData
from app.services.evaluation_service import EvaluationService
from app.services.llm_service import LLMService
from app.services.resume_parser import ResumeParserService
from app.services.speech_service import SpeechService
from app.services.usage_service import UsageService
from app.services.voice_service import VoiceService


@pytest.mark.asyncio
async def test_resume_parser_mock_pdf_text_is_non_empty():
    service = ResumeParserService()
    assert service._mock_pdf_text().strip()


@pytest.mark.asyncio
async def test_resume_parser_mock_profile_has_candidate_name():
    service = ResumeParserService()
    data = service._mock_parsed_profile()
    assert data["candidate_name"]


@pytest.mark.asyncio
async def test_llm_mock_question_contains_question_text():
    service = LLMService()
    data = service._mock_question(sequence=1)
    assert "question_text" in data


@pytest.mark.asyncio
async def test_llm_mock_question_changes_with_sequence():
    service = LLMService()
    first = service._mock_question(sequence=1)
    third = service._mock_question(sequence=3)
    assert first["question_text"] != third["question_text"]


@pytest.mark.asyncio
async def test_speech_mock_transcription_has_transcript_and_word_count():
    service = SpeechService()
    data = service._mock_transcription()
    assert data["transcript"]
    assert data["word_count"] > 0


@pytest.mark.asyncio
async def test_voice_mock_audio_url_uses_https():
    service = VoiceService()
    url = service._mock_audio_url("test")
    assert url.startswith("https://")


@pytest.mark.asyncio
async def test_evaluation_mock_has_all_score_fields():
    service = EvaluationService()
    data = service._mock_evaluation()
    score_keys = [
        "technical_score",
        "clarity_score",
        "depth_score",
        "confidence_score",
        "relevance_score",
        "structure_score",
        "communication_score",
        "conciseness_score",
        "example_quality_score",
    ]
    assert all(key in data for key in score_keys)


@pytest.mark.asyncio
async def test_evaluation_mock_scores_are_between_zero_and_ten():
    service = EvaluationService()
    data = service._mock_evaluation()
    score_values = [
        data["technical_score"],
        data["clarity_score"],
        data["depth_score"],
        data["confidence_score"],
        data["relevance_score"],
        data["structure_score"],
        data["communication_score"],
        data["conciseness_score"],
        data["example_quality_score"],
    ]
    assert all(0 <= value <= 10 for value in score_values)


@pytest.mark.asyncio
async def test_usage_mock_plan_is_free():
    service = UsageService()
    data = service._mock_usage_status()
    assert data["plan"] == "free"


@pytest.mark.asyncio
async def test_usage_check_can_start_interview_returns_true_in_mock_mode():
    service = UsageService()
    assert await service.check_can_start_interview(user_id="user-1", db=None) is True


@pytest.mark.asyncio
async def test_mock_shapes_match_pydantic_schemas():
    resume_service = ResumeParserService()
    llm_service = LLMService()
    speech_service = SpeechService()
    evaluation_service = EvaluationService()
    usage_service = UsageService()

    CandidateProfile(**resume_service._mock_parsed_profile())
    QuestionData(
        question_id="00000000-0000-0000-0000-000000000001",
        session_id="00000000-0000-0000-0000-000000000002",
        sequence=1,
        voice_enabled=True,
        latency_state=None,
        **llm_service._mock_question(sequence=1),
    )
    TranscribeData(
        answer_id="00000000-0000-0000-0000-000000000003",
        session_id="00000000-0000-0000-0000-000000000002",
        question_id="00000000-0000-0000-0000-000000000001",
        raw_audio_deleted=True,
        **speech_service._mock_transcription(),
    )
    EvaluateData(
        score_id="00000000-0000-0000-0000-000000000004",
        session_id="00000000-0000-0000-0000-000000000002",
        question_id="00000000-0000-0000-0000-000000000001",
        answer_id="00000000-0000-0000-0000-000000000003",
        scores={
            "technical_score": evaluation_service._mock_evaluation()["technical_score"],
            "clarity_score": evaluation_service._mock_evaluation()["clarity_score"],
            "depth_score": evaluation_service._mock_evaluation()["depth_score"],
            "confidence_score": evaluation_service._mock_evaluation()["confidence_score"],
            "relevance_score": evaluation_service._mock_evaluation()["relevance_score"],
            "structure_score": evaluation_service._mock_evaluation()["structure_score"],
            "communication_score": evaluation_service._mock_evaluation()["communication_score"],
            "conciseness_score": evaluation_service._mock_evaluation()["conciseness_score"],
            "example_quality_score": evaluation_service._mock_evaluation()["example_quality_score"],
            "overall_score": evaluation_service._mock_evaluation()["overall_score"],
        },
        feedback_text=evaluation_service._mock_evaluation()["feedback_text"],
        strengths=evaluation_service._mock_evaluation()["strengths"],
        improvements=evaluation_service._mock_evaluation()["improvements"],
        follow_up_question=evaluation_service._mock_evaluation()["follow_up_question"],
    )
    ReportData(
        report_id="00000000-0000-0000-0000-000000000005",
        session_id="00000000-0000-0000-0000-000000000002",
        created_at="2026-04-30T12:00:00+00:00",
        **evaluation_service._mock_final_report(),
    )
    UsageData(**usage_service._mock_usage_status())
