import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from workers.celery_app import celery_app
from app.core.config import settings
from app.models.analysis_queue import AnalysisQueueItem, QueueItemStatus
from app.models.saved_analysis import SavedAnalysis
from app.models.user_preferences import UserPreferences
from llm.client import llm_client

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
                    saved_analysis.job_title = analysis.job_summary.title
                    saved_analysis.company_name = analysis.job_summary.company
                    saved_analysis.job_description = queue_item.job_text
                    saved_analysis.job_url = queue_item.job_url
                    saved_analysis.eligibility_status = analysis.eligibility_status
                    saved_analysis.eligibility_reasons = analysis.eligibility_reasons
                    saved_analysis.matching_score = analysis.matching_score
                    saved_analysis.matching_explanation = analysis.matching_explanation
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
                    logger.info(f"Updated existing SavedAnalysis {saved_analysis.id}")
                else:
                    # Fallback: create new if original was deleted
                    saved_analysis = SavedAnalysis(
                        job_title=analysis.job_summary.title,
                        company_name=analysis.job_summary.company,
                        job_description=queue_item.job_text,
                        job_url=queue_item.job_url,
                        eligibility_status=analysis.eligibility_status,
                        eligibility_reasons=analysis.eligibility_reasons,
                        matching_score=analysis.matching_score,
                        matching_explanation=analysis.matching_explanation,
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
                    )
                    db.add(saved_analysis)
                    await db.flush()
                    queue_item.saved_analysis_id = saved_analysis.id
                    logger.info(f"Created new SavedAnalysis {saved_analysis.id} (original was deleted)")
            else:
                # CREATE new SavedAnalysis (existing behavior)
                saved_analysis = SavedAnalysis(
                    job_title=analysis.job_summary.title,
                    company_name=analysis.job_summary.company,
                    job_description=queue_item.job_text,
                    job_url=queue_item.job_url,
                    eligibility_status=analysis.eligibility_status,
                    eligibility_reasons=analysis.eligibility_reasons,
                    matching_score=analysis.matching_score,
                    matching_explanation=analysis.matching_explanation,
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
                )
                db.add(saved_analysis)
                await db.flush()
                queue_item.saved_analysis_id = saved_analysis.id

            # Update queue item
            queue_item.status = QueueItemStatus.COMPLETED.value
            queue_item.completed_at = datetime.now(timezone.utc)
            await db.commit()

            logger.info(f"Queue item {queue_item_id} completed successfully")
            return {
                "queue_item_id": queue_item_id,
                "status": "completed",
                "saved_analysis_id": saved_analysis.id,
            }

        except Exception as e:
            logger.error(f"Analysis failed for queue item {queue_item_id}: {e}")
            queue_item.status = QueueItemStatus.FAILED.value
            queue_item.error_message = str(e)
            queue_item.completed_at = datetime.now(timezone.utc)
            await db.commit()
            return {"error": str(e)}


@celery_app.task(name="workers.tasks.analyzer_queue.process_queue_item")
def process_queue_item(queue_item_id: int) -> dict:
    return asyncio.run(_process_queue_item_async(queue_item_id))
