from functools import lru_cache

from telecopilot.agent.assist_service import AgentAssistService
from telecopilot.kb.ingestion_service import IngestionService
from telecopilot.kb.repositories.base import BaseVectorRepository
from telecopilot.kb.repositories.qdrant import QdrantVectorRepository
from telecopilot.kb.retrieval import HybridRetriever
from telecopilot.kb.sparse import SparseEmbeddingModel
from telecopilot.llm.cohere import CohereService
from telecopilot.llm.gemini import GeminiService


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
        vector_repo=get_vector_repository(), cohere_service=get_cohere_service(), sparse_model=get_sparse_model()
    )


def get_hybrid_retriever() -> HybridRetriever:
    """Dependency for policy retrieval (embed query, hybrid search, rerank)."""
    return HybridRetriever(
        vector_repo=get_vector_repository(), cohere_service=get_cohere_service(), sparse_model=get_sparse_model()
    )


def get_agent_assist_service() -> AgentAssistService:
    """Dependency for Agent Assist RAG Service."""
    return AgentAssistService(retriever=get_hybrid_retriever(), gemini_service=get_gemini_service())
