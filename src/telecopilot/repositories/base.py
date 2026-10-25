from abc import ABC, abstractmethod
from typing import List, Optional
from telecopilot.models.document_models import DocumentChunk, SearchResult, SparseVectorData


class BaseVectorRepository(ABC):
    """Abstract Vector Repository interface for storing and searching embeddings."""

    @abstractmethod
    def initialize_collection(self) -> None:
        """Create or ensure vector collection exists with dense and sparse vector schemas."""
        pass

    @abstractmethod
    def upsert_chunks(self, chunks: List[DocumentChunk]) -> int:
        """Insert or update chunks into the unified Qdrant vector collection with dense + sparse vectors."""
        pass

    @abstractmethod
    def hybrid_search(
        self,
        query: str,
        query_dense_vector: List[float],
        query_sparse_vector: Optional[SparseVectorData] = None,
        top_k: int = 5,
        policy_filter: Optional[str] = None,
        intent_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """Execute true hybrid search combining Dense (Cohere) + Sparse (BM25) with Reciprocal Rank Fusion (RRF)."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return total number of indexed vectors."""
        pass
