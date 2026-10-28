from abc import ABC, abstractmethod

from telecopilot.kb.models import DocumentChunk, SearchResult, SparseVectorData


class BaseVectorRepository(ABC):
    """Abstract Vector Repository interface for storing and searching embeddings."""

    @abstractmethod
    def initialize_collection(self) -> None:
        """Create or ensure vector collection exists with dense and sparse vector schemas."""
        pass

    @abstractmethod
    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        """Insert or update chunks into the unified Qdrant vector collection with dense + sparse vectors."""
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        query_dense_vector: list[float],
        query_sparse_vector: SparseVectorData | None = None,
        top_k: int = 5,
        policy_filter: str | None = None,
        intent_filter: str | None = None,
    ) -> list[SearchResult]:
        """Execute true hybrid search combining Dense (Cohere) + Sparse (BM25) with Reciprocal Rank Fusion (RRF)."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of indexed vectors."""
        pass

    @abstractmethod
    def ping(self) -> None:
        """Raise if the vector store cannot be reached (used by /api/ready)."""
        pass
