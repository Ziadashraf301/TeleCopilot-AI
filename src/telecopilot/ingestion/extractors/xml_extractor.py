import os
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from telecopilot.core.logger import get_logger
from telecopilot.ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class XMLExtractor(BaseExtractor):
    """
    Extracts structured policy rules, tier schedules, rates, and SLA clauses
    from XML documents. Ideal for Roaming Tariffs and Enterprise SLA Contracts.
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        logger.info(f"Extracting XML document from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        filename = os.path.basename(file_path).lower()
        sections = []
        raw_text_parts = []

        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                xml_content = f.read()
            import re

            sanitized = re.sub(r"&(?!(amp|lt|gt|quot|apos);)", "&amp;", xml_content)
            root = ET.fromstring(sanitized)

            doc_title = root.attrib.get("title") or root.attrib.get("name") or root.tag.replace("_", " ").title()
            policy_type = root.attrib.get("type") or os.path.splitext(filename)[0]

            for child in root:
                sec_id = child.attrib.get("id") or child.attrib.get("code") or child.tag
                sec_title = (
                    child.attrib.get("title") or child.attrib.get("name") or f"{child.tag.capitalize()} ({sec_id})"
                )

                child_lines = []
                for elem in child.iter():
                    if elem.text and elem.text.strip():
                        tag_name = elem.tag.replace("_", " ").capitalize()
                        child_lines.append(f"{tag_name}: {elem.text.strip()}")
                    for k, v in elem.attrib.items():
                        child_lines.append(f"  [{k}]: {v}")

                content = "\n".join(child_lines)
                if content:
                    sections.append({"section_title": sec_title, "content": content, "page_number": 1})
                    raw_text_parts.append(f"## {sec_title}\n{content}")

        except Exception as e:
            logger.warning(f"ElementTree parse warning for {file_path}: {e}. Falling back to BeautifulSoup XML parser.")
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content_str = f.read()
            soup = BeautifulSoup(content_str, "xml")
            doc_title = soup.find().name if soup.find() else os.path.basename(file_path)
            policy_type = os.path.splitext(filename)[0]
            for elem in soup.find_all(recursive=False):
                sec_title = elem.name
                sec_content = elem.get_text(separator="\n").strip()
                sections.append({"section_title": sec_title, "content": sec_content, "page_number": 1})
                raw_text_parts.append(f"## {sec_title}\n{sec_content}")

        raw_text = "\n\n".join(raw_text_parts)

        return ExtractedDocument(
            document_id=f"doc_xml_{os.path.basename(file_path)}",
            source_path=file_path,
            title=doc_title,
            raw_text=raw_text,
            policy_type=policy_type,
            sections=sections,
            metadata={"format": "xml", "total_sections": len(sections)},
        )
