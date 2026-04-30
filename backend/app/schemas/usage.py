from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


class UsageLimits(BaseModel):
    free_interviews_total: int
    questions_per_session: int
    answer_duration_seconds: int
    audio_upload_mb: int
    stored_resumes: int


class UsageCurrent(BaseModel):
    free_interview_used: bool
    questions_used_current_session: int
    resumes_stored: int


class UsageRemaining(BaseModel):
    free_interviews: int
    resumes: int


class UsageData(BaseModel):
    plan: Literal["free", "pro", "team"]
    limits: UsageLimits
    usage: UsageCurrent
    remaining: UsageRemaining
    reset_at: Optional[datetime] = None
