from typing import List
import hashlib
from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.core.singletons import SingletonsManager

logger = get_logger()
settings = get_settings()


class CohereService:
    """
    Service responsible for:
    1. Generating dense embeddings via Cohere API (DENSE_EMBEDDING_MODEL = 'embed-multilingual-v3.0').
    2. Reranking retrieved candidate chunks via Cohere Rerank (RERANK_MODEL = 'rerank-v3.5').
    """

    def __init__(self):
        self.client = SingletonsManager.get_cohere_client()
        self.model = settings.DENSE_EMBEDDING_MODEL
        self.rerank_model = settings.RERANK_MODEL

    def get_embedding(self, text: str, input_type: str = "search_document") -> List[float]:
        """Generate embedding vector for a single text."""
        embeddings = self.get_embeddings_batch([text], input_type=input_type)
        return embeddings[0]

    def get_embeddings_batch(
        self,
        texts: List[str],
        input_type: str = "search_document",
        batch_size: int = 96,
    ) -> List[List[float]]:
        """Batch generate dense embeddings using embed-multilingual-v3.0,
        automatically chunking requests to stay within Cohere's 96-text limit.
        """
        if not texts:
            return []

        if self.client:
            try:
                all_embeddings: List[List[float]] = []

                for i in range(0, len(texts), batch_size):
                    batch = texts[i : i + batch_size]
                    response = self.client.embed(
                        texts=batch,
                        model=self.model,
                        input_type=input_type,
                        embedding_types=["float"],
                    )
                    all_embeddings.extend(response.embeddings.float)

                return all_embeddings
            except Exception as e:
                logger.error(
                    f"Cohere embedding failed: {e}. Falling back to deterministic pseudo-embeddings."
                )

        # Fallback deterministic embedding
        return [self._generate_fallback_embedding(t) for t in texts]
        
    def rerank(self, query: str, documents: List[str], top_n: int = 3) -> List[dict]:
        """Rerank candidate document texts using rerank-v3.5."""
        if not documents:
            return []

        if self.client:
            try:
                response = self.client.rerank(
                    model=self.rerank_model,
                    query=query,
                    documents=documents,
                    top_n=min(top_n, len(documents))
                )
                results = []
                for item in response.results:
                    results.append({
                        "index": item.index,
                        "relevance_score": item.relevance_score
                    })
                return results
            except Exception as e:
                logger.error(f"Cohere rerank failed: {e}. Defaulting to original score ranking.")

        # Fallback ranking
        return [{"index": i, "relevance_score": 1.0 - (i * 0.1)} for i in range(min(top_n, len(documents)))]

    def _generate_fallback_embedding(self, text: str) -> List[float]:
        """Creates normalized deterministic 1024-dim vector from text hash."""
        dim = settings.VECTOR_DIMENSION
        hash_digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = []
        for i in range(dim):
            byte_val = hash_digest[i % len(hash_digest)]
            val = (byte_val / 255.0) - 0.5
            vector.append(float(val))
        norm = sum(x ** 2 for x in vector) ** 0.5
        return [x / (norm or 1.0) for x in vector]
