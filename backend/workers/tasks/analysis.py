import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.job import Job, JobStatus
from app.models.llm_analysis import LLMAnalysis
from app.models.job_score import JobScore
from app.models.user_preferences import UserPreferences
from app.services.scoring import ScoringService
from llm.client import llm_client

logger = logging.getLogger(__name__)


def get_async_session():
    """Create a new engine and session factory for the current event loop."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _analyze_job_async(job_id: int) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return {"error": f"Job {job_id} not found"}

        if job.status != JobStatus.ANALYZING:
            return {"error": f"Job {job_id} is not in ANALYZING status"}

        try:
            analysis_result = await llm_client.analyze_job(
                title=job.title,
                description=job.description or "",
            )

            analysis = LLMAnalysis(
                job_id=job_id,
                seniority_level=analysis_result.seniority_level,
                detected_stack=analysis_result.detected_stack,
                required_experience_years=analysis_result.required_experience_years,
                sponsorship_likelihood=analysis_result.sponsorship_likelihood,
                remote_policy=analysis_result.remote_policy,
                key_responsibilities=analysis_result.key_responsibilities,
                nice_to_haves=analysis_result.nice_to_haves,
                raw_response=analysis_result.raw_response,
                model_used=analysis_result.model_used,
                processing_time_ms=analysis_result.processing_time_ms,
            )
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)

            compute_job_score.delay(job_id)

            return {
                "job_id": job_id,
                "status": "analyzed",
                "seniority": analysis_result.seniority_level,
                "stack_count": len(analysis_result.detected_stack),
            }

        except Exception as e:
            logger.error(f"Analysis failed for job {job_id}: {e}")
            job.status = JobStatus.RAW
            await db.commit()
            return {"error": str(e)}


@celery_app.task(name="workers.tasks.analysis.analyze_job")
def analyze_job(job_id: int) -> dict:
    return asyncio.run(_analyze_job_async(job_id))


async def _compute_job_score_async(job_id: int) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        query = select(Job).where(Job.id == job_id)
        result = await db.execute(query)
        job = result.scalar_one_or_none()

        if not job:
            return {"error": f"Job {job_id} not found"}

        analysis_query = select(LLMAnalysis).where(LLMAnalysis.job_id == job_id)
        analysis_result = await db.execute(analysis_query)
        analysis = analysis_result.scalar_one_or_none()

        if not analysis:
            return {"error": f"No analysis found for job {job_id}"}

        prefs_query = select(UserPreferences).limit(1)
        prefs_result = await db.execute(prefs_query)
        prefs = prefs_result.scalar_one_or_none()

        target_stack = prefs.target_stack if prefs else []
        target_seniority = prefs.target_seniority if prefs else "mid"

        scoring = ScoringService(
            target_stack=target_stack,
            target_seniority=target_seniority,
        )

        score_result = scoring.compute_score(job, analysis)

        score = JobScore(
            job_id=job_id,
            stack_match_score=score_result.stack_match_score,
            seniority_match_score=score_result.seniority_match_score,
            sponsorship_score=score_result.sponsorship_score,
            quality_score=score_result.quality_score,
            total_score=score_result.total_score,
            stack_match_details=score_result.stack_match_details,
        )
        db.add(score)

        job.status = JobStatus.SCORED
        await db.commit()

        return {
            "job_id": job_id,
            "status": "scored",
            "total_score": score_result.total_score,
        }


@celery_app.task(name="workers.tasks.analysis.compute_job_score")
def compute_job_score(job_id: int) -> dict:
    return asyncio.run(_compute_job_score_async(job_id))
