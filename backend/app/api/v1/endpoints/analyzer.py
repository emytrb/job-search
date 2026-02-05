from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import joinedload

from app.db.session import get_db
from app.models.user_preferences import UserPreferences
from app.models.saved_analysis import SavedAnalysis
from app.models.analysis_queue import AnalysisQueueItem, QueueItemStatus
from app.schemas.analyzer import (
    AnalyzeRequest,
    ResumeSuggestionResponse,
    ATSKeywordResponse,
    SavedAnalysisResponse,
    SavedAnalysisListItem,
    SavedAnalysisListResponse,
    QueueItemResponse,
    QueueStatusResponse,
    QueueAddResponse,
    RequeueRequest,
    RequeueResponse,
)
from workers.tasks.analyzer_queue import process_queue_item

router = APIRouter()


def build_queue_item_response(item: AnalysisQueueItem) -> QueueItemResponse:
    """Build a QueueItemResponse from an AnalysisQueueItem."""
    return QueueItemResponse(
        id=item.id,
        job_text_preview=item.job_text[:100] + "..." if len(item.job_text) > 100 else item.job_text,
        job_url=item.job_url,
        status=item.status,
        error_message=item.error_message,
        saved_analysis_id=item.saved_analysis_id,
        job_title=item.saved_analysis.job_title if item.saved_analysis else None,
        company_name=item.saved_analysis.company_name if item.saved_analysis else None,
        matching_score=item.saved_analysis.matching_score if item.saved_analysis else None,
        created_at=item.created_at,
        started_at=item.started_at,
        completed_at=item.completed_at,
    )


@router.post("/analyze", response_model=QueueAddResponse)
async def add_to_queue(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a job to the analysis queue."""
    # Check if CV is set
    query = select(UserPreferences).limit(1)
    result = await db.execute(query)
    prefs = result.scalar_one_or_none()

    if not prefs or not prefs.cv_text or not prefs.cv_text.strip():
        raise HTTPException(
            status_code=422,
            detail="CV text is required. Please set your CV in Settings first.",
        )

    # Create queue item
    queue_item = AnalysisQueueItem(
        job_text=request.job_text,
        job_url=request.job_url,
        status=QueueItemStatus.PENDING.value,
    )
    db.add(queue_item)
    await db.commit()
    await db.refresh(queue_item)

    # Count position in queue
    position_query = select(func.count(AnalysisQueueItem.id)).where(
        AnalysisQueueItem.status.in_([QueueItemStatus.PENDING.value, QueueItemStatus.PROCESSING.value]),
        AnalysisQueueItem.id <= queue_item.id,
    )
    position_result = await db.execute(position_query)
    position = position_result.scalar()

    # Check if there's already a processing item
    processing_query = select(AnalysisQueueItem).where(
        AnalysisQueueItem.status == QueueItemStatus.PROCESSING.value
    )
    processing_result = await db.execute(processing_query)
    processing_item = processing_result.scalar_one_or_none()

    # If no item is processing, start this one
    if not processing_item:
        queue_item.status = QueueItemStatus.PROCESSING.value
        queue_item.started_at = datetime.now(timezone.utc)
        await db.commit()

        # Dispatch Celery task
        task = process_queue_item.delay(queue_item.id)
        queue_item.celery_task_id = task.id
        await db.commit()

    return QueueAddResponse(
        id=queue_item.id,
        status=queue_item.status,
        position=position,
    )


@router.get("/queue", response_model=QueueStatusResponse)
async def get_queue_status(
    db: AsyncSession = Depends(get_db),
):
    """Get the current queue status."""
    # Get all queue items (recent first, limit to last 50)
    query = (
        select(AnalysisQueueItem)
        .options(joinedload(AnalysisQueueItem.saved_analysis))
        .order_by(desc(AnalysisQueueItem.created_at))
        .limit(50)
    )
    result = await db.execute(query)
    items = result.unique().scalars().all()

    # Count by status
    pending_count = sum(1 for i in items if i.status == QueueItemStatus.PENDING.value)
    processing_count = sum(1 for i in items if i.status == QueueItemStatus.PROCESSING.value)
    completed_count = sum(1 for i in items if i.status == QueueItemStatus.COMPLETED.value)
    failed_count = sum(1 for i in items if i.status == QueueItemStatus.FAILED.value)

    # Check if we need to start processing the next item
    if processing_count == 0 and pending_count > 0:
        # Find the oldest pending item
        next_item_query = (
            select(AnalysisQueueItem)
            .where(AnalysisQueueItem.status == QueueItemStatus.PENDING.value)
            .order_by(AnalysisQueueItem.created_at)
            .limit(1)
        )
        next_result = await db.execute(next_item_query)
        next_item = next_result.scalar_one_or_none()

        if next_item:
            next_item.status = QueueItemStatus.PROCESSING.value
            next_item.started_at = datetime.now(timezone.utc)
            await db.commit()

            # Dispatch Celery task
            task = process_queue_item.delay(next_item.id)
            next_item.celery_task_id = task.id
            await db.commit()

            # Refresh the items list
            result = await db.execute(query)
            items = result.unique().scalars().all()
            processing_count = 1
            pending_count -= 1

    return QueueStatusResponse(
        items=[build_queue_item_response(item) for item in items],
        pending_count=pending_count,
        processing_count=processing_count,
        completed_count=completed_count,
        failed_count=failed_count,
    )


@router.delete("/queue/{item_id}")
async def remove_from_queue(
    item_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove an item from the queue."""
    query = select(AnalysisQueueItem).where(AnalysisQueueItem.id == item_id)
    result = await db.execute(query)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    # Don't allow removing processing items
    if item.status == QueueItemStatus.PROCESSING.value:
        raise HTTPException(status_code=400, detail="Cannot remove item that is currently processing")

    await db.delete(item)
    await db.commit()

    return {"status": "deleted"}


@router.post("/requeue", response_model=RequeueResponse)
async def requeue_analyses(
    request: RequeueRequest,
    db: AsyncSession = Depends(get_db),
):
    """Requeue saved analyses for re-analysis. The new analysis will overwrite the existing record."""
    # Check if CV is set
    query = select(UserPreferences).limit(1)
    result = await db.execute(query)
    prefs = result.scalar_one_or_none()

    if not prefs or not prefs.cv_text or not prefs.cv_text.strip():
        raise HTTPException(
            status_code=422,
            detail="CV text is required. Please set your CV in Settings first.",
        )

    # Fetch all requested saved analyses
    analyses_query = select(SavedAnalysis).where(SavedAnalysis.id.in_(request.analysis_ids))
    analyses_result = await db.execute(analyses_query)
    analyses = {a.id: a for a in analyses_result.scalars().all()}

    # Check for missing analyses
    missing_ids = set(request.analysis_ids) - set(analyses.keys())
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Analyses not found: {sorted(missing_ids)}",
        )

    # Check if any are currently processing
    processing_query = select(AnalysisQueueItem).where(
        AnalysisQueueItem.status == QueueItemStatus.PROCESSING.value
    )
    processing_result = await db.execute(processing_query)
    processing_item = processing_result.scalar_one_or_none()

    queue_items = []
    for analysis_id in request.analysis_ids:
        analysis = analyses[analysis_id]

        # Create queue item with saved_analysis_id pre-set (for overwrite mode)
        queue_item = AnalysisQueueItem(
            job_text=analysis.job_description,
            job_url=analysis.job_url,
            status=QueueItemStatus.PENDING.value,
            saved_analysis_id=analysis_id,  # Key for overwrite mode
        )
        db.add(queue_item)
        await db.flush()

        # Count position in queue
        position_query = select(func.count(AnalysisQueueItem.id)).where(
            AnalysisQueueItem.status.in_([QueueItemStatus.PENDING.value, QueueItemStatus.PROCESSING.value]),
            AnalysisQueueItem.id <= queue_item.id,
        )
        position_result = await db.execute(position_query)
        position = position_result.scalar()

        queue_items.append(QueueAddResponse(
            id=queue_item.id,
            status=queue_item.status,
            position=position,
        ))

    await db.commit()

    # If no item is processing, start the first one
    if not processing_item and queue_items:
        first_item_query = select(AnalysisQueueItem).where(
            AnalysisQueueItem.id == queue_items[0].id
        )
        first_result = await db.execute(first_item_query)
        first_item = first_result.scalar_one()

        first_item.status = QueueItemStatus.PROCESSING.value
        first_item.started_at = datetime.now(timezone.utc)
        await db.commit()

        # Dispatch Celery task
        task = process_queue_item.delay(first_item.id)
        first_item.celery_task_id = task.id
        await db.commit()

        # Update response status
        queue_items[0] = QueueAddResponse(
            id=first_item.id,
            status=first_item.status,
            position=1,
        )

    return RequeueResponse(
        queued_count=len(queue_items),
        queue_items=queue_items,
    )


