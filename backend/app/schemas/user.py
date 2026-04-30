from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class UserUsageData(BaseModel):
    free_interview_used: bool
    free_interviews_total: int = 1
    remaining_free_interviews: int


class UserData(BaseModel):
    id: UUID
    email: str
    plan: Literal["free", "pro", "team"]
    created_at: datetime
    usage: UserUsageData


class DeleteAccountRequest(BaseModel):
    confirmation: str


class DeleteAccountData(BaseModel):
    user_id: UUID
    deleted: bool
    deleted_at: datetime
