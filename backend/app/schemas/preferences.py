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
    created_at: datetime
    updated_at: Optional[datetime]

    @field_validator('ats_guidelines', 'job_requirements_context', 'cover_letter_guidelines', mode='before')
    @classmethod
    def empty_str_if_none(cls, v):
        return v or ""

    class Config:
        from_attributes = True
