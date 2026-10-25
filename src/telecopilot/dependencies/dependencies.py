from functools import lru_cache
from telecopilot.repositories.base import BaseVectorRepository
from telecopilot.repositories.qdrant_repository import QdrantVectorRepository
from telecopilot.services.cohere_service import CohereService
from telecopilot.services.gemini_service import GeminiService
from telecopilot.services.sparse_embedding_model import SparseEmbeddingModel
from telecopilot.services.ingestion_service import IngestionService
from telecopilot.services.agent_assist_service import AgentAssistService


@lru_cache(maxsize=1)
def get_vector_repository() -> BaseVectorRepository:
    """Singleton dependency for Vector Repository."""
    return QdrantVectorRepository()


@lru_cache(maxsize=1)
def get_cohere_service() -> CohereService:
    """Singleton dependency for Cohere Embedding & Rerank Service."""
    return CohereService()


@lru_cache(maxsize=1)
def get_gemini_service() -> GeminiService:
    """Singleton dependency for Gemini Generation & Vision OCR Service."""
    return GeminiService()


@lru_cache(maxsize=1)
def get_sparse_model() -> SparseEmbeddingModel:
    """Singleton dependency for Sparse BM25 Embedding Model."""
    return SparseEmbeddingModel()


def get_ingestion_service() -> IngestionService:
    """Dependency for Ingestion Service."""
    return IngestionService(
        vector_repo=get_vector_repository(),
        cohere_service=get_cohere_service()
    )


def get_agent_assist_service() -> AgentAssistService:
    """Dependency for Agent Assist RAG Service."""
    return AgentAssistService(
        vector_repo=get_vector_repository(),
        cohere_service=get_cohere_service(),
        gemini_service=get_gemini_service()
    )
