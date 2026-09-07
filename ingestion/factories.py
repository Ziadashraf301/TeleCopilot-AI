import os
from core.logger import get_logger
from ingestion.base import BaseExtractor, BaseChunker
from ingestion.extractors.html_extractor import HTMLExtractor
from ingestion.extractors.gemini_ocr_extractor import GeminiOCRExtractor
from ingestion.extractors.docx_extractor import DocxExtractor
from ingestion.extractors.web_scraper_extractor import WebScraperExtractor
from ingestion.chunkers.policy_chunkers import (
    SIMPolicyChunker,
    WifiPolicyChunker,
    BillingPolicyChunker,
    WebScrapedPolicyChunker,
)

logger = get_logger()


class ExtractorFactory:
    """
    Factory Pattern for dynamically instantiating the appropriate Document Extractor
    based on live URL protocol (HTTP/HTTPS) or local file extension.
    """

    @staticmethod
    def get_extractor(file_path_or_url: str) -> BaseExtractor:
        # Check if live HTTP/HTTPS Web URL
        if file_path_or_url.startswith("http://") or file_path_or_url.startswith("https://"):
            logger.info(f"ExtractorFactory resolved WebScraperExtractor for URL: {file_path_or_url}")
            return WebScraperExtractor()

        ext = os.path.splitext(file_path_or_url)[1].lower()
        if ext in [".html", ".htm"]:
            logger.info(f"ExtractorFactory resolved HTMLExtractor for {file_path_or_url}")
            return HTMLExtractor()
        elif ext == ".pdf":
            logger.info(f"ExtractorFactory resolved GeminiOCRExtractor for {file_path_or_url}")
            return GeminiOCRExtractor()
        elif ext in [".docx", ".doc"]:
            logger.info(f"ExtractorFactory resolved DocxExtractor for {file_path_or_url}")
            return DocxExtractor()
        else:
            raise ValueError(f"Unsupported format for ingestion: {ext or file_path_or_url}")


class ChunkerFactory:
    """
    Factory Pattern for dynamically instantiating the specialized policy chunker.
    """

    @staticmethod
    def get_chunker(policy_type: str) -> BaseChunker:
        if policy_type == "sim_replacement":
            return SIMPolicyChunker()
        elif policy_type == "wifi_troubleshooting":
            return WifiPolicyChunker()
        elif policy_type == "billing_refund":
            return BillingPolicyChunker()
        elif policy_type in ["web_scraped_policy", "telecom_egypt_web"]:
            return WebScrapedPolicyChunker()
        else:
            logger.warning(f"Unknown policy type '{policy_type}', defaulting to WebScrapedPolicyChunker")
            return WebScrapedPolicyChunker()
