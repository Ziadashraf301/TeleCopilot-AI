from fastapi import APIRouter, Depends
from config.settings import get_settings
from repositories.base import BaseVectorRepository
from dependencies import get_vector_repository

router = APIRouter(prefix="/api/health", tags=["Health"])
settings = get_settings()


@router.get("")
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
            "live_connection": getattr(repo, "_is_live", False)
        },
        "providers": {
            "cohere": bool(settings.COHERE_API_KEY),
            "gemini": bool(settings.GEMINI_API_KEY),
            "langfuse": bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)
        }
    }
