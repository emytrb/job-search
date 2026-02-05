from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class RunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("scrape_sources.id"), nullable=False)
    status = Column(
        Enum(RunStatus, values_callable=lambda x: [e.value for e in x]),
        default=RunStatus.PENDING
    )
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    error_message = Column(String(2048), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    source = relationship("ScrapeSource", back_populates="scrape_runs")
