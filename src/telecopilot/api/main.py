import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from telecopilot.config.settings import get_settings
from telecopilot.controllers import agent_assist_router, download_router, health_router, ingest_router, scraper_router
from telecopilot.core.logger import get_logger
from telecopilot.services.ingestion_service import IngestionService

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
        from telecopilot.dependencies.dependencies import get_cohere_service, get_vector_repository

        repo = get_vector_repository()
        cohere_svc = get_cohere_service()
        ingestion_svc = IngestionService(repo, cohere_svc)

        logger.info("Automatically scraping website content from https://www.te.eg/ and portal pages into Qdrant...")

        if repo.count() > 0:
            logger.info("Qdrant collection already populated. Skipping startup ingestion.")
        else:
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
    lifespan=lifespan,
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

# Mount Static UI Files (resolving project root static directory)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "static"))
if not os.path.exists(static_dir):
    static_dir = os.path.abspath("static")

if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("telecopilot.api.main:app", host=settings.HOST, port=settings.PORT, reload=True)
