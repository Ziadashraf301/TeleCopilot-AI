import os
import re

from langchain_text_splitters import (
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from telecopilot.core.logger import get_logger
from telecopilot.ingestion.base import BaseChunker
from telecopilot.models.document_models import DocumentChunk, ExtractedDocument

logger = get_logger()

_HTML_HEADER_RE = re.compile(r"<h[1-6][\s>]", re.IGNORECASE)


def get_intent_for_policy(policy_type: str) -> str:
    """Helper to map any policy type or keyword to its canonical intent category."""
    p = (policy_type or "").lower()
    if "sim" in p:
        return "SIM_MANAGEMENT"
    elif "5g" in p or "network" in p:
        return "NETWORK_TECHNICAL_SUPPORT"
    elif "roam" in p:
        return "ROAMING_AND_INTERNATIONAL"
    elif "enterprise" in p or "sla" in p:
        return "ENTERPRISE_B2B_SUPPORT"
    elif "bill" in p or "refund" in p:
        return "BILLING_AND_PAYMENTS"
    elif "fiber" in p or "ftth" in p or "install" in p:
        return "BROADBAND_INSTALLATION"
    elif "fraud" in p or "secur" in p or "cyber" in p:
        return "FRAUD_AND_SECURITY"
    elif "family" in p or "bundle" in p or "migrat" in p:
        return "ACCOUNT_MIGRATION_OFFERS"
    elif "router" in p or "diagnostic" in p:
        return "ROUTER_HARDWARE_SUPPORT"
    elif "wifi" in p or "outage" in p:
        return "WIFI_TECHNICAL_SUPPORT"
    elif "web" in p or "plan" in p or "te.eg" in p:
        return "PLANS_AND_OFFERS"
    return "GENERAL_SUPPORT"


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
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " "]
        )

    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        intent = get_intent_for_policy(document.policy_type)
        doc_tag = os.path.basename(document.source_path).replace(".", "_")

        # HTMLHeaderTextSplitter only makes sense on real HTML markup. Extractors usually
        # hand over already-stripped plain text, in which case the structured sections
        # from the extractor must be used instead (otherwise all headings are lost).
        html_header_docs = []
        if _HTML_HEADER_RE.search(document.raw_text or ""):
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
                        f"[SOURCE: LOCAL_HTML] [INTENT: {intent}]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"TOPIC: {header_title}\n"
                        f"RULES & WORKFLOW:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"html_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="LOCAL_HTML",
                            policy_type=document.policy_type,
                            intent_category=intent,
                            section_title=header_title,
                            page_number=1,
                            metadata={
                                "format": "html",
                                "intent": intent,
                                "splitter": "LangChain_HTMLHeaderTextSplitter",
                            },
                        )
                    )
                    chunk_idx += 1
        else:
            for sec in document.sections:
                splits = self.text_splitter.split_text(sec.get("content", ""))
                for part in splits:
                    content = (
                        f"[SOURCE: LOCAL_HTML] [INTENT: {intent}]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"TOPIC: {sec['section_title']}\n"
                        f"RULES & WORKFLOW:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"html_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="LOCAL_HTML",
                            policy_type=document.policy_type,
                            intent_category=intent,
                            section_title=sec["section_title"],
                            page_number=1,
                            metadata={"format": "html", "intent": intent, "splitter": "LangChain_RecursiveCharacter"},
                        )
                    )
                    chunk_idx += 1

        logger.info(f"LangChain HTML SIMPolicyChunker produced {len(chunks)} chunks for {document.source_path}.")
        return chunks


