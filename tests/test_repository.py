import pytest
from qdrant_client import QdrantClient
from core.singletons import SingletonsManager
from repositories.base import DocumentChunk
from repositories.qdrant_repository import QdrantVectorRepository


@pytest.fixture
def in_memory_qdrant(monkeypatch):
    """Use an embedded in-memory Qdrant instance (no server / network needed)."""
    client = QdrantClient(":memory:")
    monkeypatch.setattr(SingletonsManager, "get_qdrant_client", classmethod(lambda cls: client))
    return client


def test_qdrant_repository_in_memory_fallback(in_memory_qdrant):
    """Verify Vector Repository stores chunks and executes hybrid search."""
    repo = QdrantVectorRepository()
    assert repo._is_live  # real Qdrant engine (embedded), not the list fallback

    test_chunk = DocumentChunk(
        chunk_id="test_sim_1",
        content="Instant eSIM activation is 100% free and takes 5 minutes.",
        source="sim_policy.html",
        source_modality="LOCAL_HTML",
        policy_type="sim_replacement",
        intent_category="SIM_MANAGEMENT",
        section_title="eSIM Activation Guide",
        page_number=1,
        dense_vector=[0.1] * 1024
    )

    upserted = repo.upsert_chunks([test_chunk])
    assert upserted == 1

    results = repo.hybrid_search(
        query="How to activate eSIM for free?",
        query_dense_vector=[0.1] * 1024,
        top_k=2
    )

    assert len(results) >= 1
    assert results[0].chunk_id == "test_sim_1"
    assert "eSIM" in results[0].content
