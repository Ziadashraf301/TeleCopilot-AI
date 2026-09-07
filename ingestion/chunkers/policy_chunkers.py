import os
from typing import List, Dict, Any
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    HTMLHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from ingestion.base import BaseChunker
from models.document_models import ExtractedDocument, DocumentChunk
from core.logger import get_logger

logger = get_logger()


class SIMPolicyChunker(BaseChunker):
    """
    Source 1 (HTML): HTML Structural Header Splitter + Recursive Splitter.
    Uses HTMLHeaderTextSplitter on DOM headers (<h1>, <h2>, <h3>) to preserve
    device replacement policies, verification workflows, and in-store fee waivers.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        self.html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " "]
        )

    def chunk(self, document: ExtractedDocument) -> List[DocumentChunk]:
        chunks = []
        chunk_idx = 1

        # 1. First split by HTML header hierarchy if raw HTML is available
        try:
            html_header_docs = self.html_splitter.split_text(document.raw_text)
        except Exception:
            html_header_docs = []

        if html_header_docs:
            for doc in html_header_docs:
                splits = self.text_splitter.split_text(doc.page_content)
                header_title = doc.metadata.get("Header 2") or doc.metadata.get("Header 1") or document.title
                for part in splits:
                    content = (
                        f"[SOURCE: LOCAL_HTML] [INTENT: SIM_MANAGEMENT]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"TOPIC: {header_title}\n"
                        f"RULES & WORKFLOW:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"sim_chunk_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="LOCAL_HTML",
                            policy_type="sim_replacement",
                            intent_category="SIM_MANAGEMENT",
                            section_title=header_title,
                            page_number=1,
                            metadata={"format": "html", "intent": "SIM_MANAGEMENT", "splitter": "LangChain_HTMLHeaderTextSplitter"}
                        )
                    )
                    chunk_idx += 1
        else:
            # Fallback per section
            for sec in document.sections:
                splits = self.text_splitter.split_text(sec.get("content", ""))
                for part in splits:
                    content = (
                        f"[SOURCE: LOCAL_HTML] [INTENT: SIM_MANAGEMENT]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"TOPIC: {sec['section_title']}\n"
                        f"RULES & WORKFLOW:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"sim_chunk_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="LOCAL_HTML",
                            policy_type="sim_replacement",
                            intent_category="SIM_MANAGEMENT",
                            section_title=sec["section_title"],
                            page_number=1,
                            metadata={"format": "html", "intent": "SIM_MANAGEMENT", "splitter": "LangChain_RecursiveCharacter"}
                        )
                    )
                    chunk_idx += 1

        logger.info(f"LangChain HTML SIMPolicyChunker produced {len(chunks)} chunks.")
        return chunks


class WifiPolicyChunker(BaseChunker):
    """
    Source 2 (PDF with Gemini Vision OCR): Markdown Header Splitter for Gemini OCR Outputs.
    Step 1: Gemini Vision OCR converts PDF pages & tables into structured Markdown (`#`, `##`, tables).
    Step 2: MarkdownHeaderTextSplitter splits on Markdown sections (`#`, `##`, `###`) preserving complete diagnostic steps and SLA tables.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on,
            strip_headers=False
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n- ", "\n", ". "]
        )

    def chunk(self, document: ExtractedDocument) -> List[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        doc_tag = os.path.basename(document.source_path).replace(".", "_")

        # 1. Split Markdown OCR output by headers
        try:
            md_header_docs = self.md_splitter.split_text(document.raw_text)
        except Exception:
            md_header_docs = []

        if md_header_docs:
            for doc in md_header_docs:
                splits = self.text_splitter.split_text(doc.page_content)
                header_title = doc.metadata.get("Header 2") or doc.metadata.get("Header 1") or "WiFi Troubleshooting"
                for part in splits:
                    content = (
                        f"[SOURCE: PDF_VISION_OCR] [INTENT: WIFI_TECHNICAL_SUPPORT]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"SECTION: {header_title}\n"
                        f"DIAGNOSTIC & SLA DISPATCH RULES:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"wifi_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="PDF_VISION_OCR",
                            policy_type="wifi_troubleshooting",
                            intent_category="WIFI_TECHNICAL_SUPPORT",
                            section_title=header_title,
                            page_number=1,
                            metadata={"format": "pdf", "intent": "WIFI_TECHNICAL_SUPPORT", "splitter": "LangChain_MarkdownHeaderTextSplitter", "ocr_engine": "gemini-vision"}
                        )
                    )
                    chunk_idx += 1
        else:
            for sec in document.sections:
                splits = self.text_splitter.split_text(sec.get("content", ""))
                for part in splits:
                    content = (
                        f"[SOURCE: PDF_VISION_OCR] [INTENT: WIFI_TECHNICAL_SUPPORT]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"SECTION: {sec['section_title']}\n"
                        f"DIAGNOSTIC & SLA DISPATCH RULES:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"wifi_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="PDF_VISION_OCR",
                            policy_type="wifi_troubleshooting",
                            intent_category="WIFI_TECHNICAL_SUPPORT",
                            section_title=sec["section_title"],
                            page_number=sec.get("page_number", 1),
                            metadata={"format": "pdf", "intent": "WIFI_TECHNICAL_SUPPORT", "splitter": "LangChain_RecursiveCharacter"}
                        )
                    )
                    chunk_idx += 1

        logger.info(f"LangChain Markdown-Aware WifiPolicyChunker produced {len(chunks)} chunks for {document.source_path}.")
        return chunks


