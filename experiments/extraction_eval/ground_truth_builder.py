"""
experiments/extraction_eval/ground_truth_builder.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Lossless container-level Ground Truth parsers for all 4 file formats.

Produces:
  - GroundTruthDocument: structured dataclass with raw text, metadata, sections
  - YAML frontmatter + section metadata tags written to .md files
  - Embedded image extraction for DOCX (word/media/)
  - Gemini Vision transcription for scanned/image PDF pages and DOCX diagrams
"""

from __future__ import annotations

import io
import os
import re
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclass
class GroundTruthSection:
    """A single section within a Ground Truth document."""

    section_id: str  # e.g. sec_1, sec_2
    title: str
    order: int  # 1-based position
    page: int  # 1-based page number (1 for single-page formats)
    parent: str  # parent section_id or "root"
    content: str  # raw text content
    table_cells: int = 0  # number of table cells in this section
    has_media: bool = False  # whether media was extracted for this section


@dataclass
class GroundTruthDocument:
    """Fully-structured ground truth for one source file."""

    document_id: str
    source_file: str
    file_format: str  # html | xml | docx | pdf
    policy_type: str
    title: str

    sections: list[GroundTruthSection] = field(default_factory=list)
    raw_text: str = ""
    total_words: int = 0
    total_table_cells: int = 0
    total_media_count: int = 0
    critical_entities: list[str] = field(default_factory=list)
    page_count: int = 1
    embedded_images: list[Any] = field(default_factory=list)  # PIL Image objects
    metadata: dict[str, Any] = field(default_factory=dict)

    def section_titles(self) -> list[str]:
        return [s.title for s in sorted(self.sections, key=lambda s: s.order)]


# ---------------------------------------------------------------------------
# Helper: Extract critical entities for frontmatter
# ---------------------------------------------------------------------------


def _extract_entities(text: str) -> list[str]:
    """Quick regex pass to find telecom-critical tokens for the YAML frontmatter."""
    patterns = [
        r"\bPOL-[A-Z]+-\d{4}-V\d+\b",  # DOC IDs
        r"\bSLA-[A-Z]+\b",  # SLA tier codes
        r"\bCORP-CIRC-\d{4}\b",  # Circuit IDs
        r"\b\d{1,3}(?:\.\d+)?%\b",  # Percentages
        r"\b19\d{3}\b|\b0[0-9]{9,10}\b",  # Phone numbers
        r"\b\d+(?:\.\d+)?\s*(?:EGP|ج\.م)\b",  # Prices
        r"\b\d+\s*(?:Mbps|Gbps|GB|MB)\b",  # Speeds/sizes
    ]
    found = set()
    for p in patterns:
        for m in re.findall(p, text, flags=re.IGNORECASE):
            found.add(m.strip())
    return sorted(found)[:20]  # cap at 20 for frontmatter readability


# ---------------------------------------------------------------------------
# Helper: Count words
# ---------------------------------------------------------------------------


def _word_count(text: str) -> int:
    from .metrics import tokenize

    return len(tokenize(text))


# ---------------------------------------------------------------------------
# HTML Ground Truth Builder
# ---------------------------------------------------------------------------


