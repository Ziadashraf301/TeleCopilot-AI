import pytest

from telecopilot.agent.assist_service import AgentAssistService
from telecopilot.api.dependencies import (
    get_agent_assist_service,
    get_cohere_service,
    get_gemini_service,
    get_hybrid_retriever,
    get_ingestion_service,
    get_sparse_model,
    get_vector_repository,
)
from telecopilot.kb.ingestion_service import IngestionService
from telecopilot.kb.repositories.base import BaseVectorRepository
from telecopilot.kb.retrieval import HybridRetriever
from telecopilot.kb.sparse import SparseEmbeddingModel
from telecopilot.llm.cohere import CohereService
from telecopilot.llm.gemini import GeminiService


@pytest.fixture
def fake_gemini_client(monkeypatch):
    """CI has no GEMINI_API_KEY: give GeminiService a stand-in client so wiring can be tested offline."""
    from telecopilot.core.singletons import SingletonsManager

    monkeypatch.setattr(SingletonsManager, "get_gemini_client", classmethod(lambda cls: object()))


def test_dependency_injection_singletons(fake_gemini_client):
    """Verify dependencies module instantiates and caches singleton instances."""
    repo1 = get_vector_repository()
    repo2 = get_vector_repository()
    assert isinstance(repo1, BaseVectorRepository)
    assert repo1 is repo2  # Verified singleton instance

    cohere1 = get_cohere_service()
    cohere2 = get_cohere_service()
    assert isinstance(cohere1, CohereService)
    assert cohere1 is cohere2

    gemini1 = get_gemini_service()
    gemini2 = get_gemini_service()
    assert isinstance(gemini1, GeminiService)
    assert gemini1 is gemini2

    sparse1 = get_sparse_model()
    sparse2 = get_sparse_model()
    assert isinstance(sparse1, SparseEmbeddingModel)
    assert sparse1 is sparse2

    ingest_svc = get_ingestion_service()
    assert isinstance(ingest_svc, IngestionService)

    retriever = get_hybrid_retriever()
    assert isinstance(retriever, HybridRetriever)
    assert retriever.sparse_model is sparse1  # shares the singleton BM25 model

    assist_svc = get_agent_assist_service()
    assert isinstance(assist_svc, AgentAssistService)
