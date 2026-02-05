import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.job_score import JobScore
from app.models.llm_analysis import LLMAnalysis
from app.models.user_preferences import UserPreferences
from app.models.digest import Digest
from mailer.sender import email_sender

logger = logging.getLogger(__name__)

templates_dir = Path(__file__).parent.parent.parent / "mailer" / "templates"
jinja_env = Environment(loader=FileSystemLoader(templates_dir))


def get_async_session():
    """Create a new engine and session factory for the current event loop."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _send_daily_digest_async() -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        prefs_query = select(UserPreferences).limit(1)
        prefs_result = await db.execute(prefs_query)
        prefs = prefs_result.scalar_one_or_none()

        if not prefs or not prefs.digest_enabled:
            return {"status": "skipped", "reason": "Digest disabled"}

        recipient = prefs.digest_email or settings.email_to

        if not recipient:
            return {"status": "skipped", "reason": "No recipient configured"}

        jobs_query = (
            select(Job)
            .join(JobScore)
            .where(Job.status == JobStatus.SCORED)
            .order_by(JobScore.total_score.desc())
            .limit(settings.digest_max_jobs)
        )
        jobs_result = await db.execute(jobs_query)
        jobs = jobs_result.scalars().all()

        if not jobs:
            return {"status": "skipped", "reason": "No jobs to send"}

        job_data = []
        job_ids = []

        for job in jobs:
            analysis_query = select(LLMAnalysis).where(LLMAnalysis.job_id == job.id)
            analysis_result = await db.execute(analysis_query)
            analysis = analysis_result.scalar_one_or_none()

            score_query = select(JobScore).where(JobScore.job_id == job.id)
            score_result = await db.execute(score_query)
            score = score_result.scalar_one_or_none()

            job_data.append({
                "id": job.id,
                "title": job.title,
                "company_name": job.company_name,
                "location": job.location,
                "url": job.url,
                "score": score.total_score if score else 0,
                "seniority": analysis.seniority_level if analysis else None,
                "stack": analysis.detected_stack if analysis else [],
            })
            job_ids.append(job.id)

        template = jinja_env.get_template("digest.html")
        html_content = template.render(
            jobs=job_data,
            job_count=len(job_data),
            date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            dashboard_url="http://localhost:3000",
        )

        subject = f"Daily Job Digest - {len(job_data)} new opportunities"

        try:
            await email_sender.send_email(
                to=recipient,
                subject=subject,
                html_content=html_content,
            )

            digest = Digest(
                job_ids=job_ids,
                job_count=len(job_ids),
                recipient_email=recipient,
                subject=subject,
                status="sent",
            )
            db.add(digest)
            await db.commit()

            return {
                "status": "sent",
                "recipient": recipient,
                "job_count": len(job_ids),
            }

        except Exception as e:
            logger.error(f"Failed to send digest: {e}")

            digest = Digest(
                job_ids=job_ids,
                job_count=len(job_ids),
                recipient_email=recipient,
                subject=subject,
                status="failed",
                error_message=str(e)[:1000],
            )
            db.add(digest)
            await db.commit()

            return {"status": "failed", "error": str(e)}


@celery_app.task(name="workers.tasks.digest.send_daily_digest")
def send_daily_digest() -> dict:
    return asyncio.run(_send_daily_digest_async())
