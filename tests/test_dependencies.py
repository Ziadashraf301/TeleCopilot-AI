import pytest
from dependencies import (
    get_vector_repository,
    get_cohere_service,
    get_gemini_service,
    get_sparse_model,
    get_ingestion_service,
    get_agent_assist_service,
)
from repositories.base import BaseVectorRepository
from services.cohere_service import CohereService
from services.gemini_service import GeminiService
from services.sparse_embedding_model import SparseEmbeddingModel
from services.ingestion_service import IngestionService
from services.agent_assist_service import AgentAssistService


@pytest.fixture
def fake_gemini_client(monkeypatch):
    """CI has no GEMINI_API_KEY: give GeminiService a stand-in client so wiring can be tested offline."""
    from core.singletons import SingletonsManager
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

    assist_svc = get_agent_assist_service()
    assert isinstance(assist_svc, AgentAssistService)
