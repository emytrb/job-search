from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models.saved_analysis import SavedAnalysis
from app.models.digest import Digest
from app.schemas.digest import DigestPreview, DigestResponse
from app.core.config import settings

router = APIRouter()


@router.get("/preview", response_model=DigestPreview)
async def preview_digest(db: AsyncSession = Depends(get_db)):
    """Preview the next digest with top analyzed jobs."""
    query = (
        select(SavedAnalysis)
        .where(SavedAnalysis.eligibility_status.in_(["eligible", "partially_eligible"]))
        .order_by(desc(SavedAnalysis.matching_score))
        .limit(settings.digest_max_jobs)
    )
    result = await db.execute(query)
    analyses = result.scalars().all()

    return DigestPreview(
        job_count=len(analyses),
        jobs=[
            {
                "id": a.id,
                "title": a.job_title,
                "company": a.company_name,
                "score": a.matching_score,
            }
            for a in analyses
        ],
    )


@router.post("/send")
async def send_digest(db: AsyncSession = Depends(get_db)):
    """Trigger sending a digest email."""
    from workers.tasks.digest import send_daily_digest

    task = send_daily_digest.delay()
    return {"status": "triggered", "task_id": task.id}


@router.get("/history", response_model=list[DigestResponse])
async def list_digests(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """List recent digest emails."""
    query = select(Digest).order_by(Digest.sent_at.desc()).limit(limit)
    result = await db.execute(query)
    digests = result.scalars().all()
    return [DigestResponse.model_validate(d) for d in digests]