def build_html_ground_truth(file_path: str) -> GroundTruthDocument:
    """
    Lossless HTML parser.
    - Keeps ALL text nodes including .note-box, .warning-box, badges, footer paragraphs.
    - Strips only <script>, <style> (invisible elements).
    - Preserves table structure as Markdown grid.
    - Captures content appearing BEFORE first heading (document metadata).
    """
    base_name = Path(file_path).stem
    with open(file_path, encoding="utf-8", errors="ignore") as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Strip scripts, styles, and HTML comment padding blocks
    # Bug fix: The HTML files contain massive <!-- hex padding --> comment blocks
    # (e.g., 2MB of 0123456789ABCDEF...) that inflate raw file size but should
    # not be included in the Ground Truth text.
    for tag in soup(["script", "style"]):
        tag.decompose()
    from bs4 import Comment

    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    title = soup.title.string.strip() if soup.title else base_name.replace("_", " ").title()

    sections: list[GroundTruthSection] = []
    all_text_parts: list[str] = []

    # ------------------------------------------------------------------
    # Capture PRE-HEADING metadata (paragraphs before first h1/h2/h3)
    # Bug fix: HTML files may wrap everything in a <div class="container">
    # so we must search the full document for the first heading, not just
    # direct children of <body>.
    # ------------------------------------------------------------------
    body = soup.body or soup
    # Find the first heading anywhere in the document
    first_heading_elem = body.find(["h1", "h2", "h3"])
    pre_heading_parts = []
    if first_heading_elem:
        # Walk all text-bearing siblings/ancestors before first heading
        for node in first_heading_elem.find_all_previous():
            if hasattr(node, "name") and node.name in ["script", "style", "head"]:
                continue
            if hasattr(node, "get_text"):
                t = node.get_text(separator=" ").strip()
                if t and len(t) > 2:
                    pre_heading_parts.append(t)
        # De-duplicate and reverse (they come out in reverse DOM order)
        seen = set()
        unique_parts = []
        for part in reversed(pre_heading_parts):
            if part not in seen:
                seen.add(part)
                unique_parts.append(part)
        pre_heading_parts = unique_parts

    if pre_heading_parts:
        pre_content = "\n".join(pre_heading_parts)
        sections.append(
            GroundTruthSection(
                section_id="sec_0",
                title="Document Header & Metadata",
                order=0,
                page=1,
                parent="root",
                content=pre_content,
            )
        )
        all_text_parts.append(pre_content)

    # ------------------------------------------------------------------
    # Section extraction by headings
    # Bug fix: headings may be inside a <div class="container"> wrapper,
    # so we search the whole document rather than just direct body children.
    # We also use find_next() to capture note-box / warning-box divs that
    # are not direct siblings of the heading but appear before the next heading.
    # ------------------------------------------------------------------
    headings = body.find_all(["h1", "h2", "h3"])
    for idx, heading in enumerate(headings):
        sec_id = f"sec_{idx + 1}"
        sec_title = heading.get_text(separator=" ").strip()
        content_parts = []
        table_cells = 0

        # Determine the stopping element: the next heading (at any depth)
        next_headings = heading.find_all_next(["h1", "h2", "h3"])
        stop_elem = next_headings[0] if next_headings else None

        # Walk every element between this heading and the next heading
        for node in heading.find_all_next():
            if node is stop_elem:
                break
            # Skip non-tag nodes and invisible containers
            if not hasattr(node, "name") or node.name in ["script", "style"]:
                continue
            # Only process leaf-level or block elements (avoid double-counting)
            if node.name == "table":
                rows = node.find_all("tr")
                md_rows = []
                for row in rows:
                    cells = row.find_all(["th", "td"])
                    cell_texts = [c.get_text(" ", strip=True) for c in cells]
                    table_cells += len(cell_texts)
                    md_rows.append(" | ".join(cell_texts))
                if md_rows:
                    header = md_rows[0]
                    sep = " | ".join(["---"] * len(header.split(" | ")))
                    md_table = "\n".join([header, sep] + md_rows[1:])
                    content_parts.append(md_table)
            elif node.name in ["p", "li", "div", "span", "code", "em", "strong", "blockquote", "dd", "dt"]:
                # Only capture if this element has text and no block children
                # to avoid double-counting container divs
                child_blocks = node.find_all(["p", "li", "table", "div", "ul", "ol"])
                if not child_blocks:
                    t = node.get_text(separator=" ").strip()
                    if t and t not in content_parts:
                        content_parts.append(t)

        content = "\n\n".join(content_parts)
        if content:
            sections.append(
                GroundTruthSection(
                    section_id=sec_id,
                    title=sec_title,
                    order=idx + 1,
                    page=1,
                    parent="root",
                    content=content,
                    table_cells=table_cells,
                )
            )
            all_text_parts.append(f"## {sec_title}\n{content}")

    raw_text = "\n\n".join(all_text_parts)
    total_cells = sum(s.table_cells for s in sections)

    return GroundTruthDocument(
        document_id=f"gt_{base_name}",
        source_file=file_path,
        file_format="html",
        policy_type=base_name,
        title=title,
        sections=sections,
        raw_text=raw_text,
        total_words=_word_count(raw_text),
        total_table_cells=total_cells,
        critical_entities=_extract_entities(raw_text),
        page_count=1,
    )


# ---------------------------------------------------------------------------
# XML Ground Truth Builder
# ---------------------------------------------------------------------------


