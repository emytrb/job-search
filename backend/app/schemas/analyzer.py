from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    job_text: str = Field(..., min_length=100)
    job_url: str = Field(..., min_length=1)


class JobSummaryResponse(BaseModel):
    title: str
    company: str
    key_requirements: list[str]


class ResumeSuggestionResponse(BaseModel):
    section: str
    suggestion: str
    reason: str


class ATSKeywordResponse(BaseModel):
    keyword: str
    found_in_resume: bool
    importance: str


class AnalyzeResponse(BaseModel):
    eligibility_status: str  # "eligible" | "partially_eligible" | "not_eligible"
    eligibility_reasons: list[str]
    matching_score: int
    matching_explanation: str
    job_summary: JobSummaryResponse
    resume_suggestions: list[ResumeSuggestionResponse]
    ats_keywords: list[ATSKeywordResponse]
    cover_letter: str
    processing_time_ms: int


class SavedAnalysisResponse(BaseModel):
    id: int
    job_title: str
    company_name: str
    job_description: str
    job_url: str
    eligibility_status: str
    eligibility_reasons: list[str]
    matching_score: int
    matching_explanation: str
    key_requirements: list[str]
    resume_suggestions: list[ResumeSuggestionResponse]
    ats_keywords: list[ATSKeywordResponse]
    cover_letter: str
    processing_time_ms: int
    llm_model: str | None = None
    applied: bool = False
    created_at: datetime
    last_analyzed_at: datetime

    class Config:
        from_attributes = True


class SavedAnalysisListItem(BaseModel):
    id: int
    job_title: str
    company_name: str
    eligibility_status: str
    matching_score: int
    applied: bool = False
    created_at: datetime
    last_analyzed_at: datetime

    class Config:
        from_attributes = True


class ToggleAppliedResponse(BaseModel):
    id: int
    applied: bool


class SavedAnalysisListResponse(BaseModel):
    analyses: list[SavedAnalysisListItem]
    total: int


class QueueItemResponse(BaseModel):
    id: int
    job_text_preview: str  # First 100 chars
    job_url: str
    status: str  # pending, processing, completed, failed
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    saved_analysis_id: Optional[int] = None
    job_title: Optional[str] = None  # From saved analysis if completed
    company_name: Optional[str] = None  # From saved analysis if completed
    matching_score: Optional[int] = None  # From saved analysis if completed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QueueStatusResponse(BaseModel):
    items: list[QueueItemResponse]
    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int


class QueueAddResponse(BaseModel):
    id: int
    status: str
    position: int  # Position in queue


class RequeueRequest(BaseModel):
    analysis_ids: list[int] = Field(..., min_length=1)


class RequeueResponse(BaseModel):
    queued_count: int
    queue_items: list[QueueAddResponse]
