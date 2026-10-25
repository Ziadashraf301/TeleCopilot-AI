"""
BM25 sparse vectors for hybrid search, via FastEmbed's Qdrant/bm25.

- Documents get BM25 term-frequency weights (k=1.2, b=0.75); queries get weight 1 per unique term.
- IDF is not computed here: the Qdrant sparse vector uses `modifier=IDF`, so Qdrant computes it from the live
  collection (it stays correct as documents are added).
- Tokens are hashed with murmur3, so the same text gives the same indices in every process.
- Bilingual corpus (Arabic + English): Arabic-script tokens use the Arabic Snowball stemmer, all other tokens the
  English one, and both stopword lists apply. A single language setting stems only one side (measured in the
  S01-11 report: "english" misses Arabic article variants, "arabic" misses English inflections).
"""

import re
from pathlib import Path

from fastembed import SparseTextEmbedding
from py_rust_stemmers import SnowballStemmer

from telecopilot.config.settings import get_settings
from telecopilot.kb.models import SparseVectorData

# Stopword lists from Qdrant/bm25 (Apache-2.0), vendored so no Hugging Face download is ever needed.
BM25_MODEL_DIR = Path(__file__).parent / "bm25_model"
BM25_LANGUAGES = ("english", "arabic")
ARABIC_SCRIPT = re.compile(r"[؀-ۿ]")


class ScriptAwareStemmer:
    """Arabic Snowball stemmer for Arabic-script tokens, English Snowball stemmer for everything else."""

    def __init__(self) -> None:
        self._arabic = SnowballStemmer("arabic")
        self._english = SnowballStemmer("english")

    def stem_word(self, word: str) -> str:
        stemmer = self._arabic if ARABIC_SCRIPT.search(word) else self._english
        return stemmer.stem_word(word)


def _load_stopwords() -> set[str]:
    return {
        word
        for language in BM25_LANGUAGES
        for word in (BM25_MODEL_DIR / f"{language}.txt").read_text(encoding="utf-8").split()
    }


def _to_sparse_vector(embedding) -> SparseVectorData:
    return SparseVectorData(indices=embedding.indices.tolist(), values=embedding.values.tolist())


class SparseEmbeddingModel:
    """BM25 sparse embeddings: `embed_documents` when indexing, `embed_query` when searching."""

    def __init__(self) -> None:
        self.model_name = get_settings().SPARSE_EMBEDDING_MODEL
        self._model = SparseTextEmbedding(
            self.model_name,
            specific_model_path=str(BM25_MODEL_DIR),
            stemmer=ScriptAwareStemmer(),
            stopwords=_load_stopwords(),
        )

    def embed_documents(self, texts: list[str]) -> list[SparseVectorData]:
        return [_to_sparse_vector(embedding) for embedding in self._model.embed(texts)]

    def embed_query(self, text: str) -> SparseVectorData:
        return _to_sparse_vector(next(iter(self._model.query_embed(text))))
