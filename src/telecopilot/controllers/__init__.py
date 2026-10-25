from telecopilot.controllers.agent_assist_controller import router as agent_assist_router
from telecopilot.controllers.ingest_controller import router as ingest_router
from telecopilot.controllers.health_controller import router as health_router
from telecopilot.controllers.scraper_controller import router as scraper_router
from telecopilot.controllers.document_download_controller import router as download_router

__all__ = ["agent_assist_router", "ingest_router", "health_router", "scraper_router", "download_router"]
