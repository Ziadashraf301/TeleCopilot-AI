from telecopilot.kb.repositories.base import DocumentChunk, SparseVectorData
from telecopilot.kb.repositories.qdrant import QdrantVectorRepository
from telecopilot.kb.sparse import SparseEmbeddingModel, SparseVector


def test_sparse_embedding_model():
    """Verify BM25 Sparse Embedding Model generates valid token indices and weights."""
    model = SparseEmbeddingModel(vocab_size=10000)
    text = "WE Space Fiber Internet Super Mega Ultra 5G"
    sparse_vec = model.embed_text(text)

    assert isinstance(sparse_vec, SparseVector)
    assert len(sparse_vec.indices) > 0
    assert len(sparse_vec.values) == len(sparse_vec.indices)
    # Okapi BM25 TF weights are positive and bounded by (k1 + 1), not by 1.0
    assert all(0.0 < v <= model.k1 + 1.0 for v in sparse_vec.values)
    # Verify indices are sorted for Qdrant compatibility
    assert sparse_vec.indices == sorted(sparse_vec.indices)


def test_dense_and_sparse_hybrid_upsert_and_search():
    """Verify QdrantVectorRepository stores and searches with both Dense and Sparse vectors."""
    repo = QdrantVectorRepository()
    model = SparseEmbeddingModel(vocab_size=10000)

    content = "Instant digital eSIM replacement is free of charge for iPhone and Samsung devices."
    sparse_vec = model.embed_text(content)

    chunk = DocumentChunk(
        chunk_id="test_hybrid_1",
        content=content,
        source="sim_policy.html",
        source_modality="LOCAL_HTML",
        policy_type="sim_replacement",
        intent_category="SIM_MANAGEMENT",
        section_title="eSIM Guide",
        page_number=1,
        dense_vector=[0.15] * 1024,
        sparse_vector=SparseVectorData(indices=sparse_vec.indices, values=sparse_vec.values),
    )

    upserted = repo.upsert_chunks([chunk])
    assert upserted == 1

    query = "How to get digital eSIM for iPhone?"
    q_sparse = model.embed_text(query)

    results = repo.hybrid_search(
        query=query,
        query_dense_vector=[0.15] * 1024,
        query_sparse_vector=SparseVectorData(indices=q_sparse.indices, values=q_sparse.values),
        top_k=3,
        intent_filter="SIM_MANAGEMENT",
    )

    assert len(results) >= 1
    assert results[0].chunk_id == "test_hybrid_1"
    assert results[0].intent_category == "SIM_MANAGEMENT"
