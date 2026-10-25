from fastapi import APIRouter, Depends, HTTPException
from telecopilot.core.logger import get_logger
from telecopilot.models.api_models import ManualScrapeRequest
from telecopilot.services.ingestion_service import IngestionService
from telecopilot.dependencies import get_ingestion_service

logger = get_logger()
router = APIRouter(prefix="/api/scraper", tags=["Manual Scraper"])


@router.post("/run")
async def run_manual_scraper(
    request: ManualScrapeRequest,
    service: IngestionService = Depends(get_ingestion_service)
):
    """
    Manually triggers in-memory scraping of any URL (such as https://www.te.eg/),
    and indexes all sections into Qdrant directly without writing to disk.
    """
    logger.info(f"Manual Scraper API called for URL: {request.url}")
    try:
        result = service.ingest_url(request.url)
        return {
            "status": "SUCCESS",
            "scraped_url": request.url,
            "indexed_chunks": result.get("chunks_count"),
            "document_title": result.get("document_title"),
            "message": f"Successfully scraped {request.url} in-memory and ingested into Qdrant vector store."
        }
    except Exception as e:
        logger.error(f"Manual scraper failed for {request.url}: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to scrape {request.url}: {str(e)}")