class BillingPolicyChunker(BaseChunker):
    """
    Source 3 (DOCX): Clause-Aware Recursive Text Splitter.
    Preserves legal clauses, dollar thresholds ($15, $50), and annual courtesy waiver rules.
    """

    def __init__(self, chunk_size: int = 450, chunk_overlap: int = 60):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". "]
        )

    def chunk(self, document: ExtractedDocument) -> List[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        for sec in document.sections:
            sec_text = sec.get("content", "")
            split_texts = self.text_splitter.split_text(sec_text)

            for part in split_texts:
                content = (
                    f"[SOURCE: WORD_DOCX] [INTENT: BILLING_AND_PAYMENTS]\n"
                    f"DOCUMENT: {document.title}\n"
                    f"CLAUSE: {sec['section_title']}\n"
                    f"REFUND RULES & CRITERIA:\n{part}"
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"billing_chunk_{chunk_idx}",
                        content=content,
                        source=document.source_path,
                        source_modality="WORD_DOCX",
                        policy_type="billing_refund",
                        intent_category="BILLING_AND_PAYMENTS",
                        section_title=sec["section_title"],
                        page_number=sec.get("page_number", 1),
                        metadata={"format": "docx", "intent": "BILLING_AND_PAYMENTS", "splitter": "LangChain_ClauseSplitter"}
                    )
                )
                chunk_idx += 1

        logger.info(f"LangChain BillingPolicyChunker produced {len(chunks)} chunks.")
        return chunks


class WebScrapedPolicyChunker(BaseChunker):
    """
    Source 4 (Live Web Scraping & te.eg): Markdown & Table Aware Semantic Chunker.
    Splits scraped web pages preserving package speed tiers (Super 30Mbps, Mega 70Mbps, Ultra 100Mbps, Max 200Mbps),
    pricing tables, and quota rules.
    """

    def __init__(self, chunk_size: int = 650, chunk_overlap: int = 120):
        self.headers_to_split_on = [
            ("h1", "Header 1"),
            ("h2", "Header 2"),
            ("h3", "Header 3"),
        ]
        self.html_splitter = HTMLHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " | ", " "]
        )

    def chunk(self, document: ExtractedDocument) -> List[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        for sec in document.sections:
            sec_text = sec.get("content", "")
            split_texts = self.text_splitter.split_text(sec_text)

            for part in split_texts:
                content = (
                    f"[SOURCE: LIVE_WEB_SCRAPED] [INTENT: PLANS_AND_OFFERS]\n"
                    f"URL: {document.source_path}\n"
                    f"PAGE: {document.title}\n"
                    f"OFFER / PACKAGE DETAILS: {sec['section_title']}\n"
                    f"CONTENT:\n{part}"
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"web_chunk_{chunk_idx}",
                        content=content,
                        source=document.source_path,
                        source_modality="LIVE_WEB_SCRAPED",
                        policy_type="telecom_egypt_web",
                        intent_category="PLANS_AND_OFFERS",
                        section_title=sec["section_title"],
                        page_number=sec.get("page_number", 1),
                        metadata={"format": "web_scraped", "intent": "PLANS_AND_OFFERS", "splitter": "LangChain_WebSemanticSplitter", "url": document.source_path}
                    )
                )
                chunk_idx += 1

        logger.info(f"LangChain WebScrapedPolicyChunker produced {len(chunks)} chunks.")
        return chunks
