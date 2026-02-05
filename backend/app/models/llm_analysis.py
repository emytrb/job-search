from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import relationship

from app.db.session import Base


class LLMAnalysis(Base):
    __tablename__ = "llm_analyses"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, unique=True)

    seniority_level = Column(String(50))  # junior, mid, senior, staff, principal
    detected_stack = Column(JSON, default=[])  # ["python", "fastapi", "postgresql"]
    required_experience_years = Column(Integer, nullable=True)
    sponsorship_likelihood = Column(Float)  # 0.0 - 1.0
    remote_policy = Column(String(50))  # remote, hybrid, onsite, unknown
    team_size = Column(String(50), nullable=True)
    key_responsibilities = Column(JSON, default=[])
    nice_to_haves = Column(JSON, default=[])

    raw_response = Column(JSON)
    model_used = Column(String(100))
    processing_time_ms = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    job = relationship("Job", back_populates="analysis")
