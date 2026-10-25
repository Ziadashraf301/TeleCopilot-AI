"""Offline stand-ins for external services (Qdrant, Cohere, Gemini), shared by the test modules."""

from telecopilot.kb.models import DocumentChunk, SearchResult
from telecopilot.kb.repositories.base import BaseVectorRepository

FAKE_DENSE_DIM = 1024


class FakeVectorRepository(BaseVectorRepository):
    """In-memory repository returning a fixed SIM policy chunk and recording upserts (no Qdrant needed)."""

    def __init__(self) -> None:
        self.upserted: list[DocumentChunk] = []

    def initialize_collection(self) -> None:
        pass

    def upsert_chunks(self, chunks: list[DocumentChunk]) -> int:
        self.upserted.extend(chunks)
        return len(chunks)

    def hybrid_search(
        self, query, query_dense_vector, query_sparse_vector=None, top_k=5, policy_filter=None, intent_filter=None
    ) -> list[SearchResult]:
        return [
            SearchResult(
                chunk_id="html_sim_replacement_policy_html_1",
                content="Lost or stolen phones: a replacement SIM is issued in-store after ID verification.",
                source="data/raw/sim_replacement_policy.html",
                source_modality="LOCAL_HTML",
                policy_type="sim_replacement",
                intent_category="SIM_MANAGEMENT",
                section_title="Lost or Stolen Device",
                score=0.9,
                page_number=1,
            )
        ]

    def count(self) -> int:
        return 1


class FakeCohereService:
    def get_embedding(self, text: str, input_type: str = "search_document") -> list[float]:
        return [0.1] * FAKE_DENSE_DIM

    def get_embeddings_batch(self, texts: list[str], input_type: str = "search_document") -> list[list[float]]:
        return [[0.1] * FAKE_DENSE_DIM for _ in texts]

    def rerank(self, query: str, documents: list[str], top_n: int = 3) -> list[dict]:
        return [{"index": i, "relevance_score": 0.95} for i in range(min(top_n, len(documents)))]


class FakeGeminiService:
    def generate_agent_solution(self, customer_query, retrieved_contexts) -> dict:
        return {
            "customer_issue_summary": "Customer lost phone and needs a replacement SIM.",
            "policy_applied": "SIM Replacement Policy",
            "resolution_status": "RESOLVED",
            "actionable_agent_steps": ["Verify customer ID", "Block old SIM", "Issue replacement SIM"],
            "suggested_customer_reply": "We can issue a replacement SIM today after verifying your ID.",
            "sla_or_credit_details": "Same-day replacement.",
        }

    async def generate_reply_stream_async(self, customer_query, retrieved_contexts):
        for token in ["We can ", "replace ", "your SIM today."]:
            yield token
