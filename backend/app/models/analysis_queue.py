from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class QueueItemStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisQueueItem(Base):
    __tablename__ = "analysis_queue"

    id = Column(Integer, primary_key=True, index=True)

    # Job information
    job_title = Column(String(512), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_text = Column(Text, nullable=False)
    job_url = Column(String(2048), nullable=False)

    # Status
    status = Column(String(50), default=QueueItemStatus.PENDING.value, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # Retry mechanism
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)

    # Celery task ID for tracking
    celery_task_id = Column(String(255), nullable=True)

    # Reference to the saved analysis once completed
    saved_analysis_id = Column(Integer, ForeignKey("saved_analyses.id"), nullable=True)
    saved_analysis = relationship("SavedAnalysis", backref="queue_item")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
