import os
import io
import fitz  # PyMuPDF
from PIL import Image
from core.logger import get_logger
from core.singletons import SingletonsManager
from ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class GeminiOCRExtractor(BaseExtractor):
    """
    Multimodal Vision OCR Extractor using Google Gemini.
    Renders PDF pages into images and uses Gemini 1.5 Flash Vision to extract
    troubleshooting flows, diagrams, tables, and policy steps with high fidelity.
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        logger.info(f"Extracting PDF via Gemini Multimodal OCR from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = fitz.open(file_path)
        gemini_client = SingletonsManager.get_gemini_client()

        sections = []
        full_text_parts = []

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)

            # Extract basic text first
            native_text = page.get_text().strip()

            # Render page to high-res image for Multimodal OCR
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_bytes))

            ocr_text = native_text
            if gemini_client:
                try:
                    logger.info(f"Invoking Gemini Multimodal Vision OCR on PDF page {page_num}...")
                    prompt = (
                        "You are an expert OCR and document analysis engine for Telecom Customer Support. "
                        "Extract all text, troubleshooting checklists, tables, decision trees, and policy rules "
                        "accurately in clear markdown formatting."
                    )
                    response = gemini_client.generate_content([prompt, img])
                    if response and response.text:
                        ocr_text = response.text.strip()
                        logger.info(f"Gemini OCR successfully extracted page {page_num} ({len(ocr_text)} chars)")
                except Exception as e:
                    logger.warning(f"Gemini Vision OCR API call skipped/failed on page {page_num}: {e}. Using native text.")

            full_text_parts.append(ocr_text)
            sections.append({
                "section_title": f"WiFi Troubleshooting & Dispatch Guide - Page {page_num}",
                "content": ocr_text,
                "page_number": page_num
            })

        doc.close()
        raw_text = "\n\n".join(full_text_parts)

        return ExtractedDocument(
            document_id=f"doc_pdf_{os.path.basename(file_path)}",
            source_path=file_path,
            title="Home WiFi Troubleshooting & Technician Dispatch Policy",
            raw_text=raw_text,
            policy_type="wifi_troubleshooting",
            sections=sections,
            metadata={"format": "pdf", "pages": len(sections), "ocr_engine": "gemini-multimodal-vision"}
        )