def build_xml_ground_truth(file_path: str) -> GroundTruthDocument:
    """
    Lossless XML parser.
    - Recursively traverses ALL nodes: elem.text, elem.tail, and ALL attrib key/values.
    - Self-closing tags with attributes (e.g. <بند_التعويض نسبة_الخصم="25%"/>)
      are fully captured.
    - Each top-level child of root becomes one numbered section.
    - Falls back to BeautifulSoup XML parser on parse errors.
    """
    base_name = Path(file_path).stem

    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            xml_content = f.read()
        # Bug fix: sanitise ALL bare & occurrences, including:
        # - "e& (Etisalat)" in element text (roaming XML)
        # - attribute values with &
        # We must handle & inside CDATA-like text and attribute values.
        import re

        sanitized = re.sub(r"&(?!(amp|lt|gt|quot|apos|#\d+|#x[0-9A-Fa-f]+);)", "&amp;", xml_content)
        root = ET.fromstring(sanitized)
        doc_title = root.attrib.get("title") or root.attrib.get("name") or root.tag.replace("_", " ").title()
        policy_type = root.attrib.get("type") or base_name

        sections: list[GroundTruthSection] = []
        all_text_parts: list[str] = []

        for child_idx, child in enumerate(root):
            sec_id = f"sec_{child_idx + 1}"
            # Bug fix: Arabic XML attributes vary widely. Try all known
            # title/name/code attributes, then fall back to first attribute value,
            # then to tag name.  This correctly handles:
            # - <مستوى_الخدمة كود="SLA-DIAMOND" اسم="الفئة الماسية">
            # - <بند_التعويض نسبة_التشغيل_الشهرية="أقل من 99.9%">
            # - <دائرة_ربط معرف="CORP-CIRC-0001" اسم_العميل="...">
            # - <bundle id="PASS-DAILY-01" name="Daily Travel Passport">
            title_candidates = [
                child.attrib.get("title"),
                child.attrib.get("name"),
                child.attrib.get("اسم"),
                child.attrib.get("اسم_العميل"),
                child.attrib.get("كود"),
                child.attrib.get("id"),
                child.attrib.get("معرف"),
                # Last resort: first attribute value
                next(iter(child.attrib.values()), None),
            ]
            sec_title = next((t for t in title_candidates if t), child.tag.replace("_", " ").capitalize())

            lines: list[str] = []

            # Root-level child attributes
            for k, v in child.attrib.items():
                lines.append(f"[{k}]: {v}")

            # Full recursive traversal of child subtree
            for elem in child.iter():
                if elem.text and elem.text.strip():
                    tag_name = elem.tag.replace("_", " ").capitalize()
                    lines.append(f"{tag_name}: {elem.text.strip()}")
                if elem.tail and elem.tail.strip():
                    lines.append(elem.tail.strip())
                for k, v in elem.attrib.items():
                    lines.append(f"  [{k}]: {v}")

            content = "\n".join(lines)
            if content:
                sections.append(
                    GroundTruthSection(
                        section_id=sec_id,
                        title=sec_title,
                        order=child_idx + 1,
                        page=1,
                        parent="root",
                        content=content,
                    )
                )
                all_text_parts.append(f"## {sec_title}\n{content}")

    except ET.ParseError:
        # Fallback: BeautifulSoup XML parser
        soup = BeautifulSoup(sanitized, "xml")
        doc_title = base_name.replace("_", " ").title()
        policy_type = base_name
        sections = []
        all_text_parts = []
        for child_idx, elem in enumerate(soup.find_all(recursive=False)):
            sec_id = f"sec_{child_idx + 1}"
            sec_title = elem.name
            content = elem.get_text(separator="\n").strip()
            sections.append(
                GroundTruthSection(
                    section_id=sec_id,
                    title=sec_title,
                    order=child_idx + 1,
                    page=1,
                    parent="root",
                    content=content,
                )
            )
            all_text_parts.append(f"## {sec_title}\n{content}")

    raw_text = "\n\n".join(all_text_parts)

    return GroundTruthDocument(
        document_id=f"gt_{base_name}",
        source_file=file_path,
        file_format="xml",
        policy_type=policy_type,
        title=doc_title,
        sections=sections,
        raw_text=raw_text,
        total_words=_word_count(raw_text),
        critical_entities=_extract_entities(raw_text),
        page_count=1,
    )


# ---------------------------------------------------------------------------
# DOCX Ground Truth Builder
# ---------------------------------------------------------------------------


