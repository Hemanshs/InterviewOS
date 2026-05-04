import pytest

from app.core.config import settings
from app.core.exceptions import LLMError
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


def test_llm_extracts_json_from_markdown_fence():
    service = LLMService()
    extracted = service._extract_json_object_text(
        """```json
{"question_text":"Test question","question_type":"technical"}
```"""
    )
    assert extracted == '{"question_text":"Test question","question_type":"technical"}'


def test_llm_extracts_json_from_wrapped_text():
    service = LLMService()
    extracted = service._extract_json_object_text(
        'Here is the JSON response:\n{"question_text":"Test question","question_type":"technical"}\nThanks.'
    )
    assert extracted == '{"question_text":"Test question","question_type":"technical"}'


@pytest.mark.asyncio
async def test_llm_question_generation_falls_back_to_plain_text(monkeypatch):
    service = LLMService()
    monkeypatch.setattr(settings, "USE_MOCK_LLM", False)

    async def fake_generate_json(**kwargs):
        raise LLMError("Gemini returned invalid JSON for question generation")

    async def fake_generate_text(**kwargs):
        return "How would you debug a flaky CI pipeline in production?"

    monkeypatch.setattr(service, "_generate_gemini_json", fake_generate_json)
    monkeypatch.setattr(service, "_generate_gemini_text", fake_generate_text)

    result = await service.generate_question(
        mode="first",
        sequence=1,
        interview_type="sde",
        difficulty="medium",
        question_count=5,
    )

    assert result["question_text"] == "How would you debug a flaky CI pipeline in production?"
    assert result["question_type"] == "technical"
    assert result["difficulty"] == "medium"


def test_llm_question_text_coercion_extracts_json_payload():
    service = LLMService()
    result = service._coerce_question_result_from_text(
        """```json
{
  "question_text": "How would you design a scalable audit logging system?",
  "question_type": "system_design",
  "difficulty": "hard",
  "expected_focus_areas": ["scalability", "storage", "reliability"],
  "time_limit_seconds": 90
}
```""",
        difficulty="medium",
        mode="first",
    )
    assert result["question_text"] == "How would you design a scalable audit logging system?"
    assert result["question_type"] == "system_design"
    assert result["difficulty"] == "hard"
    assert result["expected_focus_areas"] == ["scalability", "storage", "reliability"]
    assert result["time_limit_seconds"] == settings.FREE_MAX_AUDIO_SECONDS


def test_llm_question_text_coercion_extracts_question_text_from_partial_json():
    service = LLMService()
    result = service._coerce_question_result_from_text(
        """```json
{
  "question_text": "Design a RESTful API for a simple project management system.",
  "question_type": "API Design / Backend System Design",
  "difficulty": "medium",
""",
        difficulty="medium",
        mode="first",
    )
    assert result["question_text"] == "Design a RESTful API for a simple project management system."
    assert result["question_type"] == "system_design"
    assert result["difficulty"] == "medium"


def test_llm_question_text_coercion_extracts_from_full_gemini_rest_payload():
    service = LLMService()
    result = service._coerce_question_result_from_text(
        """{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```json\\n{\\n  \\"question_text\\": \\"Design the backend API and core service logic for a feature that allows users to like a piece of content on a social platform.\\",\\n  \\"question_type\\": \\"Backend System Design\\",\\n  \\"difficulty\\": \\"medium\\",\\n  \\"expected_focus_areas\\": [\\n    \\"RESTful API design principles\\",\\n    \\"Database schema design\\"\\n  ],\\n  \\"time_limit_seconds\\": 2400\\n}\\n```"
          }
        ],
        "role": "model"
      }
    }
  ]
}""",
        difficulty="medium",
        mode="first",
    )
    assert result["question_text"] == (
        "Design the backend API and core service logic for a feature that allows users "
        "to like a piece of content on a social platform."
    )
    assert result["question_type"] == "system_design"
    assert result["difficulty"] == "medium"
    assert result["time_limit_seconds"] == settings.FREE_MAX_AUDIO_SECONDS


def test_llm_question_text_coercion_unwraps_nested_question_text_payload():
    service = LLMService()
    result = service._coerce_question_result(
        {
            "question_text": """```json
{
  "question_text": "How would you handle retries and dead-letter queues in a distributed worker system?",
  "question_type": "system_design",
  "difficulty": "hard",
  "expected_focus_areas": ["retries", "dead letters", "idempotency"],
  "time_limit_seconds": 75
}
```""",
            "question_type": "technical",
            "difficulty": "medium",
        },
        difficulty="medium",
        mode="first",
    )
    assert result["question_text"] == "How would you handle retries and dead-letter queues in a distributed worker system?"
    assert result["question_type"] == "system_design"
    assert result["difficulty"] == "hard"


