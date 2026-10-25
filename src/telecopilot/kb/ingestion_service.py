import os
from typing import Any

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.kb.factories import ChunkerFactory, ExtractorFactory
from telecopilot.kb.models import DocumentChunk, ExtractedDocument
from telecopilot.kb.repositories.base import BaseVectorRepository
from telecopilot.kb.sparse import SparseEmbeddingModel
from telecopilot.llm.cohere import CohereService

logger = get_logger()

# Official live website URLs to ingest directly (Zero local data folder)
DEFAULT_ONLINE_SOURCES = [
    "https://www.te.eg/",
    "https://www.te.eg/web/guest/personal/services/fixed-broadband",
    "https://www.te.eg/web/guest/personal/services/mobile-call-services",
    "https://www.te.eg/web/guest/personal/services/international-roaming",
]


class IngestionService:
    """
    Zero-Disk Ingestion Service:
    Scrapes live web URLs directly in-memory, chunks them with specialized chunking,
    generates Dense (Cohere) + Sparse (BM25) vector embeddings, and inserts them directly into Qdrant.
    No local data/ folders required.
    """

    def __init__(
        self, vector_repo: BaseVectorRepository, cohere_service: CohereService, sparse_model: SparseEmbeddingModel
    ):
        self.vector_repo = vector_repo
        self.cohere_service = cohere_service
        self.sparse_model = sparse_model

    def _index_source(self, source: str) -> tuple[ExtractedDocument, list[DocumentChunk], int]:
        """Extract, chunk, embed (dense + sparse) and upsert one URL or file. Returns (document, chunks, upserted)."""
        extracted_doc = ExtractorFactory.get_extractor(source).extract(source)
        chunks = ChunkerFactory.get_chunker(extracted_doc.policy_type).chunk(extracted_doc)
        if not chunks:
            return extracted_doc, chunks, 0

        texts = [chunk.content for chunk in chunks]
        dense_embeddings = self.cohere_service.get_embeddings_batch(texts, input_type="search_document")
        sparse_embeddings = self.sparse_model.embed_batch(texts)
        for chunk, dense, sparse in zip(chunks, dense_embeddings, sparse_embeddings, strict=True):
            chunk.dense_vector = dense
            chunk.sparse_vector = sparse

        return extracted_doc, chunks, self.vector_repo.upsert_chunks(chunks)

    def ingest_url(self, target_url: str) -> dict[str, Any]:
        """Scrapes a live website URL in-memory and indexes it directly into Qdrant."""
        logger.info(f"Starting in-memory scrape & ingestion for: {target_url}")
        extracted_doc, chunks, upserted_count = self._index_source(target_url)
        if not chunks:
            logger.warning(f"No chunks extracted from {target_url}")
            return {"file_path": target_url, "chunks_count": 0, "status": "EMPTY"}

        logger.info(f"Successfully scraped & indexed {upserted_count} chunks from {target_url} into Qdrant.")
        return {
            "source_url": target_url,
            "document_title": extracted_doc.title,
            "policy_type": extracted_doc.policy_type,
            "intent_category": chunks[0].intent_category,
            "chunks_count": upserted_count,
            "vector_types": ["dense_cohere_1024", "sparse_bm25_lexical"],
            "status": "SUCCESS",
        }

    def ingest_file(self, file_path: str) -> dict[str, Any]:
        """Extracts and indexes a local policy file (HTML, PDF, DOCX) into Qdrant."""
        logger.info(f"Ingesting local document: {file_path}")
        extracted_doc, chunks, upserted_count = self._index_source(file_path)
        if not chunks:
            return {"file_path": file_path, "chunks_count": 0, "status": "EMPTY"}

        return {
            "source": file_path,
            "document_title": extracted_doc.title,
            "policy_type": extracted_doc.policy_type,
            "intent_category": chunks[0].intent_category,
            "chunks_count": upserted_count,
            "status": "SUCCESS",
        }

    def ingest_all_default_policies(self, url_list: list[str] = None) -> list[dict[str, Any]]:
        """Ingests all 10 policy modalities (HTML, XML, DOCX, PDF, Scanned Image PDF) and live Web URLs into Qdrant."""
        results = []

        # 1. Dynamically discover and ingest all files in data/raw/
        raw_dir = str(get_settings().DATA_RAW_DIR.resolve())

        supported_exts = [".html", ".xml", ".docx", ".pdf"]
        local_files = []

        if os.path.exists(raw_dir):
            for file_name in sorted(os.listdir(raw_dir)):
                ext = os.path.splitext(file_name)[1].lower()
                if ext in supported_exts:
                    local_files.append(os.path.join(raw_dir, file_name))

        logger.info(f"Discovered {len(local_files)} local policy files in {raw_dir}: {local_files}")

        for f in local_files:
            try:
                res = self.ingest_file(f)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to ingest local policy {f}: {e}")
                results.append({"source": f, "error": str(e), "status": "FAILED"})

        # 2. Ingest Live Web Modality (te.eg)
        targets = url_list or DEFAULT_ONLINE_SOURCES
        for url in targets:
            try:
                res = self.ingest_url(url)
                results.append(res)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results.append({"source_url": url, "error": str(e), "status": "FAILED"})
        return results
