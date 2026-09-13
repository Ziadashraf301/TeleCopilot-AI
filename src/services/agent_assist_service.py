import time
import json
import asyncio
from typing import AsyncIterator, Dict, Any, Optional, List
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
    Core RAG orchestrator for Customer Service Agent Assist.

    Pipeline:
      1. Dense embedding   — Cohere multilingual
      2. Sparse embedding  — BM25 (SparseEmbeddingModel)
      3. Hybrid search     — Qdrant dense + sparse fusion
      4. Neural rerank     — Cohere Rerank v3.5
      5. LLM synthesis     — Gemini (batch JSON or SSE stream)
      6. Observability     — Langfuse token & cost tracing

    Fail-fast: no fallback logic. Any downstream error propagates immediately.
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

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    def _embed_query(self, customer_query: str):
        """Embed query using Cohere (dense) and BM25 (sparse). Returns (dense_vec, sparse_vec)."""
        query_dense_vector = self.cohere_service.get_embedding(
            customer_query, input_type="search_query"
        )
        sparse_vec = self.sparse_model.embed_text(customer_query)
        query_sparse_vector = SparseVectorData(
            indices=sparse_vec.indices, values=sparse_vec.values
        )
        return query_dense_vector, query_sparse_vector

    def _hybrid_search(self, customer_query, dense_vec, sparse_vec, policy_filter, intent_filter):
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

    def _rerank(self, customer_query: str, search_results) -> List[Dict[str, Any]]:
        """Rerank via Cohere and return ordered top_contexts list."""
        candidate_docs = [r.content for r in search_results]
        rerank_results = self.cohere_service.rerank(
            query=customer_query,
            documents=candidate_docs,
            top_n=settings.RERANK_TOP_N,
        )
        top_contexts = []
        for item in rerank_results:
            res = search_results[item["index"]]
            top_contexts.append({
                "chunk_id": res.chunk_id,
                "content": res.content,
                "source": res.source,
                "source_modality": res.source_modality,
                "policy_type": res.policy_type,
                "intent_category": res.intent_category,
                "section_title": res.section_title,
                "page_number": res.page_number,
                "relevance_score": item["relevance_score"],
            })
        return top_contexts

    @staticmethod
    def _build_citations(top_contexts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Build citation list from the top 3 reranked chunks."""
        return [
            {
                "document": c.get("source", ""),
                "source_modality": c.get("source_modality", "LOCAL"),
                "intent_category": c.get("intent_category", "GENERAL"),
                "section": c.get("section_title", ""),
                "clause_summary": c.get("content", "")[:180] + "...",
            }
            for c in top_contexts[:3]
        ]

    # ------------------------------------------------------------------
    # Batch endpoint  —  POST /api/agent-assist/solve
    # ------------------------------------------------------------------

    def solve_customer_problem(
        self,
        customer_query: str,
        session_id: Optional[str] = None,
        policy_filter: Optional[str] = None,
        intent_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full RAG pipeline returning a complete structured solution dict.
        Raises on any pipeline error — no silent fallback.
        """
        start_time = time.time()
        logger.info(f"[BATCH] Solving: '{customer_query}' | intent_filter={intent_filter}")
        trace = ObservabilityTracer.trace_agent_assist(customer_query, session_id)

        try:
            # 1. Embed
            embed_start = time.time()
            dense_vec, sparse_vec = self._embed_query(customer_query)
            embed_latency = time.time() - embed_start
            ObservabilityTracer.log_span(
                trace=trace,
                name="cohere_and_bm25_query_embedding",
                input_data={"query": customer_query},
                output_data={"dense_dim": len(dense_vec), "sparse_indices_count": len(sparse_vec.indices)},
                latency=embed_latency,
                metadata={"dense_model": settings.DENSE_EMBEDDING_MODEL, "sparse_model": settings.SPARSE_EMBEDDING_MODEL},
            )

            # 2. Hybrid search
            search_start = time.time()
            search_results = self._hybrid_search(customer_query, dense_vec, sparse_vec, policy_filter, intent_filter)
            search_latency = time.time() - search_start
            ObservabilityTracer.log_span(
                trace=trace,
                name="qdrant_hybrid_vector_search",
                input_data={"top_k": settings.RETRIEVAL_TOP_K, "intent_filter": intent_filter, "policy_filter": policy_filter},
                output_data={"retrieved_candidates_count": len(search_results)},
                latency=search_latency,
                metadata={"collection": settings.QDRANT_COLLECTION},
            )

            # 3. Rerank
            rerank_start = time.time()
            top_contexts = self._rerank(customer_query, search_results)
            rerank_latency = time.time() - rerank_start
            ObservabilityTracer.log_span(
                trace=trace,
                name="cohere_neural_rerank",
                input_data={"candidates_count": len(search_results), "top_n": settings.RERANK_TOP_N},
                output_data={"reranked_top_scores": [c["relevance_score"] for c in top_contexts]},
                latency=rerank_latency,
                metadata={"rerank_model": settings.RERANK_MODEL},
            )

            detected_intent = top_contexts[0].get("intent_category", "GENERAL")
            primary_modality = top_contexts[0].get("source_modality", "LOCAL")
            citations = self._build_citations(top_contexts)

            # 4. Gemini synthesis (batch JSON)
            gen_start = time.time()
            solution = self.gemini_service.generate_agent_solution(customer_query, top_contexts)
            gen_latency = time.time() - gen_start

            # Inject Qdrant-derived fields
            solution["detected_intent"] = detected_intent
            solution["primary_source_modality"] = primary_modality
            solution["policy_citations"] = citations

            # 5. Observability
            total_latency = time.time() - start_time
            metrics = ObservabilityTracer.log_generation(
                trace=trace,
                name="gemini_agent_assist_synthesis",
                input_data={"query": customer_query, "contexts": top_contexts, "intent": detected_intent},
                output_data=solution,
                model=settings.LLM_MODEL,
                latency=gen_latency,
            )

            solution["execution_time_seconds"] = round(total_latency, 3)
            solution["retrieved_chunks_count"] = len(top_contexts)
            solution["total_tokens"] = metrics["total_tokens"]
            solution["estimated_cost_usd"] = metrics["estimated_cost_usd"]
            solution["latency_breakdown"] = {
                "query_embedding_seconds": round(embed_latency, 3),
                "qdrant_hybrid_search_seconds": round(search_latency, 3),
                "cohere_rerank_seconds": round(rerank_latency, 3),
                "gemini_llm_synthesis_seconds": round(gen_latency, 3),
                "total_seconds": round(total_latency, 3),
            }

            logger.info(
                f"[BATCH] Resolved in {total_latency:.3f}s | "
                f"intent={detected_intent} | tokens={metrics['total_tokens']} | "
                f"cost=${metrics['estimated_cost_usd']:.6f}"
            )
            return solution

        finally:
            ObservabilityTracer.end_trace(trace)

    # ------------------------------------------------------------------
    # Streaming endpoint  —  POST /api/agent-assist/solve/stream
    # ------------------------------------------------------------------

    async def solve_customer_problem_stream(
        self,
        customer_query: str,
        session_id: Optional[str] = None,
        policy_filter: Optional[str] = None,
        intent_filter: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """
        Async SSE generator — yields three event types in order:

          event: context_ready   (structured metadata from Gemini JSON call)
          event: token           (one chunk per Gemini streaming token)
          event: done            (latency + cost telemetry)

        All blocking I/O is offloaded via asyncio.to_thread so the event loop
        is never stalled. Raises on any pipeline error — no silent fallback.
        """
        start_time = time.time()
        logger.info(f"[STREAM] Solving: '{customer_query}' | intent_filter={intent_filter}")
        trace = ObservabilityTracer.trace_agent_assist(customer_query, session_id)

        try:
            # 1. Embed  (blocking → thread pool)
            embed_start = time.time()
            dense_vec, sparse_vec = await asyncio.to_thread(self._embed_query, customer_query)
            embed_latency = time.time() - embed_start

            # 2. Hybrid search  (blocking → thread pool)
            search_start = time.time()
            search_results = await asyncio.to_thread(
                self._hybrid_search, customer_query, dense_vec, sparse_vec, policy_filter, intent_filter
            )
            search_latency = time.time() - search_start

            # 3. Rerank  (blocking → thread pool)
            rerank_start = time.time()
            top_contexts = await asyncio.to_thread(self._rerank, customer_query, search_results)
            rerank_latency = time.time() - rerank_start

            detected_intent = top_contexts[0].get("intent_category", "GENERAL")
            primary_modality = top_contexts[0].get("source_modality", "LOCAL")
            citations = self._build_citations(top_contexts)

            # 4. Gemini structured metadata  (blocking JSON call → thread pool)
            structured_sol = await asyncio.to_thread(
                self.gemini_service.generate_agent_solution, customer_query, top_contexts
            )

            context_meta = {
                "customer_issue_summary": structured_sol["customer_issue_summary"],
                "detected_intent": detected_intent,
                "primary_source_modality": primary_modality,
                "policy_applied": structured_sol["policy_applied"],
                "resolution_status": structured_sol["resolution_status"],
                "actionable_agent_steps": structured_sol["actionable_agent_steps"],
                "policy_citations": citations,
                "sla_or_credit_details": structured_sol["sla_or_credit_details"],
            }

            # ── event: context_ready ─────────────────────────────────────
            yield f"event: context_ready\ndata: {json.dumps(context_meta)}\n\n"

            # 5. Stream tokens live from Gemini using native async streaming.
            #    generate_reply_stream_async() uses generate_content_async(stream=True)
            #    so each token arrives the instant Gemini produces it — zero buffering.
            gen_start = time.time()
            accumulated_text = ""

            async for token in self.gemini_service.generate_reply_stream_async(
                customer_query, top_contexts
            ):
                accumulated_text += token
                # ── event: token ─────────────────────────────────────────
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"

            gen_latency = time.time() - gen_start
            total_latency = time.time() - start_time

            # 6. Observability
            metrics = ObservabilityTracer.log_generation(
                trace=trace,
                name="gemini_agent_assist_stream",
                input_data={"query": customer_query, "intent": detected_intent},
                output_data={"suggested_customer_reply": accumulated_text},
                model=settings.LLM_MODEL,
                latency=gen_latency,
            )

            done_payload = {
                "execution_time_seconds": round(total_latency, 3),
                "retrieved_chunks_count": len(top_contexts),
                "total_tokens": metrics["total_tokens"],
                "estimated_cost_usd": metrics["estimated_cost_usd"],
                "latency_breakdown": {
                    "query_embedding_seconds": round(embed_latency, 3),
                    "qdrant_hybrid_search_seconds": round(search_latency, 3),
                    "cohere_rerank_seconds": round(rerank_latency, 3),
                    "gemini_llm_synthesis_seconds": round(gen_latency, 3),
                    "total_seconds": round(total_latency, 3),
                },
            }

            logger.info(
                f"[STREAM] Done in {total_latency:.3f}s | "
                f"intent={detected_intent} | tokens={metrics['total_tokens']} | "
                f"cost=${metrics['estimated_cost_usd']:.6f}"
            )

            # ── event: done ──────────────────────────────────────────────
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        finally:
            ObservabilityTracer.end_trace(trace)