# Saved analyses endpoints (unchanged)

@router.get("/saved", response_model=SavedAnalysisListResponse)
async def list_saved_analyses(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    # Get total count
    count_query = select(func.count(SavedAnalysis.id))
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Get analyses
    query = (
        select(SavedAnalysis)
        .order_by(desc(SavedAnalysis.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    analyses = result.scalars().all()

    return SavedAnalysisListResponse(
        analyses=[
            SavedAnalysisListItem(
                id=a.id,
                job_title=a.job_title,
                company_name=a.company_name,
                eligibility_status=a.eligibility_status,
                matching_score=a.matching_score,
                created_at=a.created_at,
            )
            for a in analyses
        ],
        total=total,
    )


@router.get("/saved/{analysis_id}", response_model=SavedAnalysisResponse)
async def get_saved_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = select(SavedAnalysis).where(SavedAnalysis.id == analysis_id)
    result = await db.execute(query)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    return SavedAnalysisResponse(
        id=analysis.id,
        job_title=analysis.job_title,
        company_name=analysis.company_name,
        job_description=analysis.job_description,
        job_url=analysis.job_url,
        eligibility_status=analysis.eligibility_status,
        eligibility_reasons=analysis.eligibility_reasons,
        matching_score=analysis.matching_score,
        matching_explanation=analysis.matching_explanation,
        key_requirements=analysis.key_requirements,
        resume_suggestions=[
            ResumeSuggestionResponse(**s) for s in analysis.resume_suggestions
        ],
        ats_keywords=[
            ATSKeywordResponse(**k) for k in analysis.ats_keywords
        ],
        cover_letter=analysis.cover_letter,
        processing_time_ms=analysis.processing_time_ms,
        created_at=analysis.created_at,
    )


@router.delete("/saved/{analysis_id}")
async def delete_saved_analysis(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
):
    query = select(SavedAnalysis).where(SavedAnalysis.id == analysis_id)
    result = await db.execute(query)
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    await db.delete(analysis)
    await db.commit()

    return {"status": "deleted"}
