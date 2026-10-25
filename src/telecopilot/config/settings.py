from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables and .env file.
    Follows Singleton access via get_settings() cache.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App Info
    APP_NAME: str = "TeleCopilot AI"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # HTTP
    CORS_ORIGINS: list[str] = ["http://localhost:8000"]  # JSON list in .env, e.g. ["http://localhost:3000"]

    # Paths, relative to the working directory (repo root locally, /app in Docker)
    DATA_RAW_DIR: Path = Path("data/raw")
    STATIC_DIR: Path = Path("static")
    LOG_DIR: Path = Path("logs")

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "telecom_customer_policies"
    QDRANT_TIMEOUT_S: float = 10.0
    VECTOR_DIMENSION: int = 1024  # embed-multilingual-v3.0

    # Postgres (CRM, tickets, audit) and Redis (sessions, pub/sub, jobs) — ADR-5.
    # 127.0.0.1, not "localhost": compose binds both to IPv4 only, and on Windows "localhost" tries IPv6 first,
    # adding ~2 s to every new connection.
    DATABASE_URL: str = "postgresql+psycopg://telecopilot:telecopilot@127.0.0.1:5432/telecopilot"
    DB_TIMEOUT_S: float = 5.0
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_TIMEOUT_S: float = 2.0

    # Model providers (ADR-2). Only today's implementations are accepted; M3 adds llamacpp | vllm | tei | local.
    LLM_PROVIDER: Literal["gemini"] = "gemini"
    EMBED_PROVIDER: Literal["cohere"] = "cohere"
    RERANK_PROVIDER: Literal["cohere"] = "cohere"

    # Specified AI Models
    DENSE_EMBEDDING_MODEL: str = "embed-multilingual-v3.0"
    RERANK_MODEL: str = "rerank-v3.5"
    SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
    LLM_MODEL: str = "gemini-3.1-flash-lite-preview"

    # API Keys
    COHERE_API_KEY: str | None = None
    GEMINI_API_KEY: str | None = None

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: str | None = None
    LANGFUSE_SECRET_KEY: str | None = None
    LANGFUSE_HOST: str | None = None
    LANGFUSE_BASE_URL: str | None = None

    @property
    def langfuse_host_url(self) -> str:
        return self.LANGFUSE_BASE_URL or self.LANGFUSE_HOST or "https://cloud.langfuse.com"

    # Web Scraper
    SCRAPER_VERIFY_SSL: bool = True
    SCRAPER_TIMEOUT_S: float = 30.0

    # RAG Tuning Parameters
    RETRIEVAL_TOP_K: int = 5
    RERANK_TOP_N: int = 3
    SIMILARITY_THRESHOLD: float = 0.35


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for configuration settings."""
    return Settings()
