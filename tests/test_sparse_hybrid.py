"""Keyword search through our Qdrant collection (sparse vector with modifier=IDF) on the embedded Qdrant."""

import pytest
from qdrant_client.http import models as qmodels

from telecopilot.kb.models import DocumentChunk
from telecopilot.kb.repositories.qdrant import QdrantVectorRepository
from telecopilot.kb.sparse import SparseEmbeddingModel

CHUNKS = {
    "esim": "The customer can get an instant eSIM by scanning the QR code sent by SMS.",
    "billing": "The customer may request a courtesy late fee waiver once every twelve months.",
    "router": "If the customer router shows a red LOS light, check the fibre drop cable before a field visit.",
    "family": "يمكن للعميل ضم حتى خمسة خطوط إلى باقة WE Mix العائلية وتوزيع الجيجابايتس بينها.",
    "sla": "يحصل العميل المؤسسي على تعويض مالي عند انخفاض نسبة التشغيل عن اتفاقية مستوى الخدمة.",
}


@pytest.fixture
def indexed_repo() -> tuple[QdrantVectorRepository, SparseEmbeddingModel]:
    model = SparseEmbeddingModel()
    repo = QdrantVectorRepository()
    texts = list(CHUNKS.values())
    chunks = [
        DocumentChunk(
            chunk_id=chunk_id,
            content=text,
            source="test.html",
            source_modality="LOCAL_HTML",
            policy_type="test",
            intent_category="GENERAL",
            section_title=chunk_id,
            dense_vector=[0.1] * 1024,
            sparse_vector=sparse,
        )
        for (chunk_id, text), sparse in zip(CHUNKS.items(), model.embed_documents(texts), strict=True)
    ]
    repo.upsert_chunks(chunks)
    return repo, model


def sparse_ranking(repo: QdrantVectorRepository, model: SparseEmbeddingModel, query: str) -> list[str]:
    vector = model.embed_query(query)
    points = repo.client.query_points(
        collection_name=repo.collection_name,
        query=qmodels.SparseVector(indices=vector.indices, values=vector.values),
        using="sparse",
        limit=3,
        with_payload=True,
    ).points
    return [point.payload["chunk_id"] for point in points]


def test_collection_uses_qdrant_side_idf(indexed_repo):
    repo, _ = indexed_repo
    sparse_config = repo.client.get_collection(repo.collection_name).config.params.sparse_vectors["sparse"]
    assert sparse_config.modifier == qmodels.Modifier.IDF


@pytest.mark.parametrize(
    ("query", "expected_first"),
    [
        ("eSIM", "esim"),
        ("late fee waiver", "billing"),
        ("red LOS light on the router", "router"),
        ("WE Mix", "family"),  # plan name inside Arabic text
        ("الباقات العائلية", "family"),  # Arabic stemming: plural + article
        ("تعويض اتفاقية مستوى الخدمة", "sla"),
    ],
)
def test_keyword_query_ranks_the_right_chunk_first(indexed_repo, query, expected_first):
    repo, model = indexed_repo
    assert sparse_ranking(repo, model, query)[0] == expected_first


def test_hybrid_search_uses_the_sparse_leg(indexed_repo):
    """Dense vectors are identical here, so the sparse (BM25) leg decides the fused RRF order."""
    repo, model = indexed_repo
    results = repo.hybrid_search(
        query="eSIM QR code", query_dense_vector=[0.1] * 1024, query_sparse_vector=model.embed_query("eSIM QR code")
    )
    assert results[0].chunk_id == "esim"
