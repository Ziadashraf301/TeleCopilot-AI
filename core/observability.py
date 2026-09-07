import time
import json
from typing import Optional, Dict, Any
from config.settings import get_settings
from core.singletons import SingletonsManager
from core.logger import get_logger

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
    Production Langfuse Observability Tracer with token & cost analytics.
    """

    @staticmethod
    def trace_agent_assist(query: str, session_id: Optional[str] = None):
        """Create a new Langfuse trace for agent assist resolution."""
        langfuse = SingletonsManager.get_langfuse_client()
        if langfuse:
            try:
                if hasattr(langfuse, "trace"):
                    return langfuse.trace(
                        name="agent_assist_solve",
                        session_id=session_id or f"session_{int(time.time())}",
                        input={"query": query},
                        tags=["customer_service", "telecom", "rag", "intent_attribution"]
                    )
                elif hasattr(langfuse, "create_trace"):
                    return langfuse.create_trace(
                        name="agent_assist_solve",
                        session_id=session_id or f"session_{int(time.time())}",
                        input={"query": query},
                        tags=["customer_service", "telecom", "rag", "intent_attribution"]
                    )
            except Exception as e:
                logger.warning(f"Error creating Langfuse trace: {e}")
        return None

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
            try:
                trace.generation(
                    name=name,
                    model=model,
                    input=input_data,
                    output=output_data,
                    usage={
                        "prompt_tokens": p_tokens,
                        "completion_tokens": c_tokens,
                        "total_tokens": total_tokens,
                    },
                    usage_details={
                        "input": p_tokens,
                        "output": c_tokens,
                        "total": total_tokens,
                    },
                    cost=cost_usd,
                    metadata={
                        "latency_seconds": round(latency, 3),
                        "cost_currency": "USD",
                        "estimated_cost_usd": cost_usd
                    }
                )
                # Flush buffer to send trace immediately to Langfuse Cloud
                langfuse = SingletonsManager.get_langfuse_client()
                if langfuse and hasattr(langfuse, "flush"):
                    langfuse.flush()
            except Exception as e:
                logger.warning(f"Failed to log generation to Langfuse: {e}")

        return {
            "prompt_tokens": p_tokens,
            "completion_tokens": c_tokens,
            "total_tokens": total_tokens,
            "estimated_cost_usd": cost_usd
        }
