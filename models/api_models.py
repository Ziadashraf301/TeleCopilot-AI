from typing import List, Optional
from pydantic import BaseModel, Field


class CustomerQueryRequest(BaseModel):
    """Request payload for CSR problem resolution."""
    customer_query: str = Field(..., description="Customer's problem or inquiry message", min_length=3)
    session_id: Optional[str] = Field(None, description="Optional CSR session identifier")
    policy_filter: Optional[str] = Field(None, description="Optional policy filter (sim_replacement, wifi_troubleshooting, billing_refund, telecom_egypt_web)")
    intent_filter: Optional[str] = Field(None, description="Optional intent filter (SIM_MANAGEMENT, WIFI_TECHNICAL_SUPPORT, BILLING_AND_PAYMENTS, PLANS_AND_OFFERS)")


class PolicyCitation(BaseModel):
    """Citation metadata identifying source, section, and intent category."""
    document: str
    source_modality: str
    intent_category: str
    section: str
    clause_summary: str


class AgentSolutionResponse(BaseModel):
    """Structured response synthesized for the Customer Service Representative."""
    customer_issue_summary: str
    detected_intent: str
    primary_source_modality: str
    policy_applied: str
    resolution_status: str
    actionable_agent_steps: List[str]
    suggested_customer_reply: str
    policy_citations: List[PolicyCitation]
    sla_or_credit_details: str
    execution_time_seconds: float
    retrieved_chunks_count: int
    total_tokens: int = Field(default=0, description="Total prompt and completion tokens processed")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated total execution cost in USD")
    latency_breakdown: Optional[dict] = Field(default_factory=dict, description="Execution time breakdown per service in seconds")


class ScrapeUrlRequest(BaseModel):
    """Request payload for scraping an online URL."""
    url: str = Field(..., description="Target website URL to scrape in-memory and index", min_length=8)


class ManualScrapeRequest(BaseModel):
    """Request payload for manual URL scraping."""
    url: str = Field(default="https://www.te.eg/", description="Web URL to manually scrape and ingest as a data source")
