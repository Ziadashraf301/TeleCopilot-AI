from qdrant_client import QdrantClient
from redis import Redis

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger

logger = get_logger()
settings = get_settings()


class SingletonsManager:
    """
    Thread-safe Singleton Manager for external API & Database clients.
    Manages instances of Qdrant, Cohere, Gemini, and Langfuse.
    """

    _qdrant_client: QdrantClient | None = None
    _cohere_client: object | None = None
    _gemini_client: object | None = None
    _langfuse_client: object | None = None
    _redis_client: Redis | None = None

    @classmethod
    def get_qdrant_client(cls) -> QdrantClient:
        """Get or initialize singleton QdrantClient."""
        if cls._qdrant_client is None:
            logger.info(f"Initializing Qdrant Client ({settings.QDRANT_HOST}:{settings.QDRANT_PORT})")
            api_key = (
                settings.QDRANT_API_KEY.strip()
                if (settings.QDRANT_API_KEY and settings.QDRANT_API_KEY.strip())
                else None
            )
            cls._qdrant_client = QdrantClient(
                url=f"http://{settings.QDRANT_HOST}:{settings.QDRANT_PORT}",
                api_key=api_key,
                timeout=settings.QDRANT_TIMEOUT_S,
            )
        return cls._qdrant_client

    @classmethod
    def get_redis_client(cls) -> Redis:
        """Get or initialize singleton Redis client (sessions, pub/sub, jobs from M5 on; readiness today)."""
        if cls._redis_client is None:
            cls._redis_client = Redis.from_url(
                settings.REDIS_URL,
                socket_timeout=settings.REDIS_TIMEOUT_S,
                socket_connect_timeout=settings.REDIS_TIMEOUT_S,
            )
        return cls._redis_client

    @classmethod
    def get_cohere_client(cls):
        """Get or initialize singleton Cohere Client."""
        if cls._cohere_client is None:
            try:
                import cohere

                if settings.COHERE_API_KEY:
                    cls._cohere_client = cohere.ClientV2(api_key=settings.COHERE_API_KEY)
                    logger.info("Cohere Client initialized successfully.")
                else:
                    logger.warning("COHERE_API_KEY not set. Fallback mode will be active.")
            except Exception as e:
                logger.error(f"Failed to initialize Cohere client: {e}")
        return cls._cohere_client

    @classmethod
    def get_gemini_client(cls):
        """Get or initialize singleton Google Gemini Client."""
        if cls._gemini_client is None:
            try:
                if settings.GEMINI_API_KEY:
                    import google.generativeai as genai

                    genai.configure(api_key=settings.GEMINI_API_KEY)
                    cls._gemini_client = genai.GenerativeModel(settings.LLM_MODEL)
                    logger.info(f"Google Gemini Client initialized with model: {settings.LLM_MODEL}")
                else:
                    logger.warning("GEMINI_API_KEY not set. Fallback response generator will be active.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        return cls._gemini_client

    @classmethod
    def get_langfuse_client(cls):
        """Get or initialize singleton Langfuse Observability Client."""
        if cls._langfuse_client is None:
            try:
                host_url = settings.langfuse_host_url
                if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
                    from langfuse import Langfuse

                    cls._langfuse_client = Langfuse(
                        public_key=settings.LANGFUSE_PUBLIC_KEY,
                        secret_key=settings.LANGFUSE_SECRET_KEY,
                        host=host_url,
                    )
                    logger.info(
                        f"🟢 [LANGFUSE OPENED] Observability client connected to host: {host_url} (Public Key: {settings.LANGFUSE_PUBLIC_KEY[:10]}...)"
                    )
                else:
                    logger.info("Langfuse credentials not set. Traces will log to console.")
            except Exception as e:
                logger.warning(f"Langfuse init skipped: {e}")
        return cls._langfuse_client
