import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.analysis_queue import AnalysisQueueItem, QueueItemStatus
from app.models.saved_analysis import SavedAnalysis
from app.models.user_preferences import UserPreferences
from llm.client import llm_client
from app.utils.simhash import compute_simhash

logger = logging.getLogger(__name__)


def get_async_session():
    """Create a new engine and session factory for the current event loop."""
    engine = create_async_engine(settings.database_url, echo=False)
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _process_queue_item_async(queue_item_id: int) -> dict:
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        # Get the queue item
        query = select(AnalysisQueueItem).where(AnalysisQueueItem.id == queue_item_id)
        result = await db.execute(query)
        queue_item = result.scalar_one_or_none()

        if not queue_item:
            return {"error": f"Queue item {queue_item_id} not found"}

        if queue_item.status != QueueItemStatus.PROCESSING.value:
            return {"error": f"Queue item {queue_item_id} is not in PROCESSING status"}

        # Get user preferences
        prefs_query = select(UserPreferences).limit(1)
        prefs_result = await db.execute(prefs_query)
        prefs = prefs_result.scalar_one_or_none()

        if not prefs or not prefs.cv_text:
            queue_item.status = QueueItemStatus.FAILED.value
            queue_item.error_message = "CV text is required"
            queue_item.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return {"error": "CV text is required"}

        try:
            # Run the analysis
            analysis = await llm_client.analyze_job_offer(
                job_text=queue_item.job_text,
                cv_text=prefs.cv_text,
                job_requirements_context=prefs.job_requirements_context or "",
                ats_guidelines=prefs.ats_guidelines or "",
                cover_letter_guidelines=prefs.cover_letter_guidelines or "",
            )

            # Apply sponsorship bonus
            offers_sponsorship = analysis.offers_sponsorship
            final_score = analysis.matching_score
            threshold = prefs.sponsorship_bonus_threshold if prefs.sponsorship_bonus_threshold is not None else 50
            if offers_sponsorship and final_score >= threshold:
                final_score = min(final_score + 20, 100)

            # Check if this is a requeue (overwrite mode)
            if queue_item.saved_analysis_id:
                # UPDATE existing SavedAnalysis
                existing_query = select(SavedAnalysis).where(
                    SavedAnalysis.id == queue_item.saved_analysis_id
                )
                existing_result = await db.execute(existing_query)
                saved_analysis = existing_result.scalar_one_or_none()

                if saved_analysis:
                    # Update existing record (preserve created_at)
                    saved_analysis.job_title = queue_item.job_title
                    saved_analysis.company_name = queue_item.company_name
                    saved_analysis.job_description = queue_item.job_text
                    saved_analysis.job_url = queue_item.job_url
                    saved_analysis.eligibility_status = analysis.eligibility_status
                    saved_analysis.eligibility_reasons = analysis.eligibility_reasons
                    saved_analysis.matching_score = final_score
                    saved_analysis.matching_explanation = analysis.matching_explanation
                    saved_analysis.offers_sponsorship = offers_sponsorship
                    saved_analysis.key_requirements = analysis.job_summary.key_requirements
                    saved_analysis.resume_suggestions = [
                        {"section": s.section, "suggestion": s.suggestion, "reason": s.reason}
                        for s in analysis.resume_suggestions
                    ]
                    saved_analysis.ats_keywords = [
                        {"keyword": k.keyword, "found_in_resume": k.found_in_resume, "importance": k.importance}
                        for k in analysis.ats_keywords
                    ]
                    saved_analysis.cover_letter = analysis.cover_letter
                    saved_analysis.processing_time_ms = analysis.processing_time_ms
                    saved_analysis.llm_model = analysis.model_used
                    saved_analysis.last_analyzed_at = datetime.now(timezone.utc)
                    saved_analysis.description_simhash = compute_simhash(queue_item.job_text)
                    logger.info(f"Updated existing SavedAnalysis {saved_analysis.id}")
                else:
                    # Fallback: create new if original was deleted
                    saved_analysis = SavedAnalysis(
                        job_title=queue_item.job_title,
                        company_name=queue_item.company_name,
                        job_description=queue_item.job_text,
                        job_url=queue_item.job_url,
                        eligibility_status=analysis.eligibility_status,
                        eligibility_reasons=analysis.eligibility_reasons,
                        matching_score=final_score,
                        matching_explanation=analysis.matching_explanation,
                        offers_sponsorship=offers_sponsorship,
                        key_requirements=analysis.job_summary.key_requirements,
                        resume_suggestions=[
                            {"section": s.section, "suggestion": s.suggestion, "reason": s.reason}
                            for s in analysis.resume_suggestions
                        ],
                        ats_keywords=[
                            {"keyword": k.keyword, "found_in_resume": k.found_in_resume, "importance": k.importance}
                            for k in analysis.ats_keywords
                        ],
                        cover_letter=analysis.cover_letter,
                        processing_time_ms=analysis.processing_time_ms,
                        llm_model=analysis.model_used,
                        description_simhash=compute_simhash(queue_item.job_text),
                    )
                    db.add(saved_analysis)
                    await db.flush()
                    queue_item.saved_analysis_id = saved_analysis.id
                    logger.info(f"Created new SavedAnalysis {saved_analysis.id} (original was deleted)")
            else:
                # CREATE new SavedAnalysis (existing behavior)
                saved_analysis = SavedAnalysis(
                    job_title=queue_item.job_title,
                    company_name=queue_item.company_name,
                    job_description=queue_item.job_text,
                    job_url=queue_item.job_url,
                    eligibility_status=analysis.eligibility_status,
                    eligibility_reasons=analysis.eligibility_reasons,
                    matching_score=final_score,
                    matching_explanation=analysis.matching_explanation,
                    offers_sponsorship=offers_sponsorship,
                    key_requirements=analysis.job_summary.key_requirements,
                    resume_suggestions=[
                        {"section": s.section, "suggestion": s.suggestion, "reason": s.reason}
                        for s in analysis.resume_suggestions
                    ],
                    ats_keywords=[
                        {"keyword": k.keyword, "found_in_resume": k.found_in_resume, "importance": k.importance}
                        for k in analysis.ats_keywords
                    ],
                    cover_letter=analysis.cover_letter,
                    processing_time_ms=analysis.processing_time_ms,
                    llm_model=analysis.model_used,
                    description_simhash=compute_simhash(queue_item.job_text),
                )
                db.add(saved_analysis)
                await db.flush()
                queue_item.saved_analysis_id = saved_analysis.id

            # Remove completed item from queue
            await db.delete(queue_item)
            await db.commit()

            logger.info(f"Queue item {queue_item_id} completed successfully")
            return {
                "queue_item_id": queue_item_id,
                "status": "completed",
                "saved_analysis_id": saved_analysis.id,
            }

        except Exception as e:
            logger.error(f"Analysis failed for queue item {queue_item_id}: {e}")

            # Check if we can retry
            if queue_item.retry_count < queue_item.max_retries:
                queue_item.retry_count += 1
                queue_item.status = QueueItemStatus.PENDING.value
                queue_item.error_message = f"Retry {queue_item.retry_count}/{queue_item.max_retries}: {str(e)}"
                queue_item.started_at = None
                queue_item.completed_at = None
                await db.commit()

                logger.info(
                    f"Queue item {queue_item_id} scheduled for retry "
                    f"({queue_item.retry_count}/{queue_item.max_retries})"
                )

                # Schedule retry with exponential backoff
                base_delay = settings.queue_retry_base_delay
                delay_seconds = base_delay * (2 ** (queue_item.retry_count - 1))
                process_queue_item.apply_async(
                    args=[queue_item_id],
                    countdown=delay_seconds,
                )

                return {
                    "queue_item_id": queue_item_id,
                    "status": "retry_scheduled",
                    "retry_count": queue_item.retry_count,
                    "max_retries": queue_item.max_retries,
                    "retry_delay_seconds": delay_seconds,
                    "error": str(e),
                }
            else:
                # Max retries reached, mark as failed
                queue_item.status = QueueItemStatus.FAILED.value
                queue_item.error_message = f"Failed after {queue_item.max_retries} retries: {str(e)}"
                queue_item.completed_at = datetime.now(timezone.utc)
                await db.commit()

                logger.error(
                    f"Queue item {queue_item_id} permanently failed after "
                    f"{queue_item.max_retries} retries"
                )

                return {"error": str(e), "retries_exhausted": True}


