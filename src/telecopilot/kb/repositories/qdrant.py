import uuid
from http import HTTPStatus

from qdrant_client.http import models as qmodels
from qdrant_client.http.exceptions import UnexpectedResponse

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.core.singletons import SingletonsManager
from telecopilot.kb.models import DocumentChunk, SearchResult, SparseVectorData
from telecopilot.kb.repositories.base import BaseVectorRepository

logger = get_logger()
settings = get_settings()

# How many candidates each sub-query (dense, sparse) contributes to RRF fusion, relative to top_k.
PREFETCH_FACTOR = 2


class QdrantVectorRepository(BaseVectorRepository):
    """
    Unified vector repository in Qdrant with:
    1. Dense vector indexing (Cohere 1024-dim, cosine distance)
    2. Sparse vector indexing (BM25)
    3. Payload filtering (intent_category, policy_type)
    4. Hybrid search: dense + sparse fused with Reciprocal Rank Fusion (RRF)

    Fail-fast: an unreachable Qdrant raises (at construction and on every call). There is no in-memory mode,
    because it made a down database look healthy and silently served keyword-overlap "search" results.
    """

    def __init__(self):
        self.client = SingletonsManager.get_qdrant_client()
        self.collection_name = settings.QDRANT_COLLECTION
        self.initialize_collection()

    def initialize_collection(self) -> None:
        """Create the collection with named dense + sparse vectors if it does not exist yet."""
        if self.client.collection_exists(self.collection_name):
            return
        logger.info(f"Creating Qdrant collection '{self.collection_name}' with dense (Cohere) + sparse (BM25) vectors")
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config={
                    "dense": qmodels.VectorParams(size=settings.VECTOR_DIMENSION, distance=qmodels.Distance.COSINE)
                },
                sparse_vectors_config={
                    # Qdrant computes BM25's IDF from the collection at query time (FastEmbed sends TF only)
                    "sparse": qmodels.SparseVectorParams(
                        index=qmodels.SparseIndexParams(on_disk=False), modifier=qmodels.Modifier.IDF
                    )
                },
            )
        except UnexpectedResponse as e:
            # Two processes/requests creating it at the same moment: the other one won, which is what we wanted.
            if e.status_code != HTTPStatus.CONFLICT:
                raise

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Upsert document chunks with both dense and sparse vectors."""
        if not chunks:
            return 0
        points = [self._to_point(chunk) for chunk in chunks]
        self.client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Upserted {len(points)} chunks with dense + sparse vectors into Qdrant ({self.collection_name}).")
        return len(points)

    @staticmethod
    def _to_point(chunk: DocumentChunk) -> qmodels.PointStruct:
        vector_dict = {"dense": chunk.dense_vector or [0.0] * settings.VECTOR_DIMENSION}
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
        # Deterministic id: re-ingesting a chunk overwrites it instead of duplicating it.
        return qmodels.PointStruct(
            id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)), vector=vector_dict, payload=payload
        )

    def hybrid_search(
        self,
        query: str,
        query_dense_vector: list[float],
        query_sparse_vector: SparseVectorData | None = None,
        top_k: int = 5,
        policy_filter: str | None = None,
        intent_filter: str | None = None,
    ) -> list[SearchResult]:
        conditions = []
        if policy_filter:
            conditions.append(qmodels.FieldCondition(key="policy_type", match=qmodels.MatchValue(value=policy_filter)))
        if intent_filter:
            conditions.append(
                qmodels.FieldCondition(key="intent_category", match=qmodels.MatchValue(value=intent_filter))
            )
        query_filter = qmodels.Filter(must=conditions) if conditions else None

        prefetches = [
            qmodels.Prefetch(
                query=query_dense_vector, using="dense", filter=query_filter, limit=top_k * PREFETCH_FACTOR
            )
        ]
        if query_sparse_vector and query_sparse_vector.indices:
            sparse_obj = qmodels.SparseVector(indices=query_sparse_vector.indices, values=query_sparse_vector.values)
            prefetches.append(
                qmodels.Prefetch(query=sparse_obj, using="sparse", filter=query_filter, limit=top_k * PREFETCH_FACTOR)
            )

        if len(prefetches) > 1:
            response = self.client.query_points(
                collection_name=self.collection_name,
                prefetch=prefetches,
                query=qmodels.FusionQuery(fusion=qmodels.Fusion.RRF),
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

    def ping(self) -> None:
        """Raise if the Qdrant server cannot be reached."""
        self.client.get_collections()

    def count(self) -> int:
        """Count points in the collection."""
        return self.client.count(collection_name=self.collection_name).count
