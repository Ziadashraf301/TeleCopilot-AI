import json
from collections.abc import AsyncIterator, Iterator
from typing import Any

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.core.singletons import SingletonsManager

logger = get_logger()
settings = get_settings()


class GeminiService:
    """
    Service for orchestrating Google Gemini LLM synthesis.
    Model configured via settings.LLM_MODEL.

    Methods:
      generate_agent_solution()       — sync, JSON mode, returns full structured dict
      generate_reply_stream()         — sync iterator, used by batch endpoint only
      generate_reply_stream_async()   — ASYNC generator, true token-by-token SSE streaming

    Fail-fast: no fallback logic. Any error propagates immediately.
    """

    def __init__(self):
        self.model = settings.LLM_MODEL
        self.client = SingletonsManager.get_gemini_client()
        if not self.client:
            raise RuntimeError(
                "Gemini client could not be initialised. Ensure GEMINI_API_KEY is set correctly in your .env file."
            )

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context_str(retrieved_contexts: list[dict[str, Any]]) -> str:
        """Format retrieved policy chunks into a numbered context block for the prompt."""
        parts = []
        for idx, ctx in enumerate(retrieved_contexts):
            parts.append(
                f"\n--- SOURCE [{idx + 1}] ---\n"
                f"Modality: {ctx.get('source_modality')}\n"
                f"Intent: {ctx.get('intent_category')}\n"
                f"Policy: {ctx.get('policy_type')}\n"
                f"Section: {ctx.get('section_title')}\n"
                f"Document: {ctx.get('source')}\n"
                f"Content: {ctx.get('content')}\n"
            )
        return "".join(parts)

    @staticmethod
    def _build_stream_prompt(customer_query: str, context_str: str) -> str:
        return (
            "You are an expert AI Telecom Customer Support Copilot assisting a human "
            "Customer Service Representative (CSR).\n"
            "Analyze the customer problem and verified policies below, and generate a polite, "
            "empathetic, and professional message ready to send directly to the customer "
            "explaining the resolution and actionable steps.\n\n"
            f'CUSTOMER PROBLEM:\n"{customer_query}"\n\n'
            f"VERIFIED COMPANY POLICIES:\n{context_str}\n\n"
            "Respond with ONLY the polite, empathetic message ready to send to the customer. "
            "Do NOT include markdown code blocks, JSON tags, or introductory remarks like "
            "'Here is the reply:'."
        )

    # ------------------------------------------------------------------
    # Batch JSON synthesis  (sync — used by both endpoints via to_thread)
    # ------------------------------------------------------------------

    def generate_agent_solution(
        self,
        customer_query: str,
        retrieved_contexts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Call Gemini in JSON mode to synthesise a fully structured CSR solution.
        Raises on any Gemini API error — no fallback.
        """
        context_str = self._build_context_str(retrieved_contexts)

        prompt = f"""
You are an expert AI Telecom Customer Support Assistant assisting a human Customer Service Representative (CSR).
Analyze the customer problem and the verified company policies below to produce a structured JSON response.

CUSTOMER PROBLEM:
"{customer_query}"

VERIFIED COMPANY POLICIES:
{context_str}

Respond STRICTLY in valid JSON format with the following keys:
{{
  "customer_issue_summary": "Short 1-sentence summary of what the customer is asking",
  "policy_applied": "Exact name of policy applied",
  "resolution_status": "APPROVED / IN_PROGRESS / REQUIRES_VERIFICATION / ESCALATE",
  "actionable_agent_steps": ["Step 1 for the agent", "Step 2 for the agent"],
  "suggested_customer_reply": "Polite, empathetic message ready to send to the customer",
  "policy_citations": [{{"document": "...", "section": "...", "clause_summary": "..."}}],
  "sla_or_credit_details": "Details on fee waivers, delivery times, or SLAs"
}}
"""
        response = self.client.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        parsed = json.loads(response.text)
        logger.info(f"Gemini batch solution generated for query: '{customer_query[:60]}...'")
        return parsed

    # ------------------------------------------------------------------
    # Sync streaming  (kept for reference — NOT used by SSE endpoint)
    # ------------------------------------------------------------------

    def generate_reply_stream(
        self,
        customer_query: str,
        retrieved_contexts: list[dict[str, Any]],
    ) -> Iterator[str]:
        """Sync streaming — only use in non-async contexts. Prefer generate_reply_stream_async."""
        context_str = self._build_context_str(retrieved_contexts)
        prompt = self._build_stream_prompt(customer_query, context_str)
        response = self.client.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text

    # ------------------------------------------------------------------
    # TRUE async streaming  (used by SSE endpoint — real token-by-token)
    # ------------------------------------------------------------------

    async def generate_reply_stream_async(
        self,
        customer_query: str,
        retrieved_contexts: list[dict[str, Any]],
    ) -> AsyncIterator[str]:
        """
        Async generator that streams CSR reply tokens directly from Gemini.
        Uses generate_content_async(stream=True) so each token is yielded
        the instant Gemini produces it — no buffering, no thread pool.

        Raises on any Gemini API error — no fallback.
        """
        context_str = self._build_context_str(retrieved_contexts)
        prompt = self._build_stream_prompt(customer_query, context_str)

        # Native async Gemini streaming — event loop is never blocked
        response = await self.client.generate_content_async(prompt, stream=True)
        async for chunk in response:
            if chunk.text:
                yield chunk.text