def build_docx_ground_truth(
    file_path: str,
    gemini_client=None,
) -> GroundTruthDocument:
    """
    Lossless DOCX parser.
    - Captures every paragraph run preserving heading level & style.
    - Tables rendered INLINE at the point they appear in document flow.
    - Embedded images extracted from word/media/ via zipfile.
    - If gemini_client is provided, images are transcribed via Gemini Vision.
    """
    from docx import Document  # python-docx

    base_name = Path(file_path).stem
    doc = Document(file_path)

    sections: list[GroundTruthSection] = []
    all_text_parts: list[str] = []
    embedded_images: list[Any] = []

    # ---- Step 1: Extract embedded images from word/media/ ----
    media_transcriptions: list[str] = []
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            media_files = [n for n in zf.namelist() if n.startswith("word/media/")]
            for mf in media_files:
                img_data = zf.read(mf)
                try:
                    from PIL import Image

                    img = Image.open(io.BytesIO(img_data))
                    embedded_images.append(img)
                    if gemini_client:
                        try:
                            prompt = (
                                "You are a precision OCR engine for technical telecom documents. "
                                "Transcribe ALL text visible in this diagram or image into structured Markdown. "
                                "Include labels, table data, flowchart steps, LED status labels, "
                                "Arabic and English captions. Be exhaustive — miss nothing."
                            )
                            response = gemini_client.generate_content([prompt, img])
                            if response and response.text:
                                media_transcriptions.append(response.text.strip())
                        except Exception:
                            media_transcriptions.append(f"[Image: {os.path.basename(mf)}]")
                    else:
                        media_transcriptions.append(f"[Image: {os.path.basename(mf)}]")
                except Exception:
                    media_transcriptions.append(f"[Binary Media: {os.path.basename(mf)}]")
    except Exception:
        pass  # Not a valid ZIP or no media

    # ---- Step 2: Build an ordered list of document elements (paragraphs + tables) ----
    # python-docx exposes doc.paragraphs and doc.tables separately,
    # but we need inline order. We walk the raw XML to get correct sequence.
    body = doc.element.body

    current_section_title = base_name.replace("_", " ").title()
    current_section_idx = 0
    current_paragraphs: list[str] = []
    first_heading = None

    def flush_section():
        nonlocal current_section_idx, current_section_title, current_paragraphs
        if current_paragraphs:
            sec_id = f"sec_{current_section_idx}"
            content = "\n".join(current_paragraphs)
            sections.append(
                GroundTruthSection(
                    section_id=sec_id,
                    title=current_section_title,
                    order=current_section_idx,
                    page=1,
                    parent="root",
                    content=content,
                )
            )
            all_text_parts.append(f"## {current_section_title}\n{content}")
            current_paragraphs = []
            current_section_idx += 1

    for elem in body:
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag

        if tag == "p":
            # Paragraph
            # Find paragraph in doc.paragraphs by XML identity
            from docx.text.paragraph import Paragraph

            p = Paragraph(elem, doc)
            text = p.text.strip()
            if not text:
                continue
            if p.style.name.startswith("Heading"):
                flush_section()
                current_section_title = text
                if first_heading is None:
                    first_heading = text
            else:
                current_paragraphs.append(text)

        elif tag == "tbl":
            # Inline table — render as Markdown grid
            from docx.table import Table

            tbl = Table(elem, doc)
            rows_md = []
            for row in tbl.rows:
                cells = [cell.text.strip() for cell in row.cells]
                rows_md.append(" | ".join(cells))
            if rows_md:
                sep = " | ".join(["---"] * len(rows_md[0].split(" | ")))
                md_table = "\n".join([rows_md[0], sep] + rows_md[1:])
                current_paragraphs.append(md_table)

    flush_section()

    # Append media transcriptions as final section
    if media_transcriptions:
        media_content = "\n\n".join(media_transcriptions)
        sections.append(
            GroundTruthSection(
                section_id=f"sec_{current_section_idx}",
                title="Embedded Diagrams & Visual Content",
                order=current_section_idx,
                page=1,
                parent="root",
                content=media_content,
                has_media=True,
            )
        )
        all_text_parts.append(f"## Embedded Diagrams & Visual Content\n{media_content}")
        current_section_idx += 1

    # Count total table cells from all sections
    # We accumulate via a running counter in the loop above, so we do it from sections
    total_tbl_cells = 0
    for line in "\n".join(all_text_parts).split("\n"):
        if " | " in line and not line.startswith("---"):
            total_tbl_cells += len(line.split(" | "))

    raw_text = "\n\n".join(all_text_parts)
    doc_title = first_heading or base_name.replace("_", " ").title()

    return GroundTruthDocument(
        document_id=f"gt_{base_name}",
        source_file=file_path,
        file_format="docx",
        policy_type=base_name,
        title=doc_title,
        sections=sections,
        raw_text=raw_text,
        total_words=_word_count(raw_text),
        total_table_cells=total_tbl_cells,
        total_media_count=len(embedded_images),
        critical_entities=_extract_entities(raw_text),
        embedded_images=embedded_images,
        page_count=1,
    )


