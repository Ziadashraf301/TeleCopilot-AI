from fastapi import APIRouter, Depends, HTTPException
from core.logger import get_logger
from models.api_models import CustomerQueryRequest, AgentSolutionResponse
from services.agent_assist_service import AgentAssistService
from dependencies import get_agent_assist_service

logger = get_logger()
router = APIRouter(prefix="/api/agent-assist", tags=["Agent Assist"])


@router.post("/solve", response_model=AgentSolutionResponse)
async def solve_problem(
    request: CustomerQueryRequest,
    service: AgentAssistService = Depends(get_agent_assist_service)
):
    """
    Controller endpoint to solve customer problems:
    Performs RAG retrieval, rerank, and generates ready-to-send CSR draft reply, action steps, and policy citations.
    """
    try:
        solution = service.solve_customer_problem(
            customer_query=request.customer_query,
            session_id=request.session_id,
            policy_filter=request.policy_filter,
            intent_filter=request.intent_filter
        )
        return solution
    except Exception as e:
        logger.error(f"Error processing agent assist query: {e}")
        raise HTTPException(status_code=500, detail=str(e))
