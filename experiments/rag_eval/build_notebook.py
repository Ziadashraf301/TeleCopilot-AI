"""Generates experiments/03_rag_evaluation_ragas.ipynb (run: python experiments/rag_eval/build_notebook.py)."""

from pathlib import Path

import nbformat as nbf

md = nbf.v4.new_markdown_cell
code = nbf.v4.new_code_cell
cells = [
    md("""# 🧪 Notebook 3 — RAG Evaluation with RAGAS
## TeleCopilot-AI end-to-end answer quality

This notebook runs the **production pipeline** (Cohere + BM25 query embedding → Qdrant hybrid search with RRF →
Cohere Rerank v3.5 → Gemini JSON answer) on a fixed set of CSR questions, then scores it with **RAGAS**.

- **Test set:** `experiments/rag_eval/eval_questions.json` — 13 questions (10 English, 3 Arabic) across 8 intents.
  Every reference answer is taken word-for-word from the human-verified ground truth in `data/ground_truth/`.
- **Vector DB:** an embedded Qdrant instance (`QdrantClient(":memory:")`), so the real hybrid RRF search is used
  without a Qdrant server.
- **Judge:** Gemini (via Google's OpenAI-compatible endpoint) with Cohere `embed-multilingual-v3.0` embeddings.

| Metric | What it checks |
|---|---|
| Faithfulness | Is every claim in the answer supported by the retrieved context? (hallucination check) |
| Answer relevancy | Does the answer address the question? |
| Context precision | Are the relevant chunks ranked at the top? |
| Context recall | Does the retrieved context contain everything needed for the reference answer? |
| Factual correctness | Does the answer agree with the reference answer? |
"""),
    md("## ⚙️ Section 1 — Setup"),
    code("""import os, sys, json, time
from pathlib import Path

ROOT = Path.cwd().parent if Path.cwd().name == "experiments" else Path.cwd()
os.chdir(ROOT)
for p in [str(ROOT / "src"), str(ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
for k in ["COHERE_API_KEY", "GEMINI_API_KEY"]:
    print(f"{k} set: {bool(os.getenv(k))}")   # never print the key itself

REPORTS = ROOT / "experiments" / "reports"
REPORTS.mkdir(parents=True, exist_ok=True)
EVAL_SET = json.loads((ROOT / "experiments" / "rag_eval" / "eval_questions.json").read_text(encoding="utf-8"))
print(f"Loaded {len(EVAL_SET)} evaluation questions")"""),
    md("## 🗄️ Section 2 — Build the index (embedded Qdrant, real hybrid search)"),
    code("""from qdrant_client import QdrantClient
from core.singletons import SingletonsManager
from config.settings import get_settings
from repositories.qdrant_repository import QdrantVectorRepository
from services.cohere_service import CohereService
from services.gemini_service import GeminiService
from services.ingestion_service import IngestionService
from services.agent_assist_service import AgentAssistService

settings = get_settings()
SingletonsManager._qdrant_client = QdrantClient(":memory:")   # embedded Qdrant, no server needed

repo = QdrantVectorRepository()
assert repo._is_live, "Qdrant should be live (embedded mode)"
cohere_svc, gemini_svc = CohereService(), GeminiService()

t0 = time.time()
ingest_results = IngestionService(repo, cohere_svc).ingest_all_default_policies()
print(f"Indexed {len(ingest_results)} sources, {repo.count()} chunks in {time.time() - t0:.0f}s")

service = AgentAssistService(vector_repo=repo, cohere_service=cohere_svc, gemini_service=gemini_svc)
print("Models:", settings.DENSE_EMBEDDING_MODEL, "|", settings.RERANK_MODEL, "|", settings.LLM_MODEL)"""),
    md("## 🤖 Section 3 — Run the pipeline on every question"),
    code("""def run_pipeline(question: str) -> dict:
    \"\"\"Same steps as AgentAssistService.solve_customer_problem, but keeps the full retrieved contexts.\"\"\"
    t = time.time()
    dense, sparse = service._embed_query(question)
    candidates = service._hybrid_search(question, dense, sparse, None, None)
    contexts = service._rerank(question, candidates)
    solution = gemini_svc.generate_agent_solution(question, contexts)
    answer = solution.get("suggested_customer_reply", "")
    steps = solution.get("actionable_agent_steps") or []
    if steps:
        answer += "\\n\\nAgent steps:\\n" + "\\n".join(f"- {s}" for s in steps)
    return {
        "response": answer.strip(),
        "retrieved_contexts": [c["content"] for c in contexts],
        "retrieved_sources": [os.path.basename(str(c["source"]).replace("\\\\", "/")) for c in contexts],
        "top_intent": contexts[0]["intent_category"] if contexts else None,
        "latency_s": round(time.time() - t, 2),
    }

rows = []
for item in EVAL_SET:
    out = run_pipeline(item["question"])
    rows.append({**item, **out})
    hit = item["source"] in out["retrieved_sources"]
    print(f"{item['id']} | {out['latency_s']:>5}s | source retrieved: {'✅' if hit else '❌'} | {item['question'][:60]}")
    time.sleep(1)   # stay under free-tier rate limits"""),
    md(
        "### Retrieval hit rate (no LLM judge needed)\nDid the reranked top 3 include the document the reference answer comes from?"
    ),
    code("""import pandas as pd
df = pd.DataFrame(rows)
df["source_hit"] = [r["source"] in r["retrieved_sources"] for r in rows]
df["intent_match"] = df["top_intent"] == df["intent"]
print(f"Source hit rate @3 : {df['source_hit'].mean():.0%}")
print(f"Intent accuracy    : {df['intent_match'].mean():.0%}")
print(f"Median latency     : {df['latency_s'].median():.1f}s")
df[["id", "language", "intent", "top_intent", "source_hit", "latency_s"]]"""),
    md("## 📏 Section 4 — RAGAS scoring"),
    code("""from ragas import evaluate, EvaluationDataset, RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.metrics import (Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference,
                           LLMContextRecall, FactualCorrectness)
from langchain_openai import ChatOpenAI
from langchain_cohere import CohereEmbeddings

judge_llm = LangchainLLMWrapper(ChatOpenAI(
    model=settings.LLM_MODEL,
    api_key=os.environ["GEMINI_API_KEY"],
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    temperature=0,
))
judge_emb = LangchainEmbeddingsWrapper(CohereEmbeddings(model="embed-multilingual-v3.0"))

dataset = EvaluationDataset.from_list([
    {"user_input": r["question"], "response": r["response"],
     "retrieved_contexts": r["retrieved_contexts"], "reference": r["reference"]}
    for r in rows
])
# strictness=1: Gemini's OpenAI-compatible endpoint does not support multiple candidates (n>1)
metrics = [Faithfulness(), ResponseRelevancy(strictness=1), LLMContextPrecisionWithReference(),
           LLMContextRecall(), FactualCorrectness(mode="recall")]

result = evaluate(dataset, metrics=metrics, llm=judge_llm, embeddings=judge_emb,
                  run_config=RunConfig(max_workers=2, timeout=240, max_retries=6), show_progress=True)
scores = result.to_pandas()
scores.insert(0, "id", df["id"])
scores.insert(1, "language", df["language"])
scores.insert(2, "intent", df["intent"])
scores"""),
    md("## 📈 Section 5 — Summary report"),
    code("""metric_cols = [c for c in scores.columns if c not in
               ("id", "language", "intent", "user_input", "response", "retrieved_contexts", "reference")]
summary = {
    "questions": len(scores),
    "source_hit_rate_at_3": round(float(df["source_hit"].mean()), 3),
    "intent_accuracy": round(float(df["intent_match"].mean()), 3),
    "median_latency_s": round(float(df["latency_s"].median()), 2),
    **{m: round(float(scores[m].mean()), 3) for m in metric_cols},
    "judge_model": settings.LLM_MODEL,
    "pipeline": f"{settings.DENSE_EMBEDDING_MODEL} + BM25 -> Qdrant RRF top{settings.RETRIEVAL_TOP_K} -> "
                f"{settings.RERANK_MODEL} top{settings.RERANK_TOP_N} -> {settings.LLM_MODEL}",
}
print(json.dumps(summary, indent=2, ensure_ascii=False))

by_lang = scores.groupby("language")[metric_cols].mean().round(3)
display(by_lang)

scores.drop(columns=["retrieved_contexts"]).to_csv(REPORTS / "ragas_results.csv", index=False, encoding="utf-8-sig")
(REPORTS / "ragas_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
print("Saved experiments/reports/ragas_results.csv and ragas_summary.json")"""),
    code("""import matplotlib.pyplot as plt
means = scores[metric_cols].mean().sort_values()
fig, ax = plt.subplots(figsize=(8, 3.6))
ax.barh(means.index, means.values, color="#D90429")
for i, v in enumerate(means.values):
    ax.text(v + 0.01, i, f"{v:.2f}", va="center")
ax.set_xlim(0, 1.1)
ax.set_title(f"TeleCopilot AI — RAGAS scores ({len(scores)} questions, EN + AR)")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.savefig(REPORTS / "ragas_scores.png", dpi=150)
plt.show()"""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3"}})
out = Path(__file__).resolve().parents[1] / "03_rag_evaluation_ragas.ipynb"
nbf.write(nb, out)
print("wrote", out)
