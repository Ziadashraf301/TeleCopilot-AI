# TeleCopilot AI

Agent-assist copilot for telecom customer service reps (CSRs), Arabic + English. Portfolio project, built to run in
production at small scale (one contact centre team, ~20–100 CSRs). The full roadmap is in [docs/PLAN.md](docs/PLAN.md).

## Current state (v1)
- FastAPI app; layered **controller → service → repository**, factories for extractors/chunkers, singletons for clients,
  FastAPI DI in `src/telecopilot/api/dependencies.py`.
- Ingestion: HTML, XML, DOCX, PDFs (Gemini Vision OCR), te.eg scraping → format-aware chunkers with 12 intent tags.
- Retrieval: Cohere `embed-multilingual-v3.0` dense + Qdrant BM25 sparse, RRF fusion, Cohere `rerank-v3.5` top 3.
- Generation: Gemini (JSON resolution or SSE stream). Tracing: Langfuse.
- UI: static HTML/JS in `static/` (a single form where the CSR types the problem — being replaced, see plan).
- Eval: `evals/` (notebooks in `evals/notebooks/`, code in `evals/extraction/` and `evals/rag/`, reports in `evals/reports/<service>/<stage>/`): extraction quality vs ground truth, RAGAS. Faithfulness 0.61 is the weak point.

## Scope
Learning + portfolio project for **one telecom contact centre** (single company).

## Direction (v2) — decisions so far
- **Local first**: every service must work on the laptop GPU before any cloud GPU. Each service ships with quality,
  performance and business-KPI reports plus a Locust load test (max concurrent CSRs at p95 < 4 s). Then free cloud
  GPUs (Kaggle/Colab/credits), then at most **$10** paid.
- Build **one milestone at a time** in the order in docs/SPRINTS.md; a service is done only when its reports exist.
- The UI becomes a real **agent desktop** built with **Reflex**: inbox across channels, conversation, customer 360,
  tickets, copilot side panel.
- Channels: WhatsApp **simulator** in Meta Cloud API format first (real API later via free test number), web chat,
  tickets, voice notes/recordings, and **live calls** over WebRTC (LiveKit, no paid phone numbers).
- **Open-source models** (learning goal), five roles: LLM, embedding, reranker, ASR, vision/OCR, from the Hugging
  Face Hub, chosen in M3 on Egyptian dialect / code-switching / Franco evals (`docs/design/MODEL_SELECTION.md`).
  llama.cpp locally, vLLM in the cloud. API providers stay behind the same interfaces as a fallback.
- UI style: `docs/design/ui-reference/STYLE_GUIDE.md`.
- Every model call goes through a provider interface selected in config (`LLM_PROVIDER=llamacpp|vllm|gemini`).

## Sprints
Work is planned in [docs/SPRINTS.md](docs/SPRINTS.md) (milestones, tickets, acceptance criteria, ADRs, working
agreement). Work only on the current sprint's tickets, tick them off there, and stop at the sprint review.

## Code quality (non-negotiable)
- Clean, modular, readable code. Follow SOLID: one responsibility per class/module, depend on interfaces
  (providers, repositories), extend by adding classes (factories/strategies) rather than editing callers.
- DRY: no duplicated logic. Extract shared helpers; reuse existing utilities before writing new ones.
- Keep the existing patterns: layered controller → service → repository, factories, singletons for clients, FastAPI DI.
- Type hints everywhere; small functions; clear names; comments explain *why*, not *what*.
- **No over-engineering** (KISS, YAGNI): simplest solution that meets the ticket; no abstractions with a single
  implementation, pass-through layers, speculative options or premature optimisation.
- **No anti-patterns**: god classes, copy-paste, magic numbers, hard-coded config/secrets, swallowed exceptions,
  wrong-way imports, global mutable state, business logic in routes/UI, leaky abstractions, dead code.
  Explained in [docs/design/CODE_GUIDELINES.md](docs/design/CODE_GUIDELINES.md).
- `ruff check` and `ruff format` must pass (configured in `pyproject.toml`); CI enforces it.
- Every ticket ends with a short report: what changed, which files, and the reasoning behind each decision.

## Commands
```bash
docker compose up --build                                  # Qdrant + app on :8000
pip install -e ".[dev]"                                    # once; installs the telecopilot package
uvicorn telecopilot.api.main:app --host 0.0.0.0 --port 8000 --reload
pytest -v                                                  # CI runs this + docker build
```
Code is one installable package under `src/telecopilot/`; always import absolutely (`from telecopilot.config.settings import ...`). No `sys.path` edits.

## Conventions
- Fail fast: no silent fallbacks in the pipeline; errors propagate (see `AgentAssistService`).
- New external clients → singleton in `telecopilot/core/singletons.py`, exposed via `telecopilot/api/dependencies.py`.
- Imports point downwards only (`api → agent → kb → llm → core → config`); `tests/test_layers.py` enforces it.
- Settings only via `telecopilot/config/settings.py` (pydantic-settings, `.env`). Never commit `.env` or secret files.
- Tests stub external clients (Gemini/Cohere); CI has no API keys and no GPU.
- Citations show file names only, never local absolute paths.
- Arabic text: normalise before comparing/evaluating (alef/yaa/taa marbuta, diacritics).

## Environment constraints
- Windows 11, Python 3.12, Docker Desktop. Local GPU: **RTX 2050, 4 GB VRAM** — only small quantised models locally
  (≤3B LLM in GGUF Q4, whisper small/turbo int8, embeddings on CPU or GPU). Larger models run on a rented cloud GPU.
- **Limited internet quota**: follow the `data-saver` skill. Ask before any download over ~200 MB (model weights,
  CUDA/PyTorch images, datasets). Prefer downloading large weights on the rented GPU box, not locally.
