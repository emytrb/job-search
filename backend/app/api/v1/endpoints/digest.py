from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.job import Job, JobStatus
from app.models.job_score import JobScore
from app.models.digest import Digest
from app.schemas.digest import DigestPreview, DigestResponse
from app.core.config import settings

router = APIRouter()


@router.get("/preview", response_model=DigestPreview)
async def preview_digest(db: AsyncSession = Depends(get_db)):
    query = (
        select(Job)
        .join(JobScore)
        .where(Job.status == JobStatus.SCORED)
        .order_by(JobScore.total_score.desc())
        .limit(settings.digest_max_jobs)
    )
    result = await db.execute(query)
    jobs = result.scalars().all()

    return DigestPreview(
        job_count=len(jobs),
        jobs=[
            {
                "id": j.id,
                "title": j.title,
                "company": j.company_name,
                "score": j.score.total_score if j.score else 0,
            }
            for j in jobs
        ],
    )


@router.post("/send")
async def send_digest(db: AsyncSession = Depends(get_db)):
    from workers.tasks.digest import send_daily_digest

    task = send_daily_digest.delay()
    return {"status": "triggered", "task_id": task.id}


@router.get("/history", response_model=list[DigestResponse])
async def list_digests(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    query = select(Digest).order_by(Digest.sent_at.desc()).limit(limit)
    result = await db.execute(query)
    digests = result.scalars().all()
    return [DigestResponse.model_validate(d) for d in digests]
