import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from loguru import logger

from telecopilot.config.settings import Settings, get_settings

CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)
TEXT_FORMAT = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"
JSON_LOG_FILE = "structured_telemetry.json.log"
TEXT_LOG_FILE = "agent_assist_{time:YYYY-MM-DD}.log"


def json_formatter(record, settings: Settings) -> str:
    """
    Format log records as structured JSON for log aggregators (Datadog, ELK, CloudWatch).
    """
    log_data = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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
            "llm": settings.LLM_MODEL,
        },
        "extra": record["extra"],
    }
    if record["exception"]:
        log_data["exception"] = {
            "type": record["exception"].type.__name__ if record["exception"].type else "Exception",
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }
    return json.dumps(log_data, ensure_ascii=False) + "\n"


def configure_logging() -> None:
    """
    Install the console, JSON Lines and rolling text sinks. Called once at start-up by the API (lifespan) and the
    ingestion CLI; importing this module has no side effects. Safe to call again (replaces the sinks).
    """
    settings = get_settings()
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    json_log_path = log_dir / JSON_LOG_FILE

    def sink_json_to_file(message) -> None:
        with json_log_path.open("a", encoding="utf-8") as f:
            f.write(json_formatter(message.record, settings))

    logger.remove()
    logger.add(sys.stdout, colorize=True, format=CONSOLE_FORMAT, level=settings.LOG_LEVEL)
    logger.add(sink_json_to_file, level=settings.LOG_LEVEL)
    logger.add(
        log_dir / TEXT_LOG_FILE,
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        level=settings.LOG_LEVEL,
        format=TEXT_FORMAT,
    )


def get_logger():
    """Shared loguru logger. Until configure_logging() runs it keeps loguru's default stderr sink."""
    return logger