def test_llm_question_result_normalizes_type_and_time_limit():
    service = LLMService()
    result = service._coerce_question_result(
        {
            "question_text": "Design a RESTful API for a project management system.",
            "question_type": "API Design / Backend System Design",
            "difficulty": "medium",
            "expected_focus_areas": ["REST", "auth"],
            "time_limit_seconds": 900,
        },
        difficulty="medium",
        mode="first",
    )
    assert result["question_type"] == "system_design"
    assert result["time_limit_seconds"] == settings.FREE_MAX_AUDIO_SECONDS


def test_llm_question_result_accepts_no_resume_first_question_suggestion():
    service = LLMService()
    result = service._coerce_question_result(
        {
            "context_mode": "no_resume",
            "safe_assumptions": [],
            "missing_context": [],
            "recommended_question_strategy": ["role-based"],
            "first_question_suggestion": {
                "question_text": "Based on this backend engineer role, how would you design an API for a high-volume write path?",
                "question_type": "system_design",
                "difficulty": "medium",
                "expected_focus_areas": ["API design", "scalability"],
                "time_limit_seconds": 90,
            },
        },
        difficulty="medium",
        mode="first",
    )
    assert result["question_text"] == "Based on this backend engineer role, how would you design an API for a high-volume write path?"
    assert result["question_type"] == "system_design"
    assert result["difficulty"] == "medium"
    assert result["expected_focus_areas"] == ["API design", "scalability"]
    assert result["time_limit_seconds"] == settings.FREE_MAX_AUDIO_SECONDS


def test_llm_evaluation_result_coerces_nested_jsonish_fields():
    service = LLMService()
    result = service._coerce_evaluation_result(
        {
            "scores": """```json
{
  "technical_correctness": 8,
  "clarity": 7,
  "depth": 9,
  "confidence": 6,
  "relevance": 8,
  "structure": 7,
  "communication": 7,
  "conciseness": 6,
  "example_quality": 8,
  "overall": 7.6
}
```""",
            "feedback": """```json
{
  "summary": "Strong technical answer with good detail.",
  "strengths": ["Good structure"],
  "improvements": ["Add examples"],
  "ideal_answer_points": ["Mention trade-offs"]
}
```""",
            "follow_up_recommendation": """```json
{
  "recommended": true,
  "suggested_follow_up_question": "Can you explain the trade-offs?"
}
```""",
        }
    )
    assert result["scores"]["technical_correctness"] == 8
    assert result["scores"]["overall"] == 7.6
    assert result["feedback"]["summary"] == "Strong technical answer with good detail."
    assert result["feedback"]["missed_points"] == []
    assert result["feedback"]["suggested_better_answer"] == ""
    assert result["follow_up"]["recommended"] is True
    assert result["follow_up"]["reason"] == ""
    assert result["follow_up"]["question_text"] == "Can you explain the trade-offs?"


def test_llm_evaluation_result_from_text_extracts_fenced_json():
    service = LLMService()
    result = service._coerce_evaluation_result_from_text(
        """```json
{
  "scores": {
    "technical_correctness": 8,
    "clarity": 8,
    "depth": 4,
    "confidence": 7,
    "relevance": 8,
    "structure": 7,
    "communication": 8,
    "conciseness": 6,
    "example_quality": 5,
    "overall": 6
  },
  "feedback": {
    "summary": "Foundational answer with missing depth.",
    "strengths": ["Good resource identification"],
    "improvements": ["Add request and response body details"],
    "ideal_answer_points": ["Define API contracts"],
    "missed_points": ["Detailed response body schemas"],
    "suggested_better_answer": "Provide concrete endpoint payload examples."
  },
  "follow_up_recommendation": {
    "recommended": true,
    "reason": "Candidate needs to elaborate on payload structure.",
    "suggested_follow_up_question": "Can you describe the POST /projects request body in detail?"
  }
}
```"""
    )
    assert result["scores"]["technical_correctness"] == 8
    assert result["feedback"]["summary"] == "Foundational answer with missing depth."
    assert result["feedback"]["missed_points"] == ["Detailed response body schemas"]
    assert result["follow_up"]["recommended"] is True
    assert result["follow_up"]["reason"] == "Candidate needs to elaborate on payload structure."
    assert result["follow_up"]["question_text"] == "Can you describe the POST /projects request body in detail?"


