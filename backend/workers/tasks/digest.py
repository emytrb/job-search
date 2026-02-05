import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.saved_analysis import SavedAnalysis
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

        # Get top analyzed jobs (eligible or partially eligible)
        analyses_query = (
            select(SavedAnalysis)
            .where(SavedAnalysis.eligibility_status.in_(["eligible", "partially_eligible"]))
            .order_by(desc(SavedAnalysis.matching_score))
            .limit(settings.digest_max_jobs)
        )
        analyses_result = await db.execute(analyses_query)
        analyses = analyses_result.scalars().all()

        if not analyses:
            return {"status": "skipped", "reason": "No analyzed jobs to send"}

        job_data = []
        job_ids = []

        for analysis in analyses:
            job_data.append({
                "id": analysis.id,
                "title": analysis.job_title,
                "company_name": analysis.company_name,
                "url": analysis.job_url,
                "score": analysis.matching_score,
                "eligibility": analysis.eligibility_status,
                "key_requirements": analysis.key_requirements[:3] if analysis.key_requirements else [],
            })
            job_ids.append(analysis.id)

        template = jinja_env.get_template("digest.html")
        html_content = template.render(
            jobs=job_data,
            job_count=len(job_data),
            date=datetime.now(timezone.utc).strftime("%B %d, %Y"),
            dashboard_url="http://localhost:3000",
        )

        subject = f"Daily Job Digest - {len(job_data)} analyzed opportunities"

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
