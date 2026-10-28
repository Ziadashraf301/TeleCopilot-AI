import pytest
from fastapi.testclient import TestClient

from telecopilot.api import main as api_main
from telecopilot.kb import ingest
from telecopilot.kb.ingestion_service import IngestionService


class StubIngestionService:
    def __init__(self, results: list[dict]):
        self.results = results
        self.calls = 0

    def ingest_all_default_policies(self) -> list[dict]:
        self.calls += 1
        return self.results


SUCCESS = {"source": "sim_replacement_policy.html", "status": "SUCCESS", "chunks_count": 12}
FAILED = {"source_url": "https://www.te.eg/", "status": "FAILED", "error": "timeout"}


def test_run_all_exits_0_when_every_source_succeeds():
    assert ingest.run_all(StubIngestionService([SUCCESS, {**SUCCESS, "status": "EMPTY"}])) == 0


def test_run_all_exits_1_when_any_source_fails():
    # Fail fast: a partial index must not look like a successful run to a script or CI job.
    assert ingest.run_all(StubIngestionService([SUCCESS, FAILED])) == 1


def test_main_requires_the_all_flag():
    with pytest.raises(SystemExit) as exit_info:
        ingest.main([])
    assert exit_info.value.code == 2


def test_main_configures_logging_and_runs_ingestion(monkeypatch):
    service = StubIngestionService([SUCCESS])
    configured = []
    monkeypatch.setattr(ingest, "configure_logging", lambda: configured.append(True))
    monkeypatch.setattr(ingest, "build_ingestion_service", lambda: service)

    assert ingest.main(["--all"]) == 0
    assert configured == [True]
    assert service.calls == 1


def test_api_startup_does_not_ingest(monkeypatch):
    def fail_if_called(self, *args, **kwargs):
        raise AssertionError("API start-up must not run ingestion")

    monkeypatch.setattr(IngestionService, "ingest_all_default_policies", fail_if_called)
    monkeypatch.setattr(api_main, "configure_logging", lambda: None)
    with TestClient(api_main.app) as client:  # the context manager runs the lifespan
        assert client.get("/").status_code == 200
