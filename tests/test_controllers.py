from fastapi.testclient import TestClient

from telecopilot.api.main import app

client = TestClient(app)


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
        "policy_filter": "sim_replacement",
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
        "policy_filter": "sim_replacement",
    }
    response = client.post("/api/agent-assist/solve/stream", json=payload)
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    content = response.text
    assert "event: context_ready" in content
    assert "event: token" in content
    assert "event: done" in content
