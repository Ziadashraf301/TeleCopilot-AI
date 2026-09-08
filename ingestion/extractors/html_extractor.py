import os
from bs4 import BeautifulSoup
from core.logger import get_logger
from ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class HTMLExtractor(BaseExtractor):
    """
    Extracts semantic structure, headings, policy clauses, and metadata from HTML files.
    Ideal for SIM Replacement and 5G Network Device Service Guides.
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        logger.info(f"Extracting HTML document from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()

        soup = BeautifulSoup(html_content, "html.parser")

        # Strip scripts, styles
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()

        title = soup.title.string.strip() if soup.title else base_name.replace("_", " ").title()

        sections = []
        headings = soup.find_all(["h1", "h2", "h3"])

        if headings:
            for heading in headings:
                sec_title = heading.get_text().strip()
                content_parts = []
                sibling = heading.find_next_sibling()
                while sibling and sibling.name not in ["h1", "h2", "h3"]:
                    if sibling.get_text().strip():
                        content_parts.append(sibling.get_text().strip())
                    sibling = sibling.find_next_sibling()

                sec_content = "\n".join(content_parts)
                if sec_content:
                    sections.append({
                        "section_title": sec_title,
                        "content": sec_content,
                        "page_number": 1
                    })
        else:
            # Fallback
            sections.append({
                "section_title": title,
                "content": soup.get_text(separator="\n").strip(),
                "page_number": 1
            })

        raw_text = soup.get_text(separator="\n").strip()

        return ExtractedDocument(
            document_id=f"doc_html_{os.path.basename(file_path)}",
            source_path=file_path,
            title=title,
            raw_text=raw_text,
            policy_type=base_name,
            sections=sections,
            metadata={"format": "html", "file_size": len(html_content)}
        )
