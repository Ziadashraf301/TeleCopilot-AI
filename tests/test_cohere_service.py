"""CohereService fails fast: no pseudo-embeddings, no fake rerank scores."""

from types import SimpleNamespace

import pytest

from telecopilot.core.singletons import SingletonsManager
from telecopilot.llm.cohere import CohereService


class StubCohereClient:
    def __init__(self, fail: bool = False):
        self.fail = fail
        self.embed_batches: list[int] = []

    def embed(self, texts, model, input_type, embedding_types):
        if self.fail:
            raise ConnectionError("Cohere unreachable")
        self.embed_batches.append(len(texts))
        return SimpleNamespace(embeddings=SimpleNamespace(float=[[float(len(t))] for t in texts]))

    def rerank(self, model, query, documents, top_n):
        if self.fail:
            raise ConnectionError("Cohere unreachable")
        return SimpleNamespace(results=[SimpleNamespace(index=1, relevance_score=0.9)])


def service_with(monkeypatch, client) -> CohereService:
    monkeypatch.setattr(SingletonsManager, "get_cohere_client", classmethod(lambda cls: client))
    return CohereService()


def test_missing_api_key_fails_at_construction(monkeypatch):
    with pytest.raises(RuntimeError, match="COHERE_API_KEY"):
        service_with(monkeypatch, None)


def test_embedding_errors_propagate(monkeypatch):
    service = service_with(monkeypatch, StubCohereClient(fail=True))
    with pytest.raises(ConnectionError):
        service.get_embeddings_batch(["chunk one", "chunk two"])


def test_rerank_errors_propagate(monkeypatch):
    service = service_with(monkeypatch, StubCohereClient(fail=True))
    with pytest.raises(ConnectionError):
        service.rerank("lost SIM", ["doc a", "doc b"])


def test_embeddings_are_requested_in_batches_within_the_cohere_limit(monkeypatch):
    client = StubCohereClient()
    service = service_with(monkeypatch, client)

    vectors = service.get_embeddings_batch([f"text {i}" for i in range(200)])

    assert client.embed_batches == [96, 96, 8]
    assert len(vectors) == 200


def test_rerank_returns_cohere_order_and_scores(monkeypatch):
    service = service_with(monkeypatch, StubCohereClient())
    assert service.rerank("lost SIM", ["doc a", "doc b"]) == [{"index": 1, "relevance_score": 0.9}]
    assert service.rerank("lost SIM", []) == []
