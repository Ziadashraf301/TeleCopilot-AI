import pytest
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from telecopilot.core.singletons import SingletonsManager
from telecopilot.kb.models import DocumentChunk
from telecopilot.kb.repositories.qdrant import QdrantVectorRepository


def test_qdrant_repository_upsert_and_search():
    """Stores chunks and runs hybrid search on the embedded Qdrant (conftest.embedded_qdrant)."""
    repo = QdrantVectorRepository()

    test_chunk = DocumentChunk(
        chunk_id="test_sim_1",
        content="Instant eSIM activation is 100% free and takes 5 minutes.",
        source="sim_policy.html",
        source_modality="LOCAL_HTML",
        policy_type="sim_replacement",
        intent_category="SIM_MANAGEMENT",
        section_title="eSIM Activation Guide",
        page_number=1,
        dense_vector=[0.1] * 1024,
    )

    assert repo.upsert_chunks([test_chunk]) == 1
    assert repo.upsert_chunks([test_chunk]) == 1  # same chunk id overwrites, never duplicates
    assert repo.count() == 1

    results = repo.hybrid_search(query="How to activate eSIM for free?", query_dense_vector=[0.1] * 1024, top_k=2)

    assert len(results) >= 1
    assert results[0].chunk_id == "test_sim_1"
    assert "eSIM" in results[0].content


def test_unreachable_qdrant_raises_instead_of_switching_to_memory(monkeypatch):
    unreachable = QdrantClient(url="http://127.0.0.1:9", timeout=1)  # port 9: nothing listens there
    monkeypatch.setattr(SingletonsManager, "get_qdrant_client", classmethod(lambda cls: unreachable))
    with pytest.raises(ResponseHandlingException):  # qdrant-client's wrapper around the refused connection
        QdrantVectorRepository()


class RacingClient:
    """The collection does not exist when checked, but another process creates it before we do."""

    def __init__(self, status_code: int):
        self.status_code = status_code

    def collection_exists(self, name):
        return False

    def create_collection(self, **kwargs):
        raise UnexpectedResponse(status_code=self.status_code, reason_phrase="", content=b"", headers={})


def test_collection_created_concurrently_is_not_an_error(monkeypatch):
    monkeypatch.setattr(SingletonsManager, "get_qdrant_client", classmethod(lambda cls: RacingClient(409)))
    QdrantVectorRepository()  # 409 Conflict: the other creator won; nothing to do


def test_other_collection_creation_errors_propagate(monkeypatch):
    monkeypatch.setattr(SingletonsManager, "get_qdrant_client", classmethod(lambda cls: RacingClient(500)))
    with pytest.raises(UnexpectedResponse):
        QdrantVectorRepository()
