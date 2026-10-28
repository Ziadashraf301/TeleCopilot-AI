import pytest
from fastapi.testclient import TestClient

from telecopilot.api.dependencies import get_readiness_checks
from telecopilot.api.main import app

client = TestClient(app)


def reachable() -> None:
    pass


def unreachable() -> None:
    raise ConnectionError("Connection refused")


@pytest.fixture
def readiness_checks():
    """Swap the real pings for stubs; each test sets which dependencies are up."""
    checks: dict = {}
    app.dependency_overrides[get_readiness_checks] = lambda: checks
    yield checks
    app.dependency_overrides.pop(get_readiness_checks, None)


def test_ready_when_every_dependency_answers(readiness_checks):
    readiness_checks.update(qdrant=reachable, postgres=reachable, redis=reachable)

    response = client.get("/api/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert set(body["checks"]) == {"qdrant", "postgres", "redis"}
    assert all(check["ok"] and check["latency_ms"] >= 0 for check in body["checks"].values())


@pytest.mark.parametrize("down", ["qdrant", "postgres", "redis"])
def test_not_ready_when_any_dependency_is_unreachable(readiness_checks, down):
    readiness_checks.update(qdrant=reachable, postgres=reachable, redis=reachable)
    readiness_checks[down] = unreachable

    response = client.get("/api/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "not_ready"
    assert body["checks"][down] == {
        "ok": False,
        "latency_ms": body["checks"][down]["latency_ms"],
        "error": "ConnectionError: Connection refused",
    }
    assert all(body["checks"][name]["ok"] for name in body["checks"] if name != down)


def test_readiness_checks_cover_the_compose_stack(monkeypatch):
    from fakes import FakeVectorRepository

    from telecopilot.api import dependencies

    monkeypatch.setattr(dependencies, "get_vector_repository", lambda: FakeVectorRepository())
    assert set(dependencies.get_readiness_checks()) == {"qdrant", "postgres", "redis"}
