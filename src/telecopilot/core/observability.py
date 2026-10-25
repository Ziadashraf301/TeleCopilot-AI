import time
import json
from typing import Optional, Dict, Any
from telecopilot.config.settings import get_settings
from telecopilot.core.singletons import SingletonsManager
from telecopilot.core.logger import get_logger

logger = get_logger()
settings = get_settings()

# Pricing constants per 1,000,000 tokens (USD)
MODEL_COST_PER_MILLION = {
    "gemini-3.1-flash-lite-preview": {"input": 0.075, "output": 0.30},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "embed-multilingual-v3.0": {"input": 0.10, "output": 0.00},
    "rerank-v3.5": {"search_unit": 0.002}
}


class ObservabilityTracer:
    """
    Production Langfuse Observability Tracer with token & cost analytics
    and granular span tracing for Embedder, Qdrant Hybrid Retrieval, Cohere Reranker, and Gemini LLM.

    Compatible with Langfuse Python SDK v4.x (context-manager-based API).
    """

    @staticmethod
    def trace_agent_assist(query: str, session_id: Optional[str] = None):
        """Create a new Langfuse trace for agent assist resolution.

        Returns a dict with trace metadata that other methods use to attach spans.
        """
        langfuse = SingletonsManager.get_langfuse_client()
        if langfuse:
            try:
                sid = session_id or f"session_{int(time.time())}"
                trace_id = langfuse.create_trace_id()

                # Create the root span for the entire agent assist pipeline
                root_span = langfuse.start_as_current_observation(
                    name="agent_assist_solve",
                    as_type="span",
                    trace_context={
                        "trace_id": trace_id,
                        "session_id": sid,
                    },
                    input={"query": query},
                    metadata={
                        "tags": ["customer_service", "telecom", "rag", "hybrid_search"],
                        "session_id": sid,
                    },
                    end_on_exit=False,
                )
                # Enter the context manager manually so we can end it later
                span_obj = root_span.__enter__()

                trace_ctx = {
                    "trace_id": trace_id,
                    "session_id": sid,
                    "langfuse": langfuse,
                    "root_span": span_obj,
                    "root_ctx": root_span,
                }

                logger.info(
                    f"📊 [LANGFUSE TRACE CREATED] ID: {trace_id} | Session: {sid} | Dashboard: {settings.langfuse_host_url}"
                )
                return trace_ctx
            except Exception as e:
                logger.warning(f"Error creating Langfuse trace: {e}")
        return None

    @staticmethod
    def log_span(trace, name: str, input_data: Any, output_data: Any, latency: float, metadata: Optional[Dict[str, Any]] = None):
        """Log an intermediate execution step (Embedder, Vector Search, Reranker) as a child span."""
        if not trace:
            return

        langfuse = trace.get("langfuse")
        if not langfuse:
            return

        try:
            with langfuse.start_as_current_observation(
                name=name,
                as_type="span",
                trace_context={
                    "trace_id": trace["trace_id"],
                    "session_id": trace.get("session_id"),
                },
                input=input_data,
                metadata=metadata or {},
            ) as span:
                span.update(
                    output=output_data,
                    metadata={**(metadata or {}), "latency_seconds": round(latency, 3)},
                )
        except Exception as e:
            logger.warning(f"Failed to log span '{name}' to Langfuse: {e}")

    @staticmethod
    def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on model pricing."""
        rates = MODEL_COST_PER_MILLION.get(model, MODEL_COST_PER_MILLION["gemini-3.1-flash-lite-preview"])
        input_cost = (prompt_tokens / 1_000_000.0) * rates.get("input", 0.075)
        output_cost = (completion_tokens / 1_000_000.0) * rates.get("output", 0.30)
        return round(input_cost + output_cost, 6)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimation (1 token ≈ 4 characters or 0.75 words)."""
        if not text:
            return 0
        return max(1, len(text) // 4)

    @staticmethod
    def log_generation(
        trace,
        name: str,
        input_data: Any,
        output_data: Any,
        model: str,
        latency: float,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Log generation step to Langfuse with complete token usage and financial cost calculation.
        """
        input_str = json.dumps(input_data) if isinstance(input_data, (dict, list)) else str(input_data)
        output_str = json.dumps(output_data) if isinstance(output_data, (dict, list)) else str(output_data)

        p_tokens = prompt_tokens or ObservabilityTracer.estimate_tokens(input_str)
        c_tokens = completion_tokens or ObservabilityTracer.estimate_tokens(output_str)
        total_tokens = p_tokens + c_tokens

        cost_usd = ObservabilityTracer.calculate_cost(model, p_tokens, c_tokens)

        logger.info(
            f"[{name}] Model: {model} | Latency: {latency:.3f}s | "
            f"Tokens: (In: {p_tokens}, Out: {c_tokens}, Total: {total_tokens}) | "
            f"Est. Cost: ${cost_usd:.6f} USD"
        )

        if trace:
            langfuse = trace.get("langfuse")
            if langfuse:
                try:
                    with langfuse.start_as_current_observation(
                        name=name,
                        as_type="generation",
                        trace_context={
                            "trace_id": trace["trace_id"],
                            "session_id": trace.get("session_id"),
                        },
                        model=model,
                        input=input_data,
                        usage_details={
                            "input": p_tokens,
                            "output": c_tokens,
                            "total": total_tokens,
                        },
                        cost_details={
                            "total": cost_usd,
                        },
                        metadata={
                            "latency_seconds": round(latency, 3),
                            "cost_currency": "USD",
                            "estimated_cost_usd": cost_usd,
                        },
                    ) as gen:
                        gen.update(output=output_data)
                except Exception as e:
                    logger.warning(f"Failed to log generation to Langfuse: {e}")

        return {
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost_usd
        }

    @staticmethod
    def end_trace(trace):
        """End the root trace span and flush all data to Langfuse cloud."""
        if not trace:
            return

        try:
            root_span = trace.get("root_span")
            root_ctx = trace.get("root_ctx")
            if root_span and root_ctx:
                root_ctx.__exit__(None, None, None)
        except Exception as e:
            logger.warning(f"Error ending root trace span: {e}")

        # Always flush
        try:
            langfuse = trace.get("langfuse") or SingletonsManager.get_langfuse_client()
            if langfuse and hasattr(langfuse, "flush"):
                langfuse.flush()
        except Exception as e:
            logger.warning(f"Langfuse flush error: {e}")