def test_llm_evaluation_result_from_full_gemini_rest_payload():
    service = LLMService()
    result = service._coerce_evaluation_result_from_text(
        """{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```json\\n{\\n  \\"scores\\": {\\n    \\"technical_correctness\\": 8,\\n    \\"clarity\\": 8,\\n    \\"depth\\": 4,\\n    \\"confidence\\": 8,\\n    \\"relevance\\": 9,\\n    \\"structure\\": 7,\\n    \\"communication\\": 7,\\n    \\"conciseness\\": 6,\\n    \\"example_quality\\": 5,\\n    \\"overall\\": 6\\n  },\\n  \\"feedback\\": {\\n    \\"summary\\": \\"Foundational API answer with missing depth.\\",\\n    \\"strengths\\": [\\"Correct endpoints\\"],\\n    \\"improvements\\": [\\"Add payload examples\\"],\\n    \\"ideal_answer_points\\": [\\"Define response bodies\\"],\\n    \\"missed_points\\": [\\"Detailed error body examples\\"],\\n    \\"suggested_better_answer\\": \\"Include concrete JSON payloads.\\"\\n  },\\n  \\"follow_up_recommendation\\": {\\n    \\"recommended\\": true,\\n    \\"reason\\": \\"Need more implementation detail.\\",\\n    \\"suggested_follow_up_question\\": \\"Can you describe the POST /projects request body?\\"\\n  }\\n}\\n```"
          }
        ],
        "role": "model"
      }
    }
  ]
}"""
    )
    assert result["scores"]["technical_correctness"] == 8
    assert result["feedback"]["summary"] == "Foundational API answer with missing depth."
    assert result["feedback"]["missed_points"] == ["Detailed error body examples"]
    assert result["follow_up"]["recommended"] is True
    assert result["follow_up"]["reason"] == "Need more implementation detail."
    assert result["follow_up"]["question_text"] == "Can you describe the POST /projects request body?"


def test_llm_final_report_result_coerces_nested_jsonish_fields():
    service = LLMService()
    result = service._coerce_final_report_result(
        {
            "overall_score": 7.8,
            "score_breakdown": """```json
{
  "technical": 8.1,
  "communication": 7.2,
  "confidence": 7.0,
  "problem_solving": 8.0,
  "role_fit": 8.3
}
```""",
            "summary": "Strong backend interview performance.",
            "strengths": ["API design", "trade-off discussion"],
            "weaknesses": ["Conciseness"],
            "recommended_topics": ["System design", "behavioral examples"],
        }
    )
    assert result["overall_score"] == 7.8
    assert result["score_breakdown"]["technical"] == 8.1
    assert result["score_breakdown"]["role_fit"] == 8.3
    assert result["summary"] == "Strong backend interview performance."


def test_llm_final_report_result_from_full_gemini_rest_payload():
    service = LLMService()
    result = service._coerce_final_report_result_from_text(
        """{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```json\\n{\\n  \\"overall_score\\": 6.8,\\n  \\"score_breakdown\\": {\\n    \\"technical\\": 6.7,\\n    \\"communication\\": 7.1,\\n    \\"confidence\\": 7.5,\\n    \\"problem_solving\\": 7.0,\\n    \\"role_fit\\": 8.5\\n  },\\n  \\"summary\\": \\"Promising candidate with areas for growth.\\",\\n  \\"strengths\\": [\\"Clear communication\\"],\\n  \\"weaknesses\\": [\\"Needs deeper payload design\\"],\\n  \\"recommended_topics\\": [\\"Advanced RESTful API design patterns\\"]\\n}\\n```"
          }
        ],
        "role": "model"
      }
    }
  ]
}"""
    )
    assert result["overall_score"] == 6.8
    assert result["score_breakdown"]["technical"] == 6.7
    assert result["score_breakdown"]["role_fit"] == 8.5
    assert result["summary"] == "Promising candidate with areas for growth."
    assert result["strengths"] == ["Clear communication"]
    assert result["weaknesses"] == ["Needs deeper payload design"]
    assert result["recommended_topics"] == ["Advanced RESTful API design patterns"]


