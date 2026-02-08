from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional


class UserPreferencesCreate(BaseModel):
    cv_text: Optional[str] = None
    target_stack: Optional[list[str]] = None
    target_seniority: Optional[str] = None
    target_location: Optional[str] = None
    digest_enabled: Optional[bool] = None
    digest_hour_utc: Optional[int] = None
    digest_email: Optional[str] = None
    ats_guidelines: Optional[str] = None
    job_requirements_context: Optional[str] = None
    cover_letter_guidelines: Optional[str] = None
    similarity_threshold: Optional[int] = None
    sponsorship_bonus_threshold: Optional[int] = None
    stale_task_timeout_minutes: Optional[int] = None


class UserPreferencesResponse(BaseModel):
    id: int
    cv_text: str
    target_stack: list[str]
    target_seniority: str
    target_location: str
    digest_enabled: bool
    digest_hour_utc: int
    digest_email: Optional[str]
    ats_guidelines: str = ""
    job_requirements_context: str = ""
    cover_letter_guidelines: str = ""
    similarity_threshold: int = 90
    sponsorship_bonus_threshold: int = 50
    stale_task_timeout_minutes: int = 10
    created_at: datetime
    updated_at: Optional[datetime]

    @field_validator('ats_guidelines', 'job_requirements_context', 'cover_letter_guidelines', mode='before')
    @classmethod
    def empty_str_if_none(cls, v):
        return v or ""

    @field_validator('similarity_threshold', mode='before')
    @classmethod
    def default_threshold(cls, v):
        return v if v is not None else 90

    @field_validator('sponsorship_bonus_threshold', mode='before')
    @classmethod
    def default_sponsorship_threshold(cls, v):
        return v if v is not None else 50

    @field_validator('stale_task_timeout_minutes', mode='before')
    @classmethod
    def default_stale_timeout(cls, v):
        return v if v is not None else 10

    class Config:
        from_attributes = True
