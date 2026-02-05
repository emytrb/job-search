from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class JobStatus(str, enum.Enum):
    RAW = "raw"
    FILTERED_OUT = "filtered_out"
    ANALYZING = "analyzing"
    SCORED = "scored"
    DISMISSED = "dismissed"
    APPLIED = "applied"


class JobType(str, enum.Enum):
    PERMANENT = "permanent"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("scrape_sources.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)

    external_id = Column(String(255), nullable=False)
    dedup_hash = Column(String(64), unique=True, index=True)

    title = Column(String(512), nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255))
    job_type = Column(
        Enum(JobType, values_callable=lambda x: [e.value for e in x]),
        default=JobType.UNKNOWN
    )
    description = Column(Text)
    url = Column(String(1024))
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), nullable=True)

    status = Column(
        Enum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.RAW,
        index=True
    )
    filter_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())

    source = relationship("ScrapeSource", back_populates="jobs")
    company = relationship("Company", back_populates="jobs")
    analysis = relationship("LLMAnalysis", back_populates="job", uselist=False, cascade="all, delete-orphan")
    score = relationship("JobScore", back_populates="job", uselist=False, cascade="all, delete-orphan")
