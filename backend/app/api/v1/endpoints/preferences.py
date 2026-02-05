from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.user_preferences import UserPreferences
from app.schemas.preferences import UserPreferencesCreate, UserPreferencesResponse

router = APIRouter()


@router.get("", response_model=UserPreferencesResponse)
async def get_preferences(db: AsyncSession = Depends(get_db)):
    query = select(UserPreferences).limit(1)
    result = await db.execute(query)
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(
            cv_text="",
            target_stack=[],
            target_seniority="mid",
            target_location="London, UK",
            digest_enabled=True,
            digest_hour_utc=8,
            ats_guidelines="",
            job_requirements_context="",
            cover_letter_guidelines="",
        )
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return UserPreferencesResponse.model_validate(prefs)


@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(
    prefs_update: UserPreferencesCreate,
    db: AsyncSession = Depends(get_db),
):
    query = select(UserPreferences).limit(1)
    result = await db.execute(query)
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(**prefs_update.model_dump())
        db.add(prefs)
    else:
        update_data = prefs_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prefs, field, value)

    await db.commit()
    await db.refresh(prefs)
    return UserPreferencesResponse.model_validate(prefs)
