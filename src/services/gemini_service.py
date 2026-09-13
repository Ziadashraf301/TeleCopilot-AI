import json
from typing import Iterator, List, Dict, Any
from config.settings import get_settings
from core.logger import get_logger
from core.singletons import SingletonsManager

logger = get_logger()
settings = get_settings()


class GeminiService:
    """
    Service for orchestrating Google Gemini LLM synthesis.
    Model configured via settings.LLM_MODEL.
    Builds grounded prompts with strict policy source citations and drafts polite CSR responses.
    Supports both structured batch generation (JSON mode) and real-time SSE token streaming.

    Fail-fast: no fallback logic. Any error from the Gemini API propagates immediately.
    """

    def __init__(self):
        self.model = settings.LLM_MODEL
        self.client = SingletonsManager.get_gemini_client()
        if not self.client:
            raise RuntimeError(
                "Gemini client could not be initialised. "
                "Ensure GEMINI_API_KEY is set correctly in your .env file."
            )

    # ------------------------------------------------------------------
    # Shared helper
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context_str(retrieved_contexts: List[Dict[str, Any]]) -> str:
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

    # ------------------------------------------------------------------
    # Batch JSON synthesis
    # ------------------------------------------------------------------

    def generate_agent_solution(
        self,
        customer_query: str,
        retrieved_contexts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Call Gemini in JSON mode to synthesise a fully structured CSR solution.
        Returns a dict with: customer_issue_summary, policy_applied,
        resolution_status, actionable_agent_steps, suggested_customer_reply,
        policy_citations, sla_or_credit_details.

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
  "policy_applied": "Exact name of policy applied (e.g. Lost SIM Policy / WiFi Troubleshooting Policy / Courtesy Late Fee Waiver Policy)",
  "resolution_status": "APPROVED / IN_PROGRESS / REQUIRES_VERIFICATION / ESCALATE",
  "actionable_agent_steps": [
    "Step 1 for the agent to take in CRM",
    "Step 2 for the agent"
  ],
  "suggested_customer_reply": "Polite, empathetic, and professional message ready to send directly to the customer explaining the resolution",
  "policy_citations": [
    {{
      "document": "Document name or source",
      "section": "Section title",
      "clause_summary": "Brief rule summary"
    }}
  ],
  "sla_or_credit_details": "Details on fee waivers, delivery times, or dispatch SLAs"
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
    # Streaming reply
    # ------------------------------------------------------------------

    def generate_reply_stream(
        self,
        customer_query: str,
        retrieved_contexts: List[Dict[str, Any]],
    ) -> Iterator[str]:
        """
        Stream a conversational CSR draft reply token-by-token using Gemini.
        Yields raw text chunks as the model generates them.

        Raises on any Gemini API error — no fallback.
        """
        context_str = self._build_context_str(retrieved_contexts)

        prompt = f"""You are an expert AI Telecom Customer Support Copilot assisting a human Customer Service Representative (CSR).
Analyze the customer problem and verified policies below, and generate a polite, empathetic, and professional message \
ready to send directly to the customer explaining the resolution and actionable steps.

CUSTOMER PROBLEM:
"{customer_query}"

VERIFIED COMPANY POLICIES:
{context_str}

Respond with ONLY the polite, empathetic message ready to send to the customer. \
Do NOT include markdown code blocks, JSON tags, or introductory remarks like 'Here is the reply:'.
"""
        response = self.client.generate_content(prompt, stream=True)
        for chunk in response:
            if chunk.text:
                yield chunk.text
