from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.job import JobStatus, JobType


class JobResponse(BaseModel):
    id: int
    title: str
    company_name: str
    location: Optional[str]
    job_type: JobType
    url: Optional[str]
    salary_min: Optional[int]
    salary_max: Optional[int]
    salary_currency: Optional[str]
    status: JobStatus
    created_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    jobs: list[JobResponse]
    total: int
    limit: int
    offset: int


class LLMAnalysisResponse(BaseModel):
    seniority_level: Optional[str]
    detected_stack: list[str]
    required_experience_years: Optional[int]
    sponsorship_likelihood: Optional[float]
    remote_policy: Optional[str]

    class Config:
        from_attributes = True


class JobScoreResponse(BaseModel):
    stack_match_score: float
    seniority_match_score: float
    sponsorship_score: float
    quality_score: float
    total_score: float
    stack_match_details: int

    class Config:
        from_attributes = True


class JobDetail(BaseModel):
    job: JobResponse
    analysis: Optional[LLMAnalysisResponse]
    score: Optional[JobScoreResponse]
