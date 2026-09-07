from controllers.agent_assist_controller import router as agent_assist_router
from controllers.ingest_controller import router as ingest_router
from controllers.health_controller import router as health_router
from controllers.scraper_controller import router as scraper_router
from controllers.document_download_controller import router as download_router

__all__ = ["agent_assist_router", "ingest_router", "health_router", "scraper_router", "download_router"]
