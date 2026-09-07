import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from config.settings import get_settings
from core.logger import get_logger
from controllers import (
    agent_assist_router,
    ingest_router,
    health_router,
    scraper_router,
    download_router
)
from services.ingestion_service import IngestionService
from services.cohere_service import CohereService
from repositories.qdrant_repository import QdrantVectorRepository

logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Bootstrap application lifecycle:
    Scrapes the live website pages and ingests all documents into Qdrant.
    """
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
    try:
        from dependencies.dependencies import get_vector_repository, get_cohere_service
        repo = get_vector_repository()
        cohere_svc = get_cohere_service()
        ingestion_svc = IngestionService(repo, cohere_svc)

        logger.info("Automatically scraping website content from https://www.te.eg/ and portal pages into Qdrant...")
        results = ingestion_svc.ingest_all_default_policies()
        logger.info(f"Website & policy ingestion finished: {len(results)} sources indexed in Qdrant.")
    except Exception as e:
        logger.warning(f"Startup website scraping notice: {e}")
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Enterprise AI Customer Support Portal & Copilot with live web scraping, document downloads, Qdrant, Cohere, Gemini, and Langfuse.",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Controller Routers
app.include_router(agent_assist_router)
app.include_router(ingest_router)
app.include_router(health_router)
app.include_router(scraper_router)
app.include_router(download_router)

# Mount Static UI Files
if os.path.exists("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.main:app", host=settings.HOST, port=settings.PORT, reload=True)
