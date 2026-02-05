import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.services.hard_filter import hard_filter

logger = logging.getLogger(__name__)


def get_async_session():
    """Create a new engine and session factory for the current event loop."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _process_raw_job_async(job_id: int) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return {"error": f"Job {job_id} not found"}

        if job.status != JobStatus.RAW:
            return {"error": f"Job {job_id} is not in RAW status"}

        filter_result = hard_filter.check(job)

        if not filter_result.passed:
            job.status = JobStatus.FILTERED_OUT
            job.filter_reason = filter_result.reason
            await db.commit()

            return {
                "job_id": job_id,
                "status": "filtered_out",
                "reason": filter_result.reason,
            }

        job.status = JobStatus.ANALYZING
        await db.commit()

        from workers.tasks.analysis import analyze_job
        analyze_job.delay(job_id)

        return {
            "job_id": job_id,
            "status": "sent_to_analysis",
        }


@celery_app.task(name="workers.tasks.processing.process_raw_job")
def process_raw_job(job_id: int) -> dict:
    return asyncio.run(_process_raw_job_async(job_id))
