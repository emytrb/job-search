from fastapi import APIRouter

from app.api.v1.endpoints import digest, preferences, analyzer

api_router = APIRouter()

api_router.include_router(digest.router, prefix="/digest", tags=["digest"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(analyzer.router, prefix="/analyzer", tags=["analyzer"])
