from app.core.config import settings

USE_MOCK = settings.USE_MOCK_AI


class UsageService:
    async def get_usage_status(self, user_id: str, db) -> dict:
        """
        TODO: Query users table for free_interview_used.
        Query sessions table for current in_progress session question count.
        Query resumes table for stored resume count.
        Return computed usage data.
        """
        if USE_MOCK:
            return self._mock_usage_status()
        raise NotImplementedError("Real implementation not built yet")

    async def check_can_start_interview(self, user_id: str, db) -> bool:
        """
        TODO: Check users.free_interview_used == False for free plan users.
        Raise QuotaExceededError if limit reached.
        """
        if USE_MOCK:
            return True
        raise NotImplementedError("Real implementation not built yet")

    async def check_can_add_question(self, session_id: str, db) -> bool:
        """
        TODO: Count questions in session.
        Raise QuotaExceededError if count >= FREE_SESSION_QUESTION_LIMIT.
        """
        if USE_MOCK:
            return True
        raise NotImplementedError("Real implementation not built yet")

    async def mark_free_interview_used(self, user_id: str, db) -> None:
        """
        TODO: UPDATE users SET free_interview_used = true WHERE id = user_id.
        Call this when POST /api/interview/start succeeds.
        """
        if USE_MOCK:
            return
        raise NotImplementedError("Real implementation not built yet")

    async def log_usage_event(
        self,
        user_id: str,
        event_type: str,
        session_id: str | None = None,
        model_name: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        audio_duration_seconds: int | None = None,
        estimated_cost_usd: float | None = None,
        db=None,
    ) -> None:
        """
        TODO: INSERT into usage_events table.
        Call after every LLM, STT, and TTS operation.
        """
        if USE_MOCK:
            return
        raise NotImplementedError("Real implementation not built yet")

    def _mock_usage_status(self) -> dict:
        return {
            "plan": "free",
            "limits": {
                "free_interviews_total": 1,
                "questions_per_session": 5,
                "answer_duration_seconds": 60,
                "audio_upload_mb": 10,
                "stored_resumes": 1,
            },
            "usage": {
                "free_interview_used": False,
                "questions_used_current_session": 0,
                "resumes_stored": 0,
            },
            "remaining": {
                "free_interviews": 1,
                "resumes": 1,
            },
            "reset_at": None,
        }
