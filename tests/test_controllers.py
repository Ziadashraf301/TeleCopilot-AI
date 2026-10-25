import pytest
from fastapi.testclient import TestClient
from telecopilot.api.main import app
from telecopilot.core.singletons import SingletonsManager
from telecopilot.dependencies import get_agent_assist_service
from telecopilot.models.document_models import SearchResult
from telecopilot.repositories.base import BaseVectorRepository
from telecopilot.services.agent_assist_service import AgentAssistService

client = TestClient(app)


class FakeVectorRepository(BaseVectorRepository):
    """In-memory repository returning a fixed SIM policy chunk (no Qdrant needed)."""

    def initialize_collection(self) -> None:
        pass

    def upsert_chunks(self, chunks) -> int:
        return len(chunks)

    def hybrid_search(self, query, query_dense_vector, query_sparse_vector=None,
                      top_k=5, policy_filter=None, intent_filter=None):
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
    def get_embedding(self, text, input_type="search_document"):
        return [0.1] * 1024

    def rerank(self, query, documents, top_n=3):
        return [{"index": i, "relevance_score": 0.95} for i in range(min(top_n, len(documents)))]


class FakeGeminiService:
    def generate_agent_solution(self, customer_query, retrieved_contexts):
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


@pytest.fixture
def mocked_agent_assist(monkeypatch):
    """Override the Agent Assist dependency with a real service wired to fake backends."""
    monkeypatch.setattr(SingletonsManager, "get_langfuse_client", classmethod(lambda cls: None))
    service = AgentAssistService(
        vector_repo=FakeVectorRepository(),
        cohere_service=FakeCohereService(),
        gemini_service=FakeGeminiService(),
    )
    app.dependency_overrides[get_agent_assist_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_agent_assist_service, None)


def test_health_endpoint():
    """Test /api/health endpoint returns 200 OK and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "vector_store" in data


def test_agent_assist_solve_endpoint(mocked_agent_assist):
    """Test /api/agent-assist/solve generates grounded CSR solution."""
    payload = {
        "customer_query": "I lost my phone today and need a replacement SIM card right away.",
        "policy_filter": "sim_replacement"
    }
    response = client.post("/api/agent-assist/solve", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "suggested_customer_reply" in data
    assert "actionable_agent_steps" in data
    assert "policy_citations" in data
    assert len(data["policy_citations"]) > 0
    assert data["detected_intent"] == "SIM_MANAGEMENT"


def test_agent_assist_solve_stream_endpoint(mocked_agent_assist):
    """Test /api/agent-assist/solve/stream returns Server-Sent Events (SSE) stream."""
    payload = {
        "customer_query": "I lost my phone today and need a replacement SIM card right away.",
        "policy_filter": "sim_replacement"
    }
    response = client.post("/api/agent-assist/solve/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    assert "event: context_ready" in content
    assert "event: token" in content
    assert "event: done" in content
