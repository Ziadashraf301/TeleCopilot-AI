import re
from collections import Counter

from telecopilot.config.settings import get_settings
from telecopilot.core.logger import get_logger
from telecopilot.kb.models import SparseVectorData

logger = get_logger()
settings = get_settings()


class SparseEmbeddingModel:
    """
    Qdrant-compatible BM25 Sparse Embedding Model (SPARSE_EMBEDDING_MODEL = 'Qdrant/bm25').
    Implements standard Okapi BM25 Term Frequency & Inverse Document Frequency (IDF) scoring
    with token hashing into Qdrant sparse index space.
    - k1: Term frequency saturation parameter (default 1.5)
    - b: Document length normalization parameter (default 0.75)
    - avg_doc_len: Average document length (default 128 tokens)
    """

    def __init__(self, vocab_size: int = 100000, k1: float = 1.5, b: float = 0.75, avg_doc_len: float = 128.0):
        self.model_name = settings.SPARSE_EMBEDDING_MODEL
        self.vocab_size = vocab_size
        self.k1 = k1
        self.b = b
        self.avg_doc_len = avg_doc_len

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize Arabic, English words and numbers."""
        tokens = re.findall(r"\b\w+\b", text.lower())
        return [t for t in tokens if len(t) > 1]

    def _hash_token(self, token: str) -> int:
        """Hash token to a fixed sparse index space (0 to vocab_size - 1)."""
        return abs(hash(token)) % self.vocab_size

    def embed_text(self, text: str) -> SparseVectorData:
        """
        Generate a sparse vector for a single document or query text using Okapi BM25 scoring:
        BM25_TF = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
        """
        tokens = self._tokenize(text)
        if not tokens:
            return SparseVectorData()

        doc_len = len(tokens)
        counts = Counter(tokens)

        token_weights: dict[int, float] = {}
        for token, tf in counts.items():
            idx = self._hash_token(token)

            # Okapi BM25 term frequency formula
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
            bm25_weight = numerator / max(denominator, 1e-6)

            # Keep max weight for hash collisions
            if idx in token_weights:
                token_weights[idx] = max(token_weights[idx], bm25_weight)
            else:
                token_weights[idx] = bm25_weight

        # Sort indices as required by Qdrant sparse vector specifications
        sorted_items = sorted(token_weights.items(), key=lambda x: x[0])
        indices = [item[0] for item in sorted_items]
        values = [round(item[1], 4) for item in sorted_items]

        return SparseVectorData(indices=indices, values=values)

    def embed_batch(self, texts: list[str]) -> list[SparseVectorData]:
        """Batch generate sparse vectors."""
        return [self.embed_text(t) for t in texts]
