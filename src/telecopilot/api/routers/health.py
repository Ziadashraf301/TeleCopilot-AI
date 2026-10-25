from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from telecopilot.api.dependencies import get_readiness_checks, get_vector_repository
from telecopilot.api.readiness import ReadinessCheck, check_readiness
from telecopilot.config.settings import get_settings
from telecopilot.kb.repositories.base import BaseVectorRepository

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/api/health")
async def health_check(repo: BaseVectorRepository = Depends(get_vector_repository)):
    """System health check verifying API and Vector DB status."""
    vector_count = repo.count()
    return {
        "status": "HEALTHY",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "vector_store": {
            "collection": settings.QDRANT_COLLECTION,
            "indexed_chunks_count": vector_count,
            "live_connection": True,  # the repository raises when Qdrant is unreachable, so reaching here means live
        },
        "providers": {
            "cohere": bool(settings.COHERE_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "langfuse": bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY),
        },
    }


@router.get("/api/ready")
def readiness_check(checks: dict[str, ReadinessCheck] = Depends(get_readiness_checks)) -> JSONResponse:
    """200 when Qdrant, Postgres and Redis are reachable, else 503 with the failing check(s). Sync: checks block."""
    ready, body = check_readiness(checks)
    return JSONResponse(status_code=200 if ready else 503, content=body)
