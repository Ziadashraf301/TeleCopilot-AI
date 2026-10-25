from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from telecopilot.core.logger import get_logger
from telecopilot.models.api_models import CustomerQueryRequest, AgentSolutionResponse
from telecopilot.services.agent_assist_service import AgentAssistService
from telecopilot.dependencies import get_agent_assist_service

logger = get_logger()
router = APIRouter(prefix="/api/agent-assist", tags=["Agent Assist"])


@router.post("/solve", response_model=AgentSolutionResponse)
async def solve_problem(
    request: CustomerQueryRequest,
    service: AgentAssistService = Depends(get_agent_assist_service),
):
    """
    Batch RAG endpoint — returns a complete structured JSON solution after the
    full pipeline (embed → search → rerank → Gemini JSON) completes.

    Raises HTTP 500 on any pipeline failure (no silent fallback).
    """
    try:
        solution = service.solve_customer_problem(
            customer_query=request.customer_query,
            session_id=request.session_id,
            policy_filter=request.policy_filter,
            intent_filter=request.intent_filter,
        )
        return solution
    except Exception as e:
        logger.error(f"[BATCH] Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/solve/stream")
async def solve_problem_stream(
    request: CustomerQueryRequest,
    service: AgentAssistService = Depends(get_agent_assist_service),
):
    """
    SSE streaming endpoint — yields three event types over text/event-stream:

      event: context_ready  — structured Gemini JSON metadata (action steps, intent, status)
      event: token          — one text chunk per Gemini streaming token
      event: done           — final telemetry (latency breakdown, tokens, cost)

    Headers set to prevent any proxy or browser from buffering the stream.
    Raises HTTP 500 on any pipeline failure (no silent fallback).
    """
    try:
        async def event_stream():
            async for chunk in service.solve_customer_problem_stream(
                customer_query=request.customer_query,
                session_id=request.session_id,
                policy_filter=request.policy_filter,
                intent_filter=request.intent_filter,
            ):
                yield chunk

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",   # disable nginx buffering
            },
        )
    except Exception as e:
        logger.error(f"[STREAM] Pipeline error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
