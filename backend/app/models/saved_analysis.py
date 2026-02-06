from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, JSON, func

from app.db.session import Base


class SavedAnalysis(Base):
    __tablename__ = "saved_analyses"

    id = Column(Integer, primary_key=True, index=True)

    # Job information (from LLM summary)
    job_title = Column(String(512), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_description = Column(Text, nullable=False)
    job_url = Column(String(2048), nullable=False)

    # Eligibility results
    eligibility_status = Column(String(50), nullable=False)  # eligible, partially_eligible, not_eligible
    eligibility_reasons = Column(JSON, nullable=False, default=list)

    # Matching results
    matching_score = Column(Integer, nullable=False)
    matching_explanation = Column(Text, nullable=False)

    # Job summary
    key_requirements = Column(JSON, nullable=False, default=list)

    # Resume suggestions (stored as JSON array)
    resume_suggestions = Column(JSON, nullable=False, default=list)

    # ATS keywords (stored as JSON array)
    ats_keywords = Column(JSON, nullable=False, default=list)

    # Cover letter
    cover_letter = Column(Text, nullable=False)

    # Metadata
    processing_time_ms = Column(Integer, nullable=False)
    llm_model = Column(String(512), nullable=True)
    applied = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
