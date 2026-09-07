import time
from typing import Dict, Any, Optional, List
from config.settings import get_settings
from core.logger import get_logger
from core.observability import ObservabilityTracer
from repositories.base import BaseVectorRepository, SparseVectorData
from services.cohere_service import CohereService
from services.gemini_service import GeminiService
from services.sparse_embedding_model import SparseEmbeddingModel

logger = get_logger()
settings = get_settings()


class AgentAssistService:
    """
    Core RAG Service coordinating Customer Service Agent problem resolution across 4 sources:
    1. Query Dense Embedding (Cohere).
    2. Query Sparse Embedding (BM25 Sparse Model).
    3. Dual-Vector Hybrid Search (Qdrant Dense + Sparse Fusion).
    4. Re-ranking (Cohere Reranker).
    5. Structured Answer Synthesis with Intent Category & Citations (Gemini).
    6. Observability Tracing with Token & Cost Analytics (Langfuse).
    """

    def __init__(
        self,
        vector_repo: BaseVectorRepository,
        cohere_service: CohereService,
        gemini_service: GeminiService,
    ):
        self.vector_repo = vector_repo
        self.cohere_service = cohere_service
        self.gemini_service = gemini_service
        self.sparse_model = SparseEmbeddingModel()

    def solve_customer_problem(
        self,
        customer_query: str,
        session_id: Optional[str] = None,
        policy_filter: Optional[str] = None,
        intent_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Solves customer issue across the 4 sources, computes tokens & cost, and returns full metrics."""
        start_time = time.time()
        logger.info(f"Solving customer problem: '{customer_query}' (Intent Filter: {intent_filter})")

        # 1. Start Langfuse Observability Trace
        trace = ObservabilityTracer.trace_agent_assist(customer_query, session_id)

        # 2. Embed Query: Dense Vector (Cohere) + Sparse Vector (BM25)
        query_dense_vector = self.cohere_service.get_embedding(customer_query, input_type="search_query")
        sparse_vec = self.sparse_model.embed_text(customer_query)
        query_sparse_vector = SparseVectorData(indices=sparse_vec.indices, values=sparse_vec.values)

        # 3. True Hybrid Search (Dense + Sparse) in Qdrant Vector Repository
        search_results = self.vector_repo.hybrid_search(
            query=customer_query,
            query_dense_vector=query_dense_vector,
            query_sparse_vector=query_sparse_vector,
            top_k=settings.RETRIEVAL_TOP_K,
            policy_filter=policy_filter,
            intent_filter=intent_filter
        )

        if not search_results:
            logger.warning("No relevant policy chunks found in vector database.")
            return {
                "customer_issue_summary": "Inquiry could not be matched with current policies.",
                "detected_intent": "UNKNOWN",
                "primary_source_modality": "NONE",
                "policy_applied": "None",
                "resolution_status": "ESCALATE",
                "actionable_agent_steps": ["Escalate ticket to Senior Support Lead for manual review."],
                "suggested_customer_reply": "Thank you for contacting us. I am transferring your request to a senior specialist who will assist you shortly.",
                "policy_citations": [],
                "sla_or_credit_details": "N/A",
                "execution_time_seconds": round(time.time() - start_time, 3),
                "retrieved_chunks_count": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0
            }

        # 4. Rerank Candidates via Cohere Rerank
        candidate_docs = [r.content for r in search_results]
        rerank_results = self.cohere_service.rerank(
            query=customer_query,
            documents=candidate_docs,
            top_n=settings.RERANK_TOP_N
        )

        top_contexts = []
        for item in rerank_results:
            original_idx = item["index"]
            res = search_results[original_idx]
            top_contexts.append({
                "chunk_id": res.chunk_id,
                "content": res.content,
                "source": res.source,
                "source_modality": res.source_modality,
                "policy_type": res.policy_type,
                "intent_category": res.intent_category,
                "section_title": res.section_title,
                "page_number": res.page_number,
                "relevance_score": item["relevance_score"]
            })

        top_hit = top_contexts[0]
        detected_intent = top_hit.get("intent_category", "GENERAL")
        primary_modality = top_hit.get("source_modality", "LOCAL")

        # 5. Synthesize Solution via Gemini Service
        gen_start = time.time()
        solution = self.gemini_service.generate_agent_solution(customer_query, top_contexts)
        gen_latency = time.time() - gen_start

        # Enhance citations with intent and modality fields
        citations = []
        for c in top_contexts[:3]:
            citations.append({
                "document": c.get("source", ""),
                "source_modality": c.get("source_modality", "LOCAL"),
                "intent_category": c.get("intent_category", "GENERAL"),
                "section": c.get("section_title", ""),
                "clause_summary": c.get("content", "")[:180] + "..."
            })

        solution["detected_intent"] = detected_intent
        solution["primary_source_modality"] = primary_modality
        solution["policy_citations"] = citations

        # 6. Log Langfuse Telemetry with Tokens & Estimated USD Cost
        metrics = ObservabilityTracer.log_generation(
            trace=trace,
            name="gemini_agent_assist_synthesis",
            input_data={"query": customer_query, "contexts": top_contexts, "intent": detected_intent},
            output_data=solution,
            model=settings.LLM_MODEL,
            latency=gen_latency
        )

        total_latency = time.time() - start_time
        solution["execution_time_seconds"] = round(total_latency, 3)
        solution["retrieved_chunks_count"] = len(top_contexts)
        solution["total_tokens"] = metrics["total_tokens"]
        solution["estimated_cost_usd"] = metrics["estimated_cost_usd"]

        logger.info(
            f"Problem resolved in {total_latency:.3f}s | "
            f"Intent: {detected_intent} | Tokens: {metrics['total_tokens']} | Cost: ${metrics['estimated_cost_usd']:.6f}"
        )
        return solution
