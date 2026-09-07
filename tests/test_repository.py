import pytest
from repositories.base import DocumentChunk
from repositories.qdrant_repository import QdrantVectorRepository


def test_qdrant_repository_in_memory_fallback():
    """Verify Vector Repository stores chunks and executes hybrid search."""
    repo = QdrantVectorRepository()

    test_chunk = DocumentChunk(
        chunk_id="test_sim_1",
        content="Instant eSIM activation is 100% free and takes 5 minutes.",
        source="sim_policy.html",
        policy_type="sim_replacement",
        section_title="eSIM Activation Guide",
        page_number=1,
        dense_vector=[0.1] * 1024
    )

    upserted = repo.upsert_chunks([test_chunk])
    assert upserted == 1

    results = repo.hybrid_search(
        query="How to activate eSIM for free?",
        query_vector=[0.1] * 1024,
        top_k=2
    )

    assert len(results) >= 1
    assert results[0].chunk_id == "test_sim_1"
    assert "eSIM" in results[0].content
