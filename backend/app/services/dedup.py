import hashlib
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job import Job


def compute_dedup_hash(company_name: str, title: str, location: Optional[str] = None) -> str:
    content = f"{company_name.lower().strip()}|{title.lower().strip()}|{(location or '').lower().strip()}"
    return hashlib.sha256(content.encode()).hexdigest()[:32]


async def job_exists(db: AsyncSession, dedup_hash: str) -> bool:
    query = select(Job.id).where(Job.dedup_hash == dedup_hash).limit(1)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None


async def get_existing_job(db: AsyncSession, dedup_hash: str) -> Optional[Job]:
    query = select(Job).where(Job.dedup_hash == dedup_hash)
    result = await db.execute(query)
    return result.scalar_one_or_none()
