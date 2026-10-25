import uuid

from qdrant_client.http import models as qmodels

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.core.singletons import SingletonsManager
from telecopilot.models.document_models import DocumentChunk, SearchResult, SparseVectorData
from telecopilot.repositories.base import BaseVectorRepository

logger = get_logger()
settings = get_settings()


class QdrantVectorRepository(BaseVectorRepository):
    """
    Production-grade Unified Vector Repository in Qdrant with:
    1. Dense Vector Indexing (Cohere 1024-dim, Cosine distance)
    2. Sparse Vector Indexing (BM25 / Lexical Sparse Insertion Model)
    3. Multi-field payload indexing & filtering (intent_category, source_modality, policy_type)
    4. True Hybrid Search using Dense + Sparse Score Fusion
    """

    # Shared class-level in-memory fallback list to ensure zero-loss across instances
    _shared_in_memory_fallback: list[DocumentChunk] = []

    def __init__(self):
        self.client = SingletonsManager.get_qdrant_client()
        self.collection_name = settings.QDRANT_COLLECTION
        self._in_memory_fallback = self._shared_in_memory_fallback
        self._is_live = False
        self.initialize_collection()

    def initialize_collection(self) -> None:
        """Create Qdrant collection with named Dense + Sparse vector configurations."""
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if not exists:
                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' with Dense (Cohere) + Sparse (BM25) vector indexes..."
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config={
                        "dense": qmodels.VectorParams(size=settings.VECTOR_DIMENSION, distance=qmodels.Distance.COSINE)
                    },
                    sparse_vectors_config={
                        "sparse": qmodels.SparseVectorParams(index=qmodels.SparseIndexParams(on_disk=False))
                    },
                )
            self._is_live = True
            logger.info(f"Connected to Qdrant collection: {self.collection_name} (Dense + Sparse Hybrid ready)")
        except Exception as e:
            logger.warning(
                f"Could not connect to live Qdrant server: {e}. Running in robust In-Memory Hybrid Mock mode."
            )
            self._is_live = False

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Upsert document chunks into Qdrant containing BOTH Dense and Sparse vectors."""
        if not chunks:
            return 0

        if self._is_live:
            try:
                points = []
                for chunk in chunks:
                    dense_vec = chunk.dense_vector or [0.0] * settings.VECTOR_DIMENSION

                    vector_dict = {"dense": dense_vec}

                    if chunk.sparse_vector:
                        vector_dict["sparse"] = qmodels.SparseVector(
                            indices=chunk.sparse_vector.indices, values=chunk.sparse_vector.values
                        )

                    payload = {
                        "chunk_id": chunk.chunk_id,
                        "content": chunk.content,
                        "source": chunk.source,
                        "source_modality": chunk.source_modality,
                        "policy_type": chunk.policy_type,
                        "intent_category": chunk.intent_category,
                        "section_title": chunk.section_title,
                        "page_number": chunk.page_number,
                        "metadata": chunk.metadata,
                    }

                    points.append(
                        qmodels.PointStruct(
                            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)), vector=vector_dict, payload=payload
                        )
                    )

                self.client.upsert(collection_name=self.collection_name, points=points)
                logger.info(
                    f"Upserted {len(points)} chunks with Dense + Sparse vectors into Qdrant ({self.collection_name})."
                )
                return len(points)
            except Exception as e:
                logger.error(f"Failed to upsert Dense + Sparse points to Qdrant: {e}. Falling back to in-memory store.")

        # Fallback in-memory
        for chunk in chunks:
            self._in_memory_fallback = [c for c in self._in_memory_fallback if c.chunk_id != chunk.chunk_id]
            self._in_memory_fallback.append(chunk)
        logger.info(f"Stored {len(chunks)} chunks in unified in-memory fallback store.")
        return len(chunks)

    def hybrid_search(
        self,
        query: str,
        query_dense_vector: list[float],
        query_sparse_vector: SparseVectorData | None = None,
        top_k: int = 5,
        policy_filter: str | None = None,
        intent_filter: str | None = None,
    ) -> list[SearchResult]:
        if self._is_live:
            try:
                # 1. Build Payload Filters
                conditions = []
                if policy_filter:
                    conditions.append(
                        qmodels.FieldCondition(
                            key="policy_type",
                            match=qmodels.MatchValue(value=policy_filter),
                        )
                    )
                if intent_filter:
                    conditions.append(
                        qmodels.FieldCondition(
                            key="intent_category",
                            match=qmodels.MatchValue(value=intent_filter),
                        )
                    )

                query_filter = qmodels.Filter(must=conditions) if conditions else None

                # 2. Configure Prefetches (Sub-queries)
                prefetches = [
                    qmodels.Prefetch(
                        query=query_dense_vector,
                        using="dense",
                        filter=query_filter,
                        limit=top_k * 2,
                    )
                ]

                if query_sparse_vector and query_sparse_vector.indices:
                    sparse_obj = qmodels.SparseVector(
                        indices=query_sparse_vector.indices,
                        values=query_sparse_vector.values,
                    )
                    prefetches.append(
                        qmodels.Prefetch(
                            query=sparse_obj,
                            using="sparse",
                            filter=query_filter,
                            limit=top_k * 2,
                        )
                    )

                # 3. Single-Roundtrip Native Query + Fusion
                if len(prefetches) > 1:
                    try:
                        fusion_query = qmodels.FusionQuery(fusion=qmodels.Fusion.RRF)
                    except AttributeError:
                        fusion_query = qmodels.RrfQuery(rrf=qmodels.Rrf(k=60))

                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        prefetch=prefetches,
                        query=fusion_query,
                        limit=top_k,
                        with_payload=True,
                    )
                else:
                    response = self.client.query_points(
                        collection_name=self.collection_name,
                        query=query_dense_vector,
                        using="dense",
                        query_filter=query_filter,
                        limit=top_k,
                        with_payload=True,
                    )

                return [
                    SearchResult(
                        chunk_id=point.payload.get("chunk_id", ""),
                        content=point.payload.get("content", ""),
                        source=point.payload.get("source", ""),
                        source_modality=point.payload.get("source_modality", "LOCAL"),
                        policy_type=point.payload.get("policy_type", ""),
                        intent_category=point.payload.get("intent_category", "GENERAL"),
                        section_title=point.payload.get("section_title", ""),
                        page_number=point.payload.get("page_number"),
                        score=round(point.score, 4),
                        metadata=point.payload.get("metadata", {}),
                    )
                    for point in response.points
                ]

            except Exception as e:
                logger.error(f"Qdrant live native hybrid search failed: {e}. Falling back to in-memory search.")

        # In-memory keyword + cosine fallback
        query_words = set(query.lower().split())
        scored_chunks = []
        for c in self._in_memory_fallback:
            if policy_filter and c.policy_type != policy_filter:
                continue
            if intent_filter and c.intent_category != intent_filter:
                continue
            content_words = set(c.content.lower().split())
            overlap = len(query_words.intersection(content_words)) / max(len(query_words), 1)
            score = 0.5 + 0.5 * overlap
            scored_chunks.append((score, c))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        results = [
            SearchResult(
                chunk_id=c.chunk_id,
                content=c.content,
                source=c.source,
                source_modality=c.source_modality,
                policy_type=c.policy_type,
                intent_category=c.intent_category,
                section_title=c.section_title,
                page_number=c.page_number,
                score=score,
                metadata=c.metadata,
            )
            for score, c in scored_chunks[:top_k]
        ]
        return results

    def count(self) -> int:
        """Count points in store."""
        if self._is_live:
            try:
                return self.client.count(collection_name=self.collection_name).count
            except Exception:
                pass
        return len(self._in_memory_fallback)
