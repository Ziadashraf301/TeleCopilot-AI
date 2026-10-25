import pytest
from fakes import FakeCohereService, FakeGeminiService, FakeVectorRepository

from telecopilot.api.main import app
from telecopilot.core.singletons import SingletonsManager
from telecopilot.dependencies import get_agent_assist_service
from telecopilot.services.agent_assist_service import AgentAssistService


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
