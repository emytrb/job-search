from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.scrape_source import ScrapeSource, RiskLevel
from app.models.scrape_run import ScrapeRun
from app.schemas.source import (
    ScrapeSourceCreate,
    ScrapeSourceUpdate,
    ScrapeSourceResponse,
    ScrapeRunResponse,
)

router = APIRouter()


@router.get("", response_model=list[ScrapeSourceResponse])
async def list_sources(db: AsyncSession = Depends(get_db)):
    query = select(ScrapeSource).order_by(ScrapeSource.created_at.desc())
    result = await db.execute(query)
    sources = result.scalars().all()
    return [ScrapeSourceResponse.model_validate(s) for s in sources]


@router.post("", response_model=ScrapeSourceResponse)
async def create_source(
    source: ScrapeSourceCreate,
    db: AsyncSession = Depends(get_db),
):
    db_source = ScrapeSource(
        name=source.name,
        source_type=source.source_type,
        base_url=source.base_url,
        risk_level=source.risk_level,
        config=source.config or {},
        enabled=source.enabled,
    )
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)
    return ScrapeSourceResponse.model_validate(db_source)


@router.get("/{source_id}", response_model=ScrapeSourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ScrapeSource).where(ScrapeSource.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    return ScrapeSourceResponse.model_validate(source)


@router.put("/{source_id}", response_model=ScrapeSourceResponse)
async def update_source(
    source_id: int,
    source_update: ScrapeSourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    query = select(ScrapeSource).where(ScrapeSource.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return ScrapeSourceResponse.model_validate(source)


@router.delete("/{source_id}")
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ScrapeSource).where(ScrapeSource.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    await db.delete(source)
    await db.commit()

    return {"status": "deleted"}


@router.post("/{source_id}/scrape")
async def trigger_scrape(source_id: int, db: AsyncSession = Depends(get_db)):
    query = select(ScrapeSource).where(ScrapeSource.id == source_id)
    result = await db.execute(query)
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    from workers.tasks.scraping import scrape_source

    task = scrape_source.delay(source_id)

    return {"status": "triggered", "task_id": task.id}


@router.get("/{source_id}/runs", response_model=list[ScrapeRunResponse])
async def list_source_runs(
    source_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(ScrapeRun)
        .where(ScrapeRun.source_id == source_id)
        .order_by(ScrapeRun.started_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    runs = result.scalars().all()
    return [ScrapeRunResponse.model_validate(r) for r in runs]
