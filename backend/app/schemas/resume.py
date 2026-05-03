from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SkillSet(BaseModel):
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    databases: list[str] = Field(default_factory=list)
    cloud_devops: list[str] = Field(default_factory=list)
    testing_tools: list[str] = Field(default_factory=list)
    other: list[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: list[str] = Field(default_factory=list)
    interview_focus: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None


class CandidateProfile(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    total_experience_years: Optional[float] = None
    current_or_latest_role: Optional[str] = None
    skills: SkillSet = Field(default_factory=SkillSet)
    experience: list[ExperienceItem] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    strength_areas: list[str] = Field(default_factory=list)
    possible_weak_areas: list[str] = Field(default_factory=list)
    recommended_interview_topics: list[str] = Field(default_factory=list)


class ResumeUploadData(BaseModel):
    resume_id: UUID
    file_name: str
    file_url: str
    parsed: bool
    profile: Optional[CandidateProfile] = None
    created_at: datetime


class ResumeLatestData(BaseModel):
    resume_id: UUID
    file_name: str
    profile: Optional[CandidateProfile] = None
    created_at: datetime
