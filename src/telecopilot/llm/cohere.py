from telecopilot.config.settings import get_settings
from telecopilot.core.singletons import SingletonsManager

settings = get_settings()

# Cohere's embed endpoint accepts at most 96 texts per request.
COHERE_EMBED_BATCH_LIMIT = 96


class CohereService:
    """
    Service responsible for:
    1. Generating dense embeddings via Cohere API (DENSE_EMBEDDING_MODEL = 'embed-multilingual-v3.0').
    2. Reranking retrieved candidate chunks via Cohere Rerank (RERANK_MODEL = 'rerank-v3.5').

    Fail-fast: any Cohere error propagates. There are no pseudo-embeddings or fake rerank scores, because those
    would be written into Qdrant (ingestion) or shown to a CSR (rerank) as if they were real.
    """

    def __init__(self):
        self.client = SingletonsManager.get_cohere_client()
        if not self.client:
            raise RuntimeError(
                "Cohere client could not be initialised. Ensure COHERE_API_KEY is set correctly in your .env file."
            )
        self.model = settings.DENSE_EMBEDDING_MODEL
        self.rerank_model = settings.RERANK_MODEL

    def get_embedding(self, text: str, input_type: str = "search_document") -> list[float]:
        """Generate embedding vector for a single text."""
        embeddings = self.get_embeddings_batch([text], input_type=input_type)
        return embeddings[0]

    def get_embeddings_batch(
        self,
        texts: list[str],
        input_type: str = "search_document",
        batch_size: int = COHERE_EMBED_BATCH_LIMIT,
    ) -> list[list[float]]:
        """Batch generate dense embeddings, chunking requests to stay within Cohere's per-request limit."""
        all_embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            response = self.client.embed(
                texts=texts[i : i + batch_size],
                model=self.model,
                input_type=input_type,
                embedding_types=["float"],
            )
            all_embeddings.extend(response.embeddings.float)
        return all_embeddings

    def rerank(self, query: str, documents: list[str], top_n: int = 3) -> list[dict]:
        """Rerank candidate document texts using rerank-v3.5."""
        if not documents:
            return []
        response = self.client.rerank(
            model=self.rerank_model, query=query, documents=documents, top_n=min(top_n, len(documents))
        )
        return [{"index": item.index, "relevance_score": item.relevance_score} for item in response.results]
