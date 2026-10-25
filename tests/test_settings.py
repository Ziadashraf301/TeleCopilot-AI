from pathlib import Path

import pytest
from pydantic import ValidationError

from telecopilot.config.settings import Settings

V2_KEYS = [
    "CORS_ORIGINS",
    "DATA_RAW_DIR",
    "STATIC_DIR",
    "LOG_DIR",
    "QDRANT_TIMEOUT_S",
    "DATABASE_URL",
    "DB_TIMEOUT_S",
    "REDIS_URL",
    "REDIS_TIMEOUT_S",
    "LLM_PROVIDER",
    "EMBED_PROVIDER",
    "RERANK_PROVIDER",
    "SCRAPER_TIMEOUT_S",
]


@pytest.fixture
def clean_env(monkeypatch):
    """Settings built from defaults only: no developer .env, no inherited environment variables."""
    for key in V2_KEYS:
        monkeypatch.delenv(key, raising=False)
    return monkeypatch


def make_settings() -> Settings:
    return Settings(_env_file=None)


def test_defaults_keep_v1_behaviour(clean_env):
    settings = make_settings()
    assert (settings.LLM_PROVIDER, settings.EMBED_PROVIDER, settings.RERANK_PROVIDER) == ("gemini", "cohere", "cohere")
    assert settings.QDRANT_TIMEOUT_S == 10.0  # was hard-coded in the Qdrant client
    assert settings.SCRAPER_TIMEOUT_S == 30.0  # was the scraper's default argument
    assert settings.DATA_RAW_DIR == Path("data/raw")
    assert settings.STATIC_DIR == Path("static")
    assert settings.LOG_DIR == Path("logs")  # was hard-coded in the logger


def test_defaults_point_at_local_compose_services(clean_env):
    settings = make_settings()
    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")
    assert settings.REDIS_URL == "redis://localhost:6379/0"
    assert settings.CORS_ORIGINS == ["http://localhost:8000"]


def test_environment_overrides_defaults(clean_env):
    clean_env.setenv("DATABASE_URL", "postgresql+psycopg://u:p@postgres:5432/db")
    clean_env.setenv("REDIS_URL", "redis://redis:6379/1")
    clean_env.setenv("CORS_ORIGINS", '["http://localhost:3000", "https://desk.example.com"]')
    clean_env.setenv("DB_TIMEOUT_S", "1.5")

    settings = make_settings()

    assert settings.DATABASE_URL == "postgresql+psycopg://u:p@postgres:5432/db"
    assert settings.REDIS_URL == "redis://redis:6379/1"
    assert settings.CORS_ORIGINS == ["http://localhost:3000", "https://desk.example.com"]
    assert settings.DB_TIMEOUT_S == 1.5


@pytest.mark.parametrize("key", ["LLM_PROVIDER", "EMBED_PROVIDER", "RERANK_PROVIDER"])
def test_unknown_provider_is_rejected_at_startup(clean_env, key):
    # Fail fast: a typo or a provider that is not implemented yet must not silently fall back to another one.
    clean_env.setenv(key, "llamacpp")
    with pytest.raises(ValidationError):
        make_settings()
