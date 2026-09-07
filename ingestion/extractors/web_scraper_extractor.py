import io
from typing import List, Dict, Any
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field
from core.logger import get_logger
from ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class WebScraperExtractor(BaseExtractor):
    """
    Zero-Local-Disk Dynamic Web Scraper.
    Fetches online website URLs (e.g. https://www.te.eg/ and its sub-policy pages)
    directly in-memory via HTTPX and parses DOM structures into ExtractedDocument
    without writing any files to disk.
    """

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }

    def scrape_url_in_memory(self, url: str) -> ExtractedDocument:
        """Fetches URL and parses content directly in memory."""
        logger.info(f"WebScraper fetching live URL in-memory: {url}")
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=True, headers=self.headers, verify=False) as client:
                response = client.get(url)
                response.raise_for_status()
                html_content = response.text
                logger.info(f"Fetched {url} ({len(html_content)} bytes)")
        except Exception as e:
            logger.error(f"Live scraping request failed for {url}: {e}")
            raise RuntimeError(f"Failed to scrape URL {url}: {e}")

        return self._parse_html_in_memory(html_content, source_url=url)

    def extract(self, url_or_target: str) -> ExtractedDocument:
        """BaseExtractor interface implementation."""
        return self.scrape_url_in_memory(url_or_target)

    def _parse_html_in_memory(self, html_content: str, source_url: str) -> ExtractedDocument:
        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles, metadata
        for tag in soup(["script", "style", "noscript", "svg", "header", "footer", "nav"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else source_url
        sections = []
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5"])

        if headings:
            for heading in headings:
                sec_title = heading.get_text().strip()
                content_parts = []
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ["h1", "h2", "h3", "h4", "h5"]:
                    text = sibling.get_text().strip()
                    if text:
                        content_parts.append(text)
                    sibling = sibling.find_next_sibling()

                sec_content = "\n".join(content_parts)
                if sec_content and len(sec_content) > 10:
                    sections.append({
                        "section_title": sec_title,
                        "content": sec_content,
                        "page_number": 1
                    })

        if not sections:
            # Fallback if no clean headings
            text_blocks = [p.get_text().strip() for p in soup.find_all("p") if len(p.get_text().strip()) > 20]
            if text_blocks:
                sections.append({
                    "section_title": f"{title} - Main Content",
                    "content": "\n".join(text_blocks),
                    "page_number": 1
                })
            else:
                body_text = soup.get_text(separator="\n").strip()
                sections.append({
                    "section_title": title,
                    "content": body_text[:3000],
                    "page_number": 1
                })

        raw_text = soup.get_text(separator="\n").strip()

        return ExtractedDocument(
            document_id=f"doc_scraped_{abs(hash(source_url)) % 1000000}",
            source_path=source_url,
            title=title,
            raw_text=raw_text,
            policy_type="telecom_egypt_web",
            sections=sections,
            metadata={"source_url": source_url, "scraped_live": True}
        )
