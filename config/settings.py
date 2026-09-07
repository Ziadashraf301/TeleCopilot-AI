from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application Settings configured via environment variables and .env file.
    Follows Singleton access via get_settings() cache.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App Info
    APP_NAME: str = "Telecom Customer Service Agent Assist"
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION: str = "telecom_customer_policies"
    VECTOR_DIMENSION: int = 1024  # embed-multilingual-v3.0

    # Specified AI Models
    DENSE_EMBEDDING_MODEL: str = "embed-multilingual-v3.0"
    RERANK_MODEL: str = "rerank-v3.5"
    SPARSE_EMBEDDING_MODEL: str = "Qdrant/bm25"
    LLM_MODEL: str = "gemini-3.1-flash-lite-preview"

    # API Keys
    COHERE_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Langfuse Observability
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: Optional[str] = None
    LANGFUSE_BASE_URL: Optional[str] = None

    @property
    def langfuse_host_url(self) -> str:
        return self.LANGFUSE_BASE_URL or self.LANGFUSE_HOST or "https://cloud.langfuse.com"

    # RAG Tuning Parameters
    RETRIEVAL_TOP_K: int = 5
    RERANK_TOP_N: int = 3
    SIMILARITY_THRESHOLD: float = 0.35


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Singleton getter for configuration settings."""
    return Settings()
