from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CandidateExperience(BaseModel):
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    highlights: list[str] = Field(default_factory=list)


class CandidateProject(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)


class CandidateEducation(BaseModel):
    institution: str
    degree: str
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class CandidateProfile(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[CandidateExperience] = Field(default_factory=list)
    projects: list[CandidateProject] = Field(default_factory=list)
    education: list[CandidateEducation] = Field(default_factory=list)


class ResumeUploadData(BaseModel):
    resume_id: UUID
    file_name: str
    file_url: str
    parsed: bool
    profile: Optional[CandidateProfile] = None
    created_at: datetime


class ResumeLatestData(ResumeUploadData):
    pass
