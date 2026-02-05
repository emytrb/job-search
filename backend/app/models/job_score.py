from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class JobScore(Base):
    __tablename__ = "job_scores"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)

    stack_match_score = Column(Float, default=0.0)  # 0-100
    seniority_match_score = Column(Float, default=0.0)  # 0-100
    sponsorship_score = Column(Float, default=0.0)  # 0-100
    quality_score = Column(Float, default=0.0)  # 0-100
    total_score = Column(Float, default=0.0, index=True)  # 0-100

    stack_match_details = Column(Integer, default=0)  # matched technologies count
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="score")