@celery_app.task(name="workers.tasks.analyzer_queue.process_queue_item")
def process_queue_item(queue_item_id: int) -> dict:
    return asyncio.run(_process_queue_item_async(queue_item_id))


async def _recover_stale_tasks_async():
    """Detect and reset queue items stuck in processing."""
    AsyncSessionLocal = get_async_session()
    async with AsyncSessionLocal() as db:
        prefs_query = select(UserPreferences).limit(1)
        prefs_result = await db.execute(prefs_query)
        prefs = prefs_result.scalar_one_or_none()
        timeout_minutes = prefs.stale_task_timeout_minutes if prefs and prefs.stale_task_timeout_minutes else 10

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=timeout_minutes)
        stale_query = select(AnalysisQueueItem).where(
            AnalysisQueueItem.status == QueueItemStatus.PROCESSING.value,
            AnalysisQueueItem.started_at < cutoff,
        )
        result = await db.execute(stale_query)
        stale_items = result.scalars().all()

        for item in stale_items:
            logger.warning(f"Resetting stale queue item {item.id} (processing since {item.started_at})")
            item.status = QueueItemStatus.PENDING.value
            item.started_at = None
            item.celery_task_id = None

        if stale_items:
            await db.commit()
            logger.info(f"Recovered {len(stale_items)} stale queue items")


@celery_app.task(name="workers.tasks.analyzer_queue.recover_stale_tasks")
def recover_stale_tasks():
    return asyncio.run(_recover_stale_tasks_async())
