import json
import subprocess
import sys

import pytest

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import configure_logging, get_logger


@pytest.fixture
def log_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    get_settings.cache_clear()
    yield tmp_path / "logs"
    get_logger().remove()  # drop sinks pointing at tmp_path
    get_settings.cache_clear()


def test_importing_the_logger_has_no_side_effects(tmp_path):
    """No sinks, files or folders until configure_logging() is called (fresh process, empty working dir)."""
    subprocess.run([sys.executable, "-c", "import telecopilot.core.logger"], cwd=tmp_path, check=True)
    assert list(tmp_path.iterdir()) == []


def test_configure_logging_writes_structured_json(log_dir):
    configure_logging()
    get_logger().info("Structured Logger Test: Checking intent and model telemetry")

    last_log = json.loads((log_dir / "structured_telemetry.json.log").read_text(encoding="utf-8").splitlines()[-1])
    assert last_log["message"] == "Structured Logger Test: Checking intent and model telemetry"
    assert last_log["timestamp"].endswith("Z")
    assert last_log["models"] == {
        "dense": "embed-multilingual-v3.0",
        "sparse": "Qdrant/bm25",
        "rerank": "rerank-v3.5",
        "llm": "gemini-3.1-flash-lite-preview",
    }
    assert list(log_dir.glob("agent_assist_*.log"))  # rolling text log
