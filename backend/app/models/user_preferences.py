from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, func

from app.db.session import Base


class UserPreferences(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)

    cv_text = Column(Text, default="")
    target_stack = Column(JSON, default=[])  # ["python", "typescript", "react"]
    target_seniority = Column(String(50), default="mid")  # junior, mid, senior
    target_location = Column(String(255), default="London, UK")

    digest_enabled = Column(Boolean, default=True)
    digest_hour_utc = Column(Integer, default=8)
    digest_email = Column(String(255), nullable=True)

    ats_guidelines = Column(Text, default="")
    job_requirements_context = Column(Text, default="")
    cover_letter_guidelines = Column(Text, default="")
    similarity_threshold = Column(Integer, default=90)
    sponsorship_bonus_threshold = Column(Integer, default=50)
    stale_task_timeout_minutes = Column(Integer, default=10)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
