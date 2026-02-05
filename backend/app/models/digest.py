from sqlalchemy import Column, Integer, String, DateTime, JSON, func

from app.db.session import Base


class Digest(Base):
    __tablename__ = "digests"

    id = Column(Integer, primary_key=True, index=True)

    job_ids = Column(JSON, default=[])
    job_count = Column(Integer, default=0)
    recipient_email = Column(String(255))
    subject = Column(String(512))
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), default="sent")  # sent, failed
    error_message = Column(String(1024), nullable=True)
