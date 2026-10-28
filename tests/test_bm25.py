"""BM25 sparse vectors (FastEmbed Qdrant/bm25, vendored stopwords: no network)."""

import json
import subprocess
import sys

import pytest

from telecopilot.kb.sparse import ScriptAwareStemmer, SparseEmbeddingModel

TEXTS = {
    "english": "Instant eSIM activation is free for iPhone and Samsung devices.",
    "arabic": "شروط ضم خطوط العائلة وتوزيع الجيجابايتس على الباقات",
    "mixed": "تفعيل eSIM للعميل على باقة WE Mix",
}
EMBED_IN_SUBPROCESS = (
    "import json, sys; from telecopilot.kb.sparse import SparseEmbeddingModel; m = SparseEmbeddingModel(); "
    "texts = json.loads(sys.argv[1]); "
    "print(json.dumps({k: [m.embed_documents([t])[0].indices, m.embed_query(t).indices] for k, t in texts.items()}))"
)


@pytest.fixture(scope="module")
def model() -> SparseEmbeddingModel:
    return SparseEmbeddingModel()


def embed_in_new_process() -> dict:
    out = subprocess.run(
        [sys.executable, "-c", EMBED_IN_SUBPROCESS, json.dumps(TEXTS)], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout.strip().splitlines()[-1])


def test_indices_are_identical_across_processes(model):
    # The old model used Python's hash(), which is randomised per process: indexing and querying never matched.
    first, second = embed_in_new_process(), embed_in_new_process()
    in_this_process = {
        k: [model.embed_documents([t])[0].indices, model.embed_query(t).indices] for k, t in TEXTS.items()
    }
    assert first == second == in_this_process


@pytest.mark.parametrize("language", TEXTS)
def test_arabic_english_and_mixed_texts_give_non_empty_vectors(model, language):
    document = model.embed_documents([TEXTS[language]])[0]
    query = model.embed_query(TEXTS[language])
    assert document.indices and len(document.indices) == len(document.values)
    assert all(value > 0 for value in document.values)
    assert set(query.values) == {1.0}  # queries carry no TF weight; Qdrant applies IDF
    assert set(query.indices) == set(document.indices)


def test_stopwords_of_both_languages_are_dropped(model):
    assert model.embed_query("the and of في من على").indices == []


def test_each_script_gets_its_own_stemmer():
    stemmer = ScriptAwareStemmer()
    assert stemmer.stem_word("activation") == stemmer.stem_word("activated")  # English stemming
    assert stemmer.stem_word("الباقات") == stemmer.stem_word("باقة")  # Arabic: article + plural removed
