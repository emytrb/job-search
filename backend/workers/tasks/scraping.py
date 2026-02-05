import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.scrape_source import ScrapeSource, RiskLevel
from app.models.scrape_run import ScrapeRun, RunStatus
from app.models.job import Job, JobStatus
from app.services.dedup import compute_dedup_hash, job_exists
from scrapers.sources import get_scraper

logger = logging.getLogger(__name__)


def get_async_session():
    """Create a new engine and session factory for the current event loop.

    This must be called inside an async context to avoid event loop conflicts
    when using asyncio.run() in Celery tasks.
    """
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _scrape_source_async(source_id: int) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        source_query = select(ScrapeSource).where(ScrapeSource.id == source_id)
        result = await db.execute(source_query)
        source = result.scalar_one_or_none()

        if not source:
            return {"error": f"Source {source_id} not found"}

        if not source.enabled:
            return {"error": f"Source {source_id} is disabled"}

        run = ScrapeRun(
            source_id=source_id,
            status=RunStatus.RUNNING,
        )
        db.add(run)
        await db.commit()
        await db.refresh(run)

        jobs_found = 0
        jobs_new = 0

        try:
            scraper = get_scraper(
                source_type=source.source_type.value,
                base_url=source.base_url,
                config=source.config,
            )

            async with scraper:
                async for raw_job in scraper.scrape():
                    jobs_found += 1

                    dedup_hash = compute_dedup_hash(
                        raw_job.company_name,
                        raw_job.title,
                        raw_job.location,
                    )

                    if await job_exists(db, dedup_hash):
                        continue

                    job = Job(
                        source_id=source_id,
                        external_id=raw_job.external_id,
                        dedup_hash=dedup_hash,
                        title=raw_job.title,
                        company_name=raw_job.company_name,
                        location=raw_job.location,
                        description=raw_job.description,
                        url=raw_job.url,
                        salary_min=raw_job.salary_min,
                        salary_max=raw_job.salary_max,
                        salary_currency=raw_job.salary_currency,
                        status=JobStatus.RAW,
                    )
                    db.add(job)
                    await db.commit()
                    await db.refresh(job)

                    jobs_new += 1

                    from workers.tasks.processing import process_raw_job
                    process_raw_job.delay(job.id)

            run.status = RunStatus.COMPLETED
            run.jobs_found = jobs_found
            run.jobs_new = jobs_new
            run.completed_at = datetime.now(timezone.utc)

            source.last_scraped_at = datetime.now(timezone.utc)

            await db.commit()

            return {
                "source_id": source_id,
                "jobs_found": jobs_found,
                "jobs_new": jobs_new,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Scraping failed for source {source_id}: {e}")
            run.status = RunStatus.FAILED
            run.error_message = str(e)[:2000]
            run.completed_at = datetime.now(timezone.utc)
            await db.commit()

            return {"error": str(e)}


@celery_app.task(name="workers.tasks.scraping.scrape_source")
def scrape_source(source_id: int) -> dict:
    return asyncio.run(_scrape_source_async(source_id))


async def _scrape_all_sources_async(risk_level: str) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        risk = RiskLevel(risk_level)
        query = select(ScrapeSource).where(
            ScrapeSource.enabled == True,
            ScrapeSource.risk_level == risk,
        )
        result = await db.execute(query)
        sources = result.scalars().all()

        triggered = []
        for source in sources:
            scrape_source.delay(source.id)
            triggered.append(source.id)

        return {
            "risk_level": risk_level,
            "triggered_sources": triggered,
        }


@celery_app.task(name="workers.tasks.scraping.scrape_all_sources")
def scrape_all_sources(risk_level: str = "low") -> dict:
    return asyncio.run(_scrape_all_sources_async(risk_level))