def test_llm_final_report_result_salvages_truncated_json():
    service = LLMService()
    result = service._coerce_final_report_result_from_text(
        """{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```json\\n{\\n  \\"overall_score\\": 6.8,\\n  \\"score_breakdown\\": {\\n    \\"technical\\": 6.7,\\n    \\"communication\\": 7.1,\\n    \\"confidence\\": 7.5,\\n    \\"problem_solving\\": 7.0,\\n    \\"role_fit\\": 8.5\\n  },\\n  \\"summary\\": \\"Promising candidate with areas for growth.\\",\\n  \\"strengths\\": [\\"Clear communication\\"],\\n  \\"weaknesses\\": [\\"Needs deeper payload design\\"],\\n  \\"recommended_topics\\": [\\"Advanced RESTful API design patterns\\""
          }
        ],
        "role": "model"
      }
    }
  ]
}"""
    )
    assert result["overall_score"] == 6.8
    assert result["score_breakdown"]["technical"] == 6.7
    assert result["score_breakdown"]["role_fit"] == 8.5
    assert result["summary"] == "Promising candidate with areas for growth."
    assert result["strengths"] == ["Clear communication"]
    assert result["weaknesses"] == ["Needs deeper payload design"]
    assert result["recommended_topics"] == []


def test_llm_resume_profile_result_from_full_gemini_rest_payload():
    service = LLMService()
    result = service._coerce_resume_profile_result_from_text(
        """{
  "candidates": [
    {
      "content": {
        "parts": [
          {
            "text": "```json\\n{\\n  \\"candidate_name\\": \\"Hemansh Solanki\\",\\n  \\"email\\": \\"hemansh@example.com\\",\\n  \\"phone\\": \\"+91-9000000000\\",\\n  \\"location\\": \\"India\\",\\n  \\"summary\\": \\"Backend engineer focused on APIs and automation.\\",\\n  \\"total_experience_years\\": 2.5,\\n  \\"current_or_latest_role\\": \\"Software Engineer\\",\\n  \\"skills\\": {\\n    \\"languages\\": [\\"Python\\", \\"Go\\"],\\n    \\"frameworks\\": [\\"FastAPI\\", \\"React\\"],\\n    \\"databases\\": [\\"PostgreSQL\\"],\\n    \\"cloud_devops\\": [\\"Docker\\"],\\n    \\"testing_tools\\": [\\"pytest\\", \\"Playwright\\"],\\n    \\"other\\": [\\"LLM integration\\"]\\n  },\\n  \\"experience\\": [],\\n  \\"projects\\": [],\\n  \\"education\\": [],\\n  \\"strength_areas\\": [\\"Backend APIs\\", \\"Automation\\"],\\n  \\"possible_weak_areas\\": [\\"Large-scale system design\\"],\\n  \\"recommended_interview_topics\\": [\\"API design\\", \\"CI/CD\\"]\\n}\\n```"
          }
        ],
        "role": "model"
      }
    }
  ]
}"""
    )
    assert result["candidate_name"] == "Hemansh Solanki"
    assert result["email"] == "hemansh@example.com"
    assert result["total_experience_years"] == 2.5
    assert result["skills"]["languages"] == ["Python", "Go"]
    assert result["skills"]["frameworks"] == ["FastAPI", "React"]
    assert result["strength_areas"] == ["Backend APIs", "Automation"]
    assert result["recommended_interview_topics"] == ["API design", "CI/CD"]


def test_candidate_profile_prompt_context_is_human_readable():
    service = LLMService()
    context = service._candidate_profile_prompt_context(
        {
            "candidate_name": "Hemansh Solanki",
            "current_or_latest_role": "Software Engineer",
            "total_experience_years": 2.5,
            "summary": "Backend engineer focused on APIs and automation.",
            "skills": {
                "languages": ["Python", "Go"],
                "frameworks": ["FastAPI", "React"],
                "databases": ["PostgreSQL"],
                "cloud_devops": ["Docker"],
                "testing_tools": ["pytest"],
                "other": ["LLM integration"],
            },
            "experience": [
                {
                    "company": "ExampleCorp",
                    "role": "Software Engineer",
                    "technologies": ["Python", "FastAPI"],
                    "achievements": ["Improved API latency by 30%"],
                    "responsibilities": [],
                }
            ],
            "projects": [
                {
                    "name": "InterviewOS",
                    "description": "AI voice interview coach",
                    "technologies": ["FastAPI", "Next.js"],
                    "interview_focus": ["API design", "LLM integration"],
                }
            ],
            "strength_areas": ["Backend APIs"],
            "recommended_interview_topics": ["API design"],
        }
    )
    assert "Candidate name: Hemansh Solanki" in context
    assert "Current or latest role: Software Engineer" in context
    assert "Languages: Python, Go" in context
    assert "Experience: Software Engineer at ExampleCorp" in context
    assert "Project: InterviewOS" in context
