import sys
import json
import os
from datetime import datetime
from loguru import logger
from telecopilot.config.settings import get_settings

settings = get_settings()


def json_formatter(record):
    """
    Format log records as structured JSON for log aggregators (Datadog, ELK, CloudWatch).
    """
    log_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "models": {
            "dense": settings.DENSE_EMBEDDING_MODEL,
            "sparse": settings.SPARSE_EMBEDDING_MODEL,
            "rerank": settings.RERANK_MODEL,
            "llm": settings.LLM_MODEL
        },
        "extra": record["extra"]
    }
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else "Exception",
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback
        }
    return json.dumps(log_data, ensure_ascii=False) + "\n"


def sink_json_to_file(message):
    """Custom JSON serializer sink for structured JSON log files."""
    record = message.record
    formatted_json = json_formatter(record)
    os.makedirs("logs", exist_ok=True)
    with open("logs/structured_telemetry.json.log", "a", encoding="utf-8") as f:
        f.write(formatted_json)


# Reset logger sinks
logger.remove()

# 1. Console Sink: Colorized, human-readable structured console output
logger.add(
    sys.stdout,
    colorize=True,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level=settings.LOG_LEVEL,
)

# 2. JSON Telemetry Sink: Machine-readable JSON Lines (.jsonl) log stream
logger.add(
    sink_json_to_file,
    level=settings.LOG_LEVEL,
)

# 3. Standard Rolling Text File Log
logger.add(
    "logs/agent_assist_{time:YYYY-MM-DD}.log",
    rotation="10 MB",
    retention="14 days",
    compression="zip",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
)


def get_logger():
    """Singleton getter for structured enterprise logger."""
    return logger
