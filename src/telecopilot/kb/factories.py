import os

from telecopilot.core.logger import get_logger
from telecopilot.kb.base import BaseChunker, BaseExtractor
from telecopilot.kb.chunkers.policy_chunkers import (
    BillingPolicyChunker,
    SIMPolicyChunker,
    WebScrapedPolicyChunker,
    WifiPolicyChunker,
    XMLPolicyChunker,
)
from telecopilot.kb.extractors.docx_extractor import DocxExtractor
from telecopilot.kb.extractors.gemini_ocr_extractor import GeminiOCRExtractor
from telecopilot.kb.extractors.html_extractor import HTMLExtractor
from telecopilot.kb.extractors.web_scraper_extractor import WebScraperExtractor
from telecopilot.kb.extractors.xml_extractor import XMLExtractor

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
        elif ext == ".xml":
            logger.info(f"ExtractorFactory resolved XMLExtractor for {file_path_or_url}")
            return XMLExtractor()
        else:
            raise ValueError(f"Unsupported format for ingestion: {ext or file_path_or_url}")


class ChunkerFactory:
    """
    Factory Pattern for dynamically instantiating the specialized policy chunker.
    """

    @staticmethod
    def get_chunker(policy_type: str, file_path_or_url: str = None) -> BaseChunker:
        p = (policy_type or "").lower()
        if file_path_or_url:
            ext = os.path.splitext(file_path_or_url)[1].lower()
            if ext == ".xml":
                return XMLPolicyChunker()
            elif ext in [".docx", ".doc"]:
                return BillingPolicyChunker()
            elif ext in [".html", ".htm"]:
                return SIMPolicyChunker()
            elif ext == ".pdf":
                return WifiPolicyChunker()

        if "roam" in p or "xml" in p or "enterprise" in p or "sla" in p:
            return XMLPolicyChunker()
        elif "sim" in p or "5g" in p or "network" in p:
            return SIMPolicyChunker()
        elif "wifi" in p or "pdf" in p or "fraud" in p or "family" in p or "diagnostic" in p:
            return WifiPolicyChunker()
        elif "bill" in p or "refund" in p or "fiber" in p or "ftth" in p or "docx" in p:
            return BillingPolicyChunker()
        elif p in ["web_scraped_policy", "telecom_egypt_web"]:
            return WebScrapedPolicyChunker()
        else:
            logger.warning(f"Unknown policy type '{policy_type}', defaulting to WebScrapedPolicyChunker")
            return WebScrapedPolicyChunker()
