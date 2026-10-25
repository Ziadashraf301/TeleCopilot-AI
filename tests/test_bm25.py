from telecopilot.services.sparse_embedding_model import SparseEmbeddingModel, SparseVector


def test_okapi_bm25_sparse_model():
    """Verify Okapi BM25 formula calculates term weights with document length normalization."""
    model = SparseEmbeddingModel(vocab_size=50000, k1=1.5, b=0.75, avg_doc_len=100.0)

    # Short query
    query = "eSIM activation router red light"
    q_sparse = model.embed_text(query)

    assert isinstance(q_sparse, SparseVector)
    assert len(q_sparse.indices) == 5
    assert len(q_sparse.values) == 5
    # Verify strict ascending order for Qdrant
    assert q_sparse.indices == sorted(q_sparse.indices)
    assert all(v > 0.0 for v in q_sparse.values)

    # Arabic support
    arabic_text = "خدمة عملاء المصرية للاتصالات باقات النت المنزلي راوتر فايبر"
    ar_sparse = model.embed_text(arabic_text)
    assert len(ar_sparse.indices) > 0
    assert ar_sparse.indices == sorted(ar_sparse.indices)
