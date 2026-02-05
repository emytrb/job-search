from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.scrape_source import SourceType, RiskLevel
from app.models.scrape_run import RunStatus


class ScrapeSourceCreate(BaseModel):
    name: str
    source_type: SourceType
    base_url: str
    risk_level: RiskLevel = RiskLevel.LOW
    config: Optional[dict] = None
    enabled: bool = True


class ScrapeSourceUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    config: Optional[dict] = None
    enabled: Optional[bool] = None


class ScrapeSourceResponse(BaseModel):
    id: int
    name: str
    source_type: SourceType
    base_url: str
    risk_level: RiskLevel
    config: dict
    enabled: bool
    last_scraped_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class ScrapeRunResponse(BaseModel):
    id: int
    source_id: int
    status: RunStatus
    jobs_found: int
    jobs_new: int
    error_message: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
