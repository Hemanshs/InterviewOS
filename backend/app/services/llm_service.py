from app.core.config import settings
from app.prompts.base_prompts import get_prompt_version

USE_MOCK = settings.USE_MOCK_AI


class LLMService:
    async def generate_first_question(
        self,
        candidate_profile: dict | None,
        job_analysis: dict | None,
        interview_type: str,
        difficulty: str,
        prompt_version: str,
    ) -> dict:
        """
        TODO: Call OpenAI/Claude with build_first_question_prompt(...).
        Model: gpt-4o-mini for MVP question gen.
        Parse JSON response. Store prompt_version in questions table.
        """
        if USE_MOCK:
            return self._mock_question(sequence=1)
        raise NotImplementedError("Real implementation not built yet")

    async def generate_next_question(
        self,
        session_context: dict,
        previous_answers: list[dict],
        sequence: int,
        prompt_version: str,
    ) -> dict:
        """
        TODO: Call OpenAI/Claude with build_next_question_prompt(...).
        Adaptive difficulty: if overall_score >= 7 increase difficulty,
        if overall_score <= 4 reduce difficulty, else maintain.
        """
        if USE_MOCK:
            return self._mock_question(sequence=sequence)
        raise NotImplementedError("Real implementation not built yet")

    async def analyze_job_description(
        self,
        job_description: str,
        target_role: str,
        target_company: str,
        prompt_version: str,
    ) -> dict:
        """
        TODO: Call OpenAI/Claude with build_jd_analysis_prompt(...).
        Model: gpt-4o-mini.
        """
        if USE_MOCK:
            return self._mock_jd_analysis()
        raise NotImplementedError("Real implementation not built yet")

    def _mock_question(self, sequence: int) -> dict:
        questions = [
            "Can you walk me through how you would design a rate-limiting system for a public API?",
            "Your experience includes CI/CD pipelines. How did you handle test flakiness in automated suites?",
            "How would you approach debugging a memory leak in a long-running Python service?",
            "Describe a time you had to make a tradeoff between code quality and delivery speed.",
            "How do you ensure database queries stay performant as data grows?",
        ]
        return {
            "question_text": questions[min(sequence - 1, len(questions) - 1)],
            "question_type": "technical",
            "expected_focus_areas": ["system design", "API design", "scalability"],
            "prompt_version": get_prompt_version("first_question"),
            "audio_url": None,
        }

    def _mock_jd_analysis(self) -> dict:
        return {
            "role_title": "Software Development Engineer",
            "company": "Example Corp",
            "seniority_level": "mid",
            "must_have_skills": ["Python", "REST APIs", "SQL"],
            "nice_to_have_skills": ["Docker", "AWS"],
            "responsibilities": ["Build backend services", "Write unit tests"],
            "technical_domains": ["backend", "databases"],
            "likely_interview_topics": ["system design", "API design", "testing"],
            "behavioral_traits_expected": ["ownership", "communication"],
            "system_design_relevance": "medium",
            "coding_relevance": "high",
            "testing_relevance": "medium",
            "backend_relevance": "high",
        }
