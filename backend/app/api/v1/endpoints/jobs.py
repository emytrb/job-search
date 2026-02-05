from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.session import get_db
from app.models.job import Job, JobStatus
from app.models.llm_analysis import LLMAnalysis
from app.models.job_score import JobScore
from app.schemas.job import JobResponse, JobListResponse, JobDetail

router = APIRouter()


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    min_score: Optional[float] = Query(None, ge=0, le=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Job)

    if status:
        query = query.where(Job.status == status)
    else:
        query = query.where(Job.status == JobStatus.SCORED)

    if min_score is not None:
        query = query.join(JobScore).where(JobScore.total_score >= min_score)

    query = query.order_by(Job.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    count_query = select(func.count(Job.id))
    if status:
        count_query = count_query.where(Job.status == status)
    else:
        count_query = count_query.where(Job.status == JobStatus.SCORED)

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    return JobListResponse(
        jobs=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobDetail)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    analysis_query = select(LLMAnalysis).where(LLMAnalysis.job_id == job_id)
    analysis_result = await db.execute(analysis_query)
    analysis = analysis_result.scalar_one_or_none()

    score_query = select(JobScore).where(JobScore.job_id == job_id)
    score_result = await db.execute(score_query)
    score = score_result.scalar_one_or_none()

    return JobDetail(
        job=JobResponse.model_validate(job),
        analysis=analysis,
        score=score,
    )


@router.post("/{job_id}/dismiss")
async def dismiss_job(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.DISMISSED
    await db.commit()

    return {"status": "dismissed"}


@router.post("/{job_id}/apply")
async def mark_applied(job_id: int, db: AsyncSession = Depends(get_db)):
    query = select(Job).where(Job.id == job_id)
    result = await db.execute(query)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job.status = JobStatus.APPLIED
    await db.commit()

    return {"status": "applied"}
