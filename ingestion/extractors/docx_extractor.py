import os
from docx import Document
from core.logger import get_logger
from ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class DocxExtractor(BaseExtractor):
    """
    Extracts structured policy rules, heading hierarchies, tables, and clauses
    from Word (.docx) documents.
    Supports Billing Dispute policies and FTTH Installation Guides.
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        logger.info(f"Extracting DOCX document from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        doc = Document(file_path)
        sections = []
        default_title = base_name.replace("_", " ").title()
        current_title = default_title
        current_paragraphs = []
        first_heading_seen = None

        # Process paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            if p.style.name.startswith("Heading"):
                if not first_heading_seen:
                    first_heading_seen = text
                if current_paragraphs:
                    sections.append({
                        "section_title": current_title,
                        "content": "\n".join(current_paragraphs),
                        "page_number": 1
                    })
                    current_paragraphs = []
                current_title = text
            else:
                current_paragraphs.append(text)

        if current_paragraphs:
            sections.append({
                "section_title": current_title,
                "content": "\n".join(current_paragraphs),
                "page_number": 1
            })

        # Process tables
        for idx, table in enumerate(doc.tables):
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells]
                table_rows.append(" | ".join(row_cells))
            table_text = "\n".join(table_rows)
            sections.append({
                "section_title": f"Technical Data & Schedule Table {idx + 1}",
                "content": table_text,
                "page_number": 1
            })

        full_text = "\n\n".join([f"### {s['section_title']}\n{s['content']}" for s in sections])
        final_title = first_heading_seen if first_heading_seen else default_title

        return ExtractedDocument(
            document_id=f"doc_docx_{os.path.basename(file_path)}",
            source_path=file_path,
            title=final_title,
            raw_text=full_text,
            policy_type=base_name,
            sections=sections,
            metadata={"format": "docx", "total_sections": len(sections)}
        )
