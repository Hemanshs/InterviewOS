from app.core.config import settings

USE_MOCK = settings.USE_MOCK_AI


class EvaluationService:
    async def evaluate_answer(
        self,
        question_text: str,
        transcript: str,
        candidate_profile: dict | None,
        interview_type: str,
        prompt_version: str,
    ) -> dict:
        """
        TODO: Call LLM with build_evaluation_prompt(...).
        Model: gpt-4o-mini for per-answer evaluation.
        Parse 9 score fields from JSON response.
        prompt_version = get_prompt_version("answer_evaluation")
        """
        if USE_MOCK:
            return self._mock_evaluation()
        raise NotImplementedError("Real implementation not built yet")

    async def generate_final_report(
        self,
        session_id: str,
        all_scores: list[dict],
        all_transcripts: list[dict],
        candidate_profile: dict | None,
        prompt_version: str,
    ) -> dict:
        """
        TODO: Call LLM with build_final_report_prompt(...).
        Model: gpt-4o or Claude Sonnet for final report (higher quality).
        prompt_version = get_prompt_version("final_report")
        """
        if USE_MOCK:
            return self._mock_final_report()
        raise NotImplementedError("Real implementation not built yet")

    def _mock_evaluation(self) -> dict:
        return {
            "technical_score": 7,
            "clarity_score": 8,
            "depth_score": 6,
            "confidence_score": 7,
            "relevance_score": 9,
            "structure_score": 7,
            "communication_score": 8,
            "conciseness_score": 6,
            "example_quality_score": 5,
            "overall_score": 7.0,
            "feedback_text": "Good answer with solid understanding of the concept. Could benefit from a concrete real-world example.",
            "strengths": ["Clear explanation", "Relevant to the question"],
            "improvements": ["Add a specific example from your experience", "Go deeper on trade-offs"],
            "follow_up_question": "Can you give a specific example of when you applied this approach in production?",
        }

    def _mock_final_report(self) -> dict:
        return {
            "overall_score": 7.2,
            "score_breakdown": {
                "technical": 7.0,
                "communication": 7.8,
                "confidence": 6.5,
                "clarity": 7.5,
                "overall": 7.2,
            },
            "summary": "Strong communication skills with solid technical fundamentals. Focus on deepening system design knowledge.",
            "strengths": ["Clear verbal communication", "Good problem structuring", "Relevant examples"],
            "weaknesses": ["System design depth", "Trade-off analysis"],
            "recommended_topics": ["Distributed systems basics", "Database indexing", "API rate limiting patterns"],
            "question_reviews": [],
        }
