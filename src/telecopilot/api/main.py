from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from telecopilot.api.routers import assist, documents, health, ingest, scraper
from telecopilot.config.settings import get_settings
from telecopilot.core.logger import configure_logging, get_logger

logger = get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start-up only configures logging; indexing runs separately (python -m telecopilot.kb.ingest --all)."""
    configure_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode...")
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
for module in (assist, ingest, health, scraper, documents):
    app.include_router(module.router)

# Mount the v1 static UI (replaced by the Reflex app in M1)
if settings.STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=settings.STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("telecopilot.api.main:app", host=settings.HOST, port=settings.PORT, reload=True)