# ---------------------------------------------------------------------------
# PDF Ground Truth Builder
# ---------------------------------------------------------------------------


def build_pdf_ground_truth(
    file_path: str,
    gemini_client=None,
    max_vision_pages: int = 50,
) -> GroundTruthDocument:
    """
    Lossless PDF parser.
    - PyMuPDF native word stream for text-rich pages.
    - 150 DPI page render + Gemini Vision transcription for scanned/diagram pages.
    - Each page becomes one numbered section with page metadata.
    """
    import fitz  # PyMuPDF
    from PIL import Image

    base_name = Path(file_path).stem
    doc = fitz.open(file_path)
    sections: list[GroundTruthSection] = []
    all_text_parts: list[str] = []
    embedded_images: list[Any] = []
    inferred_title: str | None = None

    for page_idx in range(len(doc)):
        page_num = page_idx + 1
        page = doc.load_page(page_idx)

        # ---- Native text ----
        native_text = page.get_text("text").strip()
        is_scanned = len(native_text) < 80  # threshold: less than 80 chars = image page

        page_text = native_text
        vision_used = False

        # ---- Gemini Vision for scanned / diagram pages ----
        if gemini_client and page_idx < max_vision_pages:
            try:
                pix = page.get_pixmap(dpi=150)
                img_bytes = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_bytes))
                embedded_images.append(img)

                if is_scanned or page_idx < max_vision_pages:
                    prompt = (
                        "You are a precision OCR and technical document analysis engine. "
                        "Your task is to produce a COMPLETE, LOSSLESS transcription of this page. "
                        "Include ALL text, numbers, table data, flowchart steps, LED status labels, "
                        "Arabic and English content, footnotes, and captions. "
                        "Format tables as Markdown. Miss nothing."
                    )
                    response = gemini_client.generate_content([prompt, img])
                    if response and response.text:
                        page_text = response.text.strip()
                        vision_used = True
            except Exception:
                pass  # Fall back to native text

        if not inferred_title and page_text:
            first_line = page_text.splitlines()[0].replace("#", "").strip()
            if len(first_line) > 3:
                inferred_title = first_line

        sections.append(
            GroundTruthSection(
                section_id=f"page_{page_num}",
                title=f"{base_name.replace('_', ' ').title()} — Page {page_num}",
                order=page_num,
                page=page_num,
                parent="root",
                content=page_text,
                has_media=vision_used,
            )
        )
        all_text_parts.append(page_text)

    doc.close()
    raw_text = "\n\n".join(all_text_parts)
    doc_title = inferred_title or base_name.replace("_", " ").title()

    return GroundTruthDocument(
        document_id=f"gt_{base_name}",
        source_file=file_path,
        file_format="pdf",
        policy_type="wifi_troubleshooting" if base_name == "pdf" else base_name,
        title=doc_title,
        sections=sections,
        raw_text=raw_text,
        total_words=_word_count(raw_text),
        total_media_count=len(embedded_images),
        critical_entities=_extract_entities(raw_text),
        page_count=len(sections),
        embedded_images=embedded_images,
    )


# ---------------------------------------------------------------------------
# Main GroundTruthBuilder Dispatcher
# ---------------------------------------------------------------------------


