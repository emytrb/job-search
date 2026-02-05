from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class SourceType(str, enum.Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WTTJ = "wttj"
    INDEED = "indeed"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ScrapeSource(Base):
    __tablename__ = "scrape_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    source_type = Column(
        Enum(SourceType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    base_url = Column(String(1024), nullable=False)
    risk_level = Column(
        Enum(RiskLevel, values_callable=lambda x: [e.value for e in x]),
        default=RiskLevel.LOW
    )
    config = Column(JSON, default={})
    enabled = Column(Boolean, default=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)

    company = relationship("Company", back_populates="scrape_sources")
    scrape_runs = relationship("ScrapeRun", back_populates="source", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="source", cascade="all, delete-orphan")
