import pytest
from fakes import FakeCohereService, FakeGeminiService, FakeVectorRepository
from qdrant_client import QdrantClient

from telecopilot.agent.assist_service import AgentAssistService
from telecopilot.api.dependencies import get_agent_assist_service, get_vector_repository
from telecopilot.api.main import app
from telecopilot.core.singletons import SingletonsManager
from telecopilot.kb.retrieval import HybridRetriever
from telecopilot.kb.sparse import SparseEmbeddingModel


@pytest.fixture
def mocked_agent_assist(monkeypatch):
    """Override the Agent Assist dependency with a real service wired to fake backends."""
    monkeypatch.setattr(SingletonsManager, "get_langfuse_client", classmethod(lambda cls: None))
    retriever = HybridRetriever(FakeVectorRepository(), FakeCohereService(), SparseEmbeddingModel())
    service = AgentAssistService(retriever=retriever, gemini_service=FakeGeminiService())
    app.dependency_overrides[get_agent_assist_service] = lambda: service
    yield service
    app.dependency_overrides.pop(get_agent_assist_service, None)


@pytest.fixture(autouse=True)
def embedded_qdrant(monkeypatch):
    """Every test gets its own in-process Qdrant, so no test can reach (or write into) a real server."""
    client = QdrantClient(":memory:")
    monkeypatch.setattr(SingletonsManager, "get_qdrant_client", classmethod(lambda cls: client))
    get_vector_repository.cache_clear()
    yield client
    get_vector_repository.cache_clear()