class WifiPolicyChunker(BaseChunker):
    """
    Source 2 (PDF with Gemini Vision OCR / Text PDF): Markdown Header Splitter for PDF Outputs.
    Step 1: Gemini Vision OCR / PyMuPDF converts PDF pages & tables into structured Markdown (`#`, `##`, tables).
    Step 2: MarkdownHeaderTextSplitter splits on Markdown sections (`#`, `##`, `###`) preserving complete diagnostic steps and SLA tables.
    """

    def __init__(self, chunk_size: int = 600, chunk_overlap: int = 100):
        self.headers_to_split_on = [
            ("#", "Header 1"),
            ("##", "Header 2"),
            ("###", "Header 3"),
        ]
        self.md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=self.headers_to_split_on, strip_headers=False)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n- ", "\n", ". "]
        )

    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        doc_tag = os.path.basename(document.source_path).replace(".", "_")
        intent = get_intent_for_policy(document.policy_type)

        try:
            md_header_docs = self.md_splitter.split_text(document.raw_text)
        except Exception:
            md_header_docs = []

        if md_header_docs:
            for doc in md_header_docs:
                splits = self.text_splitter.split_text(doc.page_content)
                header_title = doc.metadata.get("Header 2") or doc.metadata.get("Header 1") or document.title
                for part in splits:
                    content = (
                        f"[SOURCE: PDF_VISION_OCR] [INTENT: {intent}]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"SECTION: {header_title}\n"
                        f"DIAGNOSTIC & SLA DISPATCH RULES:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"pdf_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="PDF_VISION_OCR",
                            policy_type=document.policy_type,
                            intent_category=intent,
                            section_title=header_title,
                            page_number=1,
                            metadata={
                                "format": "pdf",
                                "intent": intent,
                                "splitter": "LangChain_MarkdownHeaderTextSplitter",
                                "ocr_engine": "gemini-vision",
                            },
                        )
                    )
                    chunk_idx += 1
        else:
            for sec in document.sections:
                splits = self.text_splitter.split_text(sec.get("content", ""))
                for part in splits:
                    content = (
                        f"[SOURCE: PDF_VISION_OCR] [INTENT: {intent}]\n"
                        f"DOCUMENT: {document.title}\n"
                        f"SECTION: {sec['section_title']}\n"
                        f"DIAGNOSTIC & SLA DISPATCH RULES:\n{part}"
                    )
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"pdf_{doc_tag}_{chunk_idx}",
                            content=content,
                            source=document.source_path,
                            source_modality="PDF_VISION_OCR",
                            policy_type=document.policy_type,
                            intent_category=intent,
                            section_title=sec["section_title"],
                            page_number=sec.get("page_number", 1),
                            metadata={"format": "pdf", "intent": intent, "splitter": "LangChain_RecursiveCharacter"},
                        )
                    )
                    chunk_idx += 1

        logger.info(
            f"LangChain Markdown-Aware WifiPolicyChunker produced {len(chunks)} chunks for {document.source_path}."
        )
        return chunks


class BillingPolicyChunker(BaseChunker):
    """
    Source 3 (DOCX): Clause-Aware Recursive Text Splitter.
    Preserves legal clauses, financial schedules, installation procedures, and credit rules.
    """

    def __init__(self, chunk_size: int = 450, chunk_overlap: int = 60):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". "]
        )

    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        doc_tag = os.path.basename(document.source_path).replace(".", "_")
        intent = get_intent_for_policy(document.policy_type)

        for sec in document.sections:
            sec_text = sec.get("content", "")
            split_texts = self.text_splitter.split_text(sec_text)

            for part in split_texts:
                content = (
                    f"[SOURCE: WORD_DOCX] [INTENT: {intent}]\n"
                    f"DOCUMENT: {document.title}\n"
                    f"CLAUSE / TOPIC: {sec['section_title']}\n"
                    f"POLICY RULES & CRITERIA:\n{part}"
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"docx_{doc_tag}_{chunk_idx}",
                        content=content,
                        source=document.source_path,
                        source_modality="WORD_DOCX",
                        policy_type=document.policy_type,
                        intent_category=intent,
                        section_title=sec["section_title"],
                        page_number=sec.get("page_number", 1),
                        metadata={"format": "docx", "intent": intent, "splitter": "LangChain_ClauseSplitter"},
                    )
                )
                chunk_idx += 1

        logger.info(f"LangChain BillingPolicyChunker produced {len(chunks)} chunks for {document.source_path}.")
        return chunks


class XMLPolicyChunker(BaseChunker):
    """
    Source 5 (XML): Tariff and SLA contract splitter for hierarchical XML policies.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 80):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " "]
        )

    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
        chunks = []
        chunk_idx = 1
        doc_tag = os.path.basename(document.source_path).replace(".", "_")
        intent = get_intent_for_policy(document.policy_type)

        for sec in document.sections:
            sec_text = sec.get("content", "")
            split_texts = self.text_splitter.split_text(sec_text)

            for part in split_texts:
                content = (
                    f"[SOURCE: LOCAL_XML] [INTENT: {intent}]\n"
                    f"DOCUMENT: {document.title}\n"
                    f"SECTION: {sec['section_title']}\n"
                    f"SPECIFICATIONS & RULES:\n{part}"
                )
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"xml_{doc_tag}_{chunk_idx}",
                        content=content,
                        source=document.source_path,
                        source_modality="LOCAL_XML",
                        policy_type=document.policy_type,
                        intent_category=intent,
                        section_title=sec["section_title"],
                        page_number=sec.get("page_number", 1),
                        metadata={"format": "xml", "intent": intent, "splitter": "LangChain_XMLRecursive"},
                    )
                )
                chunk_idx += 1

        logger.info(f"LangChain XMLPolicyChunker produced {len(chunks)} chunks for {document.source_path}.")
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
            chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ". ", " | ", " "]
        )

    def chunk(self, document: ExtractedDocument) -> list[DocumentChunk]:
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
                        metadata={
                            "format": "web_scraped",
                            "intent": "PLANS_AND_OFFERS",
                            "splitter": "LangChain_WebSemanticSplitter",
                            "url": document.source_path,
                        },
                    )
                )
                chunk_idx += 1

        logger.info(f"LangChain WebScrapedPolicyChunker produced {len(chunks)} chunks.")
        return chunks
