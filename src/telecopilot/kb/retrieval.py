from typing import Any

from telecopilot.config.settings import get_settings
from telecopilot.kb.models import SearchResult
from telecopilot.kb.repositories.base import BaseVectorRepository, SparseVectorData
from telecopilot.kb.sparse import SparseEmbeddingModel
from telecopilot.llm.cohere import CohereService

settings = get_settings()


class HybridRetriever:
    """
    Policy retrieval for a customer query: dense (Cohere) + sparse (BM25) query embedding,
    Qdrant hybrid search, then Cohere rerank.

    The steps are separate methods so callers can time and trace each one.
    Fail-fast: no fallback logic. Any downstream error propagates immediately.
    """

    def __init__(
        self,
        vector_repo: BaseVectorRepository,
        cohere_service: CohereService,
        sparse_model: SparseEmbeddingModel,
    ):
        self.vector_repo = vector_repo
        self.cohere_service = cohere_service
        self.sparse_model = sparse_model

    def embed_query(self, customer_query: str) -> tuple[list[float], SparseVectorData]:
        """Embed query using Cohere (dense) and BM25 (sparse)."""
        query_dense_vector = self.cohere_service.get_embedding(customer_query, input_type="search_query")
        return query_dense_vector, self.sparse_model.embed_query(customer_query)

    def search(
        self,
        customer_query: str,
        dense_vec: list[float],
        sparse_vec: SparseVectorData,
        policy_filter: str | None,
        intent_filter: str | None,
    ) -> list[SearchResult]:
        """Run Qdrant hybrid search. Raises ValueError if no results found."""
        results = self.vector_repo.hybrid_search(
            query=customer_query,
            query_dense_vector=dense_vec,
            query_sparse_vector=sparse_vec,
            top_k=settings.RETRIEVAL_TOP_K,
            policy_filter=policy_filter,
            intent_filter=intent_filter,
        )
        if not results:
            raise ValueError(
                f"No relevant policy chunks found in Qdrant for query: '{customer_query}'. "
                "Ensure documents are ingested before querying."
            )
        return results

    def rerank(self, customer_query: str, search_results: list[SearchResult]) -> list[dict[str, Any]]:
        """Rerank via Cohere and return the ordered top contexts."""
        candidate_docs = [r.content for r in search_results]
        rerank_results = self.cohere_service.rerank(
            query=customer_query,
            documents=candidate_docs,
            top_n=settings.RERANK_TOP_N,
        )
        top_contexts = []
        for item in rerank_results:
            res = search_results[item["index"]]
            top_contexts.append(
                {
                    "chunk_id": res.chunk_id,
                    "content": res.content,
                    "source": res.source,
                    "source_modality": res.source_modality,
                    "policy_type": res.policy_type,
                    "intent_category": res.intent_category,
                    "section_title": res.section_title,
                    "page_number": res.page_number,
                    "relevance_score": item["relevance_score"],
                }
            )
        return top_contexts
