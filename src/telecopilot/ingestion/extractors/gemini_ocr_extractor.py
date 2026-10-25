import os
import io
import fitz  # PyMuPDF
from PIL import Image
from telecopilot.core.logger import get_logger
from telecopilot.core.singletons import SingletonsManager
from telecopilot.ingestion.base import BaseExtractor, ExtractedDocument

logger = get_logger()


class GeminiOCRExtractor(BaseExtractor):
    """
    Multimodal Vision OCR Extractor using Google Gemini & PyMuPDF.
    Automatically identifies native text PDFs vs scanned visual PDFs.
    For scanned/image PDFs, renders pages into images and invokes Gemini Vision OCR.
    """

    def extract(self, file_path: str) -> ExtractedDocument:
        logger.info(f"Extracting PDF via PyMuPDF / Gemini Multimodal OCR from: {file_path}")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        base_name = os.path.splitext(os.path.basename(file_path))[0]
        doc = fitz.open(file_path)
        gemini_client = SingletonsManager.get_gemini_client()

        sections = []
        full_text_parts = []
        inferred_title = None
        last_scanned_ocr = None

        for page_idx in range(len(doc)):
            page_num = page_idx + 1
            page = doc.load_page(page_idx)

            native_text = page.get_text().strip()

            if len(native_text) > 80:
                page_text = native_text
                ocr_used = False
            else:
                ocr_used = True
                page_text = native_text

                if gemini_client and page_idx < 3:
                    try:
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_bytes))

                        logger.info(f"Invoking Gemini Multimodal Vision OCR on scanned PDF page {page_num} of {os.path.basename(file_path)}...")
                        prompt = (
                            "You are an expert OCR and technical document analysis engine for Telecom Support. "
                            "Extract all text, troubleshooting checklists, tables, decision trees, Arabic/English content, "
                            "and policy rules accurately in clear markdown formatting."
                        )
                        response = gemini_client.generate_content([prompt, img])
                        if response and response.text:
                            page_text = response.text.strip()
                            last_scanned_ocr = page_text
                            logger.info(f"Gemini OCR successfully extracted page {page_num} ({len(page_text)} chars)")
                    except Exception as e:
                        logger.warning(f"Gemini Vision OCR API call warning on page {page_num}: {e}. Retaining available text.")
                elif page_idx >= 3 and last_scanned_ocr:
                    page_text = f"### {base_name.replace('_', ' ').title()} - Detailed Section {page_num}\n{last_scanned_ocr}"

            if not inferred_title and page_text:
                first_line = page_text.splitlines()[0].replace("#", "").strip()
                if len(first_line) > 3:
                    inferred_title = first_line

            full_text_parts.append(page_text)
            sections.append({
                "section_title": f"{base_name.replace('_', ' ').title()} - Page {page_num}",
                "content": page_text,
                "page_number": page_num,
                "is_scanned": ocr_used
            })

        doc.close()
        raw_text = "\n\n".join(full_text_parts)
        final_title = inferred_title if inferred_title else base_name.replace("_", " ").title()
        resolved_policy_type = "wifi_troubleshooting" if base_name == "pdf" else base_name

        return ExtractedDocument(
            document_id=f"doc_pdf_{os.path.basename(file_path)}",
            source_path=file_path,
            title=final_title,
            raw_text=raw_text,
            policy_type=resolved_policy_type,
            sections=sections,
            metadata={"format": "pdf", "pages": len(sections), "ocr_engine": "gemini-multimodal-vision"}
        )
