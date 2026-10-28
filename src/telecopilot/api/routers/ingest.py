from fastapi import APIRouter, Depends, HTTPException

from telecopilot.api.dependencies import get_ingestion_service
from telecopilot.api.schemas import ScrapeUrlRequest
from telecopilot.core.logger import get_logger
from telecopilot.kb.ingestion_service import IngestionService

logger = get_logger()
router = APIRouter(prefix="/api/ingest", tags=["Ingestion"])


@router.post("/all")
async def ingest_all_policies(service: IngestionService = Depends(get_ingestion_service)):
    """Triggers in-memory scraping and indexing of all default online Telecom Egypt web pages."""
    try:
        results = service.ingest_all_default_policies()
        return {
            "message": "Live online website ingestion completed in-memory without local files.",
            "pages_scraped": len(results),
            "details": results,
        }
    except Exception as e:
        logger.error(f"Live web ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/scrape-url")
async def scrape_and_ingest_url(request: ScrapeUrlRequest, service: IngestionService = Depends(get_ingestion_service)):
    """
    Live in-memory Web Scraper endpoint:
    Fetches real-time web pages directly over HTTP, chunks content in-memory,
    and indexes into Qdrant vector database (Zero local files created).
    """
    try:
        result = service.ingest_url(request.url)
        return {"message": "Web page successfully scraped in-memory and indexed into Qdrant.", "details": result}
    except Exception as e:
        logger.error(f"Web scraper ingestion failed for {request.url}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
