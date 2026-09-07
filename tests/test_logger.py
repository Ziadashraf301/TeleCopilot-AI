import pytest
import os
import json
from core.logger import get_logger


def test_structured_logger():
    """Verify structured logger writes structured console and JSON sink logs."""
    logger = get_logger()
    assert logger is not None

    test_message = "Structured Logger Test: Checking intent and model telemetry"
    logger.info(test_message)

    # Verify structured JSON log file is produced
    log_file = "logs/structured_telemetry.json.log"
    assert os.path.exists(log_file)

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) > 0
        last_log = json.loads(lines[-1])
        assert "timestamp" in last_log
        assert "level" in last_log
        assert "models" in last_log
        assert last_log["models"]["llm"] == "gemini-3.1-flash-lite-preview"
        assert last_log["models"]["dense"] == "embed-multilingual-v3.0"
        assert last_log["models"]["sparse"] == "Qdrant/bm25"
