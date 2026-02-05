from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DigestJobPreview(BaseModel):
    id: int
    title: str
    company: str
    score: float


class DigestPreview(BaseModel):
    job_count: int
    jobs: list[dict]


class DigestResponse(BaseModel):
    id: int
    job_count: int
    recipient_email: str
    subject: str
    sent_at: datetime
    status: str
    error_message: Optional[str]

    class Config:
        from_attributes = True