class GroundTruthBuilder:
    """
    Dispatches the correct lossless parser based on file extension.
    Generates YAML-frontmatted Markdown files with section metadata.
    """

    def __init__(self, gemini_client=None):
        self.gemini_client = gemini_client

    def build(self, file_path: str) -> GroundTruthDocument:
        ext = Path(file_path).suffix.lower()
        if ext in [".html", ".htm"]:
            return build_html_ground_truth(file_path)
        elif ext == ".xml":
            return build_xml_ground_truth(file_path)
        elif ext in [".docx", ".doc"]:
            return build_docx_ground_truth(file_path, gemini_client=self.gemini_client)
        elif ext == ".pdf":
            return build_pdf_ground_truth(file_path, gemini_client=self.gemini_client)
        else:
            raise ValueError(f"Unsupported format for Ground Truth: {ext}")

    def to_markdown(self, gt: GroundTruthDocument) -> str:
        """
        Render a GroundTruthDocument into a YAML-frontmatted Markdown string.
        Includes per-section metadata delimiter comments.
        """
        lines: list[str] = []

        # ---- YAML Frontmatter ----
        lines.append("---")
        lines.append(f"document_id: {gt.document_id}")
        lines.append(f"source_file: {os.path.basename(gt.source_file)}")
        lines.append(f"file_format: {gt.file_format}")
        lines.append(f"policy_type: {gt.policy_type}")
        lines.append(f'title: "{gt.title}"')
        lines.append(f"page_count: {gt.page_count}")
        lines.append(f"total_sections: {len(gt.sections)}")
        lines.append(f"total_words: {gt.total_words}")
        lines.append(f"total_table_cells: {gt.total_table_cells}")
        lines.append(f"total_media_count: {gt.total_media_count}")

        # Critical entities list
        if gt.critical_entities:
            entities_str = ", ".join(f'"{e}"' for e in gt.critical_entities[:20])
            lines.append(f"critical_entities: [{entities_str}]")
        else:
            lines.append("critical_entities: []")

        # Hierarchy
        lines.append("hierarchy:")
        for sec in sorted(gt.sections, key=lambda s: s.order):
            lines.append(f"  - id: {sec.section_id}")
            safe_title = sec.title.replace('"', "'")
            lines.append(f'    title: "{safe_title}"')
            lines.append(f"    order: {sec.order}")
            lines.append(f"    page: {sec.page}")
        lines.append("---\n")

        # ---- Sections with metadata delimiters ----
        for sec in sorted(gt.sections, key=lambda s: s.order):
            safe_title = sec.title.replace('"', "'")
            lines.append(
                f"<!-- section: {sec.section_id} | "
                f"title: {safe_title} | "
                f"page: {sec.page} | "
                f"order: {sec.order} | "
                f"parent: {sec.parent} "
                f"-->"
            )
            # Heading level: use h1 for page-level (PDF), h2 for section-level
            heading_level = "##" if gt.file_format != "pdf" else "###"
            lines.append(f"{heading_level} {sec.title}\n")
            lines.append(sec.content)
            lines.append("")  # blank line between sections

        return "\n".join(lines)

    def save(self, gt: GroundTruthDocument, output_dir: str) -> str:
        """Save ground truth as .md file. Returns the saved file path."""
        os.makedirs(output_dir, exist_ok=True)
        stem = Path(gt.source_file).stem
        out_path = os.path.join(output_dir, f"{stem}.md")
        md_content = self.to_markdown(gt)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        return out_path


# ---------------------------------------------------------------------------
# Ground Truth Loader (for Notebook 2)
# ---------------------------------------------------------------------------


def load_ground_truth_md(md_path: str) -> tuple[dict[str, Any], str, list[GroundTruthSection]]:
    """
    Load a saved Ground Truth .md file.
    Returns:
        (frontmatter_dict, raw_body_text, sections_list)
    """
    import yaml

    with open(md_path, encoding="utf-8") as f:
        content = f.read()

    # Parse YAML frontmatter
    frontmatter: dict[str, Any] = {}
    body = content
    if content.startswith("---"):
        end_idx = content.find("---", 3)
        if end_idx != -1:
            yaml_str = content[3:end_idx].strip()
            try:
                frontmatter = yaml.safe_load(yaml_str) or {}
            except Exception:
                frontmatter = {}
            body = content[end_idx + 3 :].strip()

    # Parse sections from metadata delimiter comments
    sections: list[GroundTruthSection] = []
    section_pattern = re.compile(
        r"<!--\s*section:\s*(\S+)\s*\|\s*title:\s*(.+?)\s*\|\s*page:\s*(\d+)\s*\|"
        r"\s*order:\s*(\d+)\s*\|\s*parent:\s*(\S+)\s*-->"
    )
    blocks = re.split(r"<!--\s*section:[^>]+-->", body)
    matches = section_pattern.findall(body)

    for i, match in enumerate(matches):
        sec_id, title, page, order, parent = match
        # Content is everything in the corresponding block (after the heading line)
        block_text = blocks[i + 1] if i + 1 < len(blocks) else ""
        # Strip the heading line
        block_lines = block_text.strip().splitlines()
        content_lines = [line for line in block_lines if not line.strip().startswith("#")]
        content = "\n".join(content_lines).strip()

        sections.append(
            GroundTruthSection(
                section_id=sec_id.strip(),
                title=title.strip(),
                order=int(order),
                page=int(page),
                parent=parent.strip(),
                content=content,
            )
        )

    return frontmatter, body, sections
