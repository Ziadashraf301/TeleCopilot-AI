from fastapi.testclient import TestClient

from telecopilot.api.main import app
from telecopilot.config.settings import get_settings

client = TestClient(app)


def preflight(origin: str):
    return client.options(
        "/api/agent-assist/solve",
        headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
    )


def test_configured_origin_is_allowed():
    origin = get_settings().CORS_ORIGINS[0]
    response = preflight(origin)
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin


def test_other_origins_are_rejected():
    response = preflight("https://evil.example.com")
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
