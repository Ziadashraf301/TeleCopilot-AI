"""v1 contract: endpoints, JSON shapes and pipeline outputs must not change during the S01 refactor.

Golden files live in tests/golden/. A change to them is a deliberate API change and must be explained in the
ticket report.
"""

import json
from pathlib import Path

import httpx
import pytest
from fakes import FakeCohereService, FakeVectorRepository
from fastapi.testclient import TestClient

from telecopilot.api.main import app
from telecopilot.kb.factories import ChunkerFactory
from telecopilot.kb.ingestion_service import IngestionService
from telecopilot.kb.sparse import SparseEmbeddingModel

GOLDEN_DIR = Path(__file__).parent / "golden"
RAW_DIR = Path(__file__).parents[1] / "data" / "raw"
QUERY = {"customer_query": "I lost my phone today and need a replacement SIM card.", "policy_filter": "sim_replacement"}
# Timing fields differ on every run; everything else must match exactly.
VOLATILE_KEYS = {"execution_time_seconds", "latency_breakdown"}
SCRAPED_PAGE = """<html><head><title>WE Internet</title></head><body>
<h1>Home Internet</h1><p>Super Speed 140 Mbps plan costs 650 EGP per month with 400 GB quota.</p>
<h2>Router</h2><p>Free VDSL router delivery within 3 working days for new lines.</p></body></html>"""

client = TestClient(app)


def load_golden(name: str):
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def strip_volatile(payload: dict) -> dict:
    return {k: v for k, v in payload.items() if k not in VOLATILE_KEYS}


def parse_sse(text: str) -> list[dict]:
    events = []
    for block in text.strip().split("\n\n"):
        event_line, data_line = block.split("\n")
        events.append(
            {"event": event_line.removeprefix("event: "), "data": json.loads(data_line.removeprefix("data: "))}
        )
    return events


def chunk_summary(repo: FakeVectorRepository) -> list[dict]:
    # Sparse indices come from Python's per-process hash(), so only their presence is compared.
    return [
        {
            **chunk.model_dump(exclude={"dense_vector", "sparse_vector"}),
            "source": Path(chunk.source).name if not chunk.source.startswith("http") else chunk.source,
            "dense_dim": len(chunk.dense_vector),
            "has_sparse": bool(chunk.sparse_vector and chunk.sparse_vector.indices),
        }
        for chunk in repo.upserted
    ]


def openapi_contract() -> dict:
    spec = app.openapi()
    return {"paths": spec["paths"], "components": spec["components"]}


def solve_contract() -> dict:
    return strip_volatile(client.post("/api/agent-assist/solve", json=QUERY).json())


def stream_contract() -> list[dict]:
    events = parse_sse(client.post("/api/agent-assist/solve/stream", json=QUERY).text)
    for event in events:
        if event["event"] == "done":
            event["data"] = strip_volatile(event["data"])
    return events


def ingest_file_contract() -> dict:
    repo = FakeVectorRepository()
    result = IngestionService(repo, FakeCohereService(), SparseEmbeddingModel()).ingest_file(
        str(RAW_DIR / "sim_replacement_policy.html")
    )
    result["source"] = Path(result["source"]).name  # absolute path differs per machine
    return {"result": result, "chunks": chunk_summary(repo)}


def ingest_url_contract(monkeypatch) -> dict:
    def fake_get(self, url):
        return httpx.Response(200, text=SCRAPED_PAGE, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.Client, "get", fake_get)
    repo = FakeVectorRepository()
    result = IngestionService(repo, FakeCohereService(), SparseEmbeddingModel()).ingest_url(
        "https://www.te.eg/test-page"
    )
    return {"result": result, "chunks": chunk_summary(repo)}


def test_openapi_contract_unchanged():
    assert openapi_contract() == load_golden("openapi.json")


@pytest.mark.usefixtures("mocked_agent_assist")
def test_solve_response_unchanged():
    assert solve_contract() == load_golden("solve.json")


@pytest.mark.usefixtures("mocked_agent_assist")
def test_stream_events_unchanged():
    assert stream_contract() == load_golden("solve_stream.json")


def test_ingest_file_output_unchanged():
    assert ingest_file_contract() == load_golden("ingest_file.json")


def test_ingest_url_output_unchanged(monkeypatch):
    assert ingest_url_contract(monkeypatch) == load_golden("ingest_url.json")


def test_ingest_empty_document_result_unchanged(monkeypatch):
    class NoChunks:
        def chunk(self, document):
            return []

    monkeypatch.setattr(ChunkerFactory, "get_chunker", staticmethod(lambda policy_type: NoChunks()))
    monkeypatch.setattr(
        httpx.Client, "get", lambda self, url: httpx.Response(200, text=SCRAPED_PAGE, request=httpx.Request("GET", url))
    )
    repo = FakeVectorRepository()
    service = IngestionService(repo, FakeCohereService(), SparseEmbeddingModel())
    html_file = str(RAW_DIR / "sim_replacement_policy.html")

    assert service.ingest_file(html_file) == {"file_path": html_file, "chunks_count": 0, "status": "EMPTY"}
    assert service.ingest_url("https://www.te.eg/x") == {
        "file_path": "https://www.te.eg/x",
        "chunks_count": 0,
        "status": "EMPTY",
    }
    assert repo.upserted == []
