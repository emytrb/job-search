from fastapi import APIRouter

from app.api.v1.endpoints import jobs, sources, digest, preferences, analyzer

api_router = APIRouter()

api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(digest.router, prefix="/digest", tags=["digest"])
api_router.include_router(preferences.router, prefix="/preferences", tags=["preferences"])
api_router.include_router(analyzer.router, prefix="/analyzer", tags=["analyzer"])
