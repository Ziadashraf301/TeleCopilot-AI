# TeleCopilot AI v2 — Milestones & Sprints

Owner: Ziad (product owner). Tech lead: Claude (this plan). Implementer: a Claude Code agent working ticket by ticket.
Source of truth for *what* and *why*: [PLAN.md](PLAN.md). Architecture decisions explained:
[design/ARCHITECTURE_DECISIONS.md](design/ARCHITECTURE_DECISIONS.md). This file is the *how* and *when*.

## Order of work (agreed 2026-10-25)
1. **Restructure** the code and folders (no behaviour change).
2. **Front end first**: the agent desktop and the CRM data it shows, in Ziad's visual style.
3. **Data first**: knowledge base and data pipelines with measured data quality, *before* choosing models.
4. Then models, retrieval and generation baselines, channels, agent, speech, hardening, and the cloud stages.

## Working agreement
- **Sprint = 2 weeks** at ~20–25 h/week (~40 h of tickets). Estimates are ideal hours (h).
- **Design before code**: every milestone starts with a **design pack** ticket. The agent writes
  `docs/design/M<n>-<name>.md` with Mermaid diagrams (architecture, data flow / sequence, ERD when there is data),
  the decisions for that milestone (options considered, choice, why, trade-offs) in plain language, and open
  questions. **Ziad approves the design pack before any code for that milestone is written.**
- **One branch per sprint**: `sprint/<nn>-<slug>` from `master`. Small commits per ticket (`S01-03: ...`).
  Merge to `master` only after Ziad accepts the sprint review. Never push or open PRs without Ziad's OK.
- **Definition of Done (ticket)**: code + tests (no network, GPU or API keys in tests) · `pytest` green ·
  `ruff check` + `ruff format --check` clean · follows CLAUDE.md + `docs/design/CODE_GUIDELINES.md` (SOLID, DRY,
  KISS/YAGNI, no anti-patterns, existing patterns, type hints) · docs updated · no secrets or local absolute paths committed · ticket ticked here ·
  **ticket report** posted (what changed, which files, why each decision was taken).
- **Definition of Done (service milestone)**: reports in `evals/reports/<service>/<stage>/` — `quality.md`,
  `performance.md`, `kpi.md` — produced by scripts, with raw JSON/CSV next to them.
- **Downloads**: follow the `data-saver` skill; any single download > 200 MB needs Ziad's explicit OK first.
- **Sprint review**: agent writes `docs/sprints/S<nn>-review.md` (done / not done with evidence, decisions, downloads +
  sizes, risks, proposals), then stops and waits for Ziad.

## Architecture decisions (summary — full explanations in design/ARCHITECTURE_DECISIONS.md)
| # | Decision |
|---|---|
| ADR-1 | One installable package `telecopilot` under `src/telecopilot/`; Reflex app in `apps/web/`; `evals/`; `deploy/` |
| ADR-2 | Providers behind interfaces: `LLM_PROVIDER=llamacpp\|vllm\|gemini`, `EMBED_PROVIDER=tei\|local\|cohere`, `RERANK_PROVIDER=tei\|local\|cohere`, `STT_PROVIDER=faster_whisper` |
| ADR-3 | Five model roles (LLM, embedding, reranker, ASR, vision/OCR) from the Hugging Face Hub, chosen in S08-00 on our Egyptian dialect/Franco evals; local LLM on llama.cpp, embed/rerank on CPU. Starting candidates in `docs/design/MODEL_SELECTION.md`. No Ollama |
| ADR-4 | Sparse retrieval stays Qdrant/bm25 unless an experiment shows BGE-M3 sparse is clearly better and servable |
| ADR-5 | Postgres (SQLAlchemy 2 + Alembic) for CRM, tickets, conversations, KB registry, audit; Redis for sessions, pub/sub, jobs |
| ADR-6 | Single company (one telecom contact centre) |
| ADR-7 | UI = Reflex (responsive web, **fully bilingual Arabic + English**, RTL for Arabic). Visual reference: Figma community "Chat UI" (file 1057195320253196766) — calm, clean, easy to use; **no emojis, no robot/chatbot imagery** |
| ADR-8 | Agent = LangGraph; tools = typed Python functions, later exposed as MCP servers |
| ADR-9 | Load testing = Locust; capacity = max concurrent CSRs at p95 copilot latency < 4 s and error rate < 1% |
| ADR-10 | Data before models: KB pipeline quality (extraction, cleaning, metadata, freshness) is measured before model selection |

## Milestones
| ID | Milestone | Sprints | Exit criteria |
|---|---|---|---|
| **M0** | Restructure & foundation | S01 | New package layout, config, Postgres/Redis/Alembic, ingestion as a job, CI; v1 behaviour unchanged |
| **M1** | Agent desktop + CRM data | S02–S04 | Ziad-approved UI design; CSR logs in and works a ticket end to end on synthetic CRM data; copilot panel shows the v1 answer |
| **M2** | Knowledge base & data pipelines | S05–S07 | Real public AR/EN sources, all formats, cleaning + data-quality checks, versioning/freshness, gold eval sets; data-quality reports |
| **M3** | Model providers + retrieval baseline | S08–S09 | Provider interfaces, local models running, retrieval reports AR/EN, local vs Cohere |
| **M4** | Generation baseline | S10–S11 | Faithfulness, JSON validity, streaming, capacity reports |
| **M5** | Channels | S12–S13 | Tickets/email, WhatsApp simulator, web chat in one inbox; copilot per message; channel reports |
| **M6** | Agent copilot | S14–S16 | Tools, memory, guardrails, wrap-up; tool accuracy; AHT simulation vs baseline |
| **M7** | Speech | S17–S19 | Voice notes, recordings, live calls; Egyptian WER |
| **M8** | MCP + hardening | S20–S21 | MCP servers, CI eval gate, PII masking, audit, metrics; checklist ≥ 90% |
| **M9** | Stage A baseline report | S22 | All reports + laptop max capacity published |
| **M10** | Stage B / C | S23–S24 | Free cloud GPUs, then ≤ $10 paid; side-by-side table |

Rough calendar: ~48 weeks part-time. Re-plan at every milestone review.

---

## M0 — Restructure & foundation (S01)
| ID | Ticket | Est | Acceptance criteria |
|---|---|---|---|
| S01-00 | **Design pack M0**: current vs target folder/package diagram, dependency direction between layers, migration steps, risks | 3 | `docs/design/M0-foundation.md` approved by Ziad |
| S01-01 | Add `pyproject.toml` (Python ≥ 3.11), move `src/*` → `src/telecopilot/*`, rewrite imports to `telecopilot.*`, drop `sys.path` hacks | 6 | `pip install -e .` works; `uvicorn telecopilot.api.main:app` serves; all tests green; Dockerfile + CI updated |
| S01-02 | Group modules: `kb/` (ingestion, chunkers, repositories, retrieval), `llm/` (current Cohere/Gemini services, unchanged), `core/`, `config/`, `api/` | 4 | Same endpoints and JSON shapes; tests green |
| S01-03 | Move `experiments/` → `evals/` (notebooks under `evals/notebooks/`, reusable code under `evals/<area>/`) | 2 | Notebooks still open; paths fixed |
| S01-04 | Settings v2: Postgres/Redis URLs, timeouts, CORS origins; placeholders for provider selection (values keep today's Cohere/Gemini) | 3 | Settings unit tests; `.env.example` updated |
| S01-05 | `deploy/compose/`: Qdrant, Postgres 16-alpine, Redis 7-alpine, app; root `docker-compose.yml` delegates | 4 | `docker compose up` works as today; image sizes listed in review |
| S01-06 | SQLAlchemy 2 + Alembic skeleton, DB session dependency, first migration (`audit_log`) | 4 | `alembic upgrade head` on compose Postgres; tests with SQLite/fake session |
| S01-07 | Startup ingestion → CLI job `python -m telecopilot.kb.ingest --all`; `/api/ready` reports dependency status | 3 | API starts fast with empty Qdrant |
| S01-08 | CORS from settings, requirements split (runtime / dev / eval extras), pinned versions, ruff in CI | 3 | CI green; image not larger than before |
| S01-10 | Remove silent fallbacks: `CohereService` raises instead of pseudo-embeddings / fake rerank scores; `QdrantVectorRepository` raises instead of in-memory mode; tests inject fakes (done before S01-09) | 3 | Errors propagate; tests use fakes, no network waits; behaviour change on errors documented in report + review |
| S01-09 | Sprint + M0 review | 2 | `docs/sprints/S01-review.md` |

## M1 — Agent desktop + CRM data (S02–S04)
**Visual reference:** Figma community file "Chat UI" (https://www.figma.com/community/file/1057195320253196766/chat-ui).
Take its colours, spacing and clean chat layout; drop emojis and robot/chatbot styling; optimise for a busy CSR
(clear hierarchy, few clicks, keyboard shortcuts, readable Arabic). The style guide derived from the reference is
`docs/design/ui-reference/STYLE_GUIDE.md` (layout mapping, colour tokens, typography, UX rules).

| ID | Ticket | Est |
|---|---|---|
| S02-00 | **Design pack M1**: screen map + wireframes (login, inbox, workspace 3 panes, customer 360, ticket form, wrap-up, KB viewer); **ERD** of the CRM (customers, lines, plans, bills, payments, usage, tickets, ticket events, CSR users, roles, dispositions, audit); UI ↔ API sequence diagrams; why Reflex and how state/live updates work | 8 |
| S02-01 | Design system from Ziad's style guide: colour tokens (light/dark), typography (Arabic + Latin), spacing, components (buttons, tables, chips, panes), RTL rules | 6 |
| S02-02 | Data model + Alembic migrations from the approved ERD | 8 |
| S02-03 | Synthetic seed (Faker `ar_EG`): 500 customers, plans, bills, usage, 2,000 tickets; deterministic; data-quality checks on the seed | 8 |
| S02-04 | Sprint review | 2 |
| S03-01 | Auth: CSR / supervisor / admin, JWT, password hashing, rate-limited login | 6 |
| S03-02 | CRM API: customer search, customer 360, tickets CRUD, dispositions, audit of CSR actions | 10 |
| S03-03 | Reflex app shell in `apps/web/`: login, layout, design system applied | 8 |
| S03-06 | **Bilingual UI (Arabic + English)**: i18n layer with `ar.json` / `en.json`, language switch saved per CSR, full RTL mirroring for Arabic, `dir="auto"` for message content, AR/EN date and number formats, test that both files have the same keys | 6 |
| S03-04 | Inbox: tickets list, filters, SLA timers, assignment | 8 |
| S03-05 | Sprint review | 2 |
| S04-01 | Workspace: conversation pane (ticket text for now) · customer 360 + ticket form · copilot panel calling v1 `/solve` | 14 |
| S04-02 | Wrap-up form (manual for now), disposition codes, audit log | 6 |
| S04-03 | KB viewer: list sources, preview, download (reuse v1 endpoints) | 4 |
| S04-04 | UI tests (state/unit) + manual test script; screenshots for README | 6 |
| S04-05 | Sprint + M1 review | 3 |
**Exit**: CSR logs in, finds a customer, works a ticket end to end **in both Arabic and English**; copilot panel shows the v1 answer; UI matches the approved design.

## M2 — Knowledge base & data pipelines (S05–S07)
Goal: the best possible data before any model choice. Embedding/indexing keeps the current Cohere setup until M3.

| ID | Ticket | Est |
|---|---|---|
| S05-00 | **Design pack M2**: pipeline architecture (sources → fetch → extract → clean/normalise → validate → chunk → enrich → index), **ERD** of the source registry (source, document, version, chunk, quality_check, ingestion_run), orchestration choice (simple job runner vs Prefect/Dagster — explained), data contracts per stage | 8 |
| S05-01 | Source registry + ingestion runs in Postgres; idempotent runs keyed by content hash | 8 |
| S05-02 | Polite crawler (robots.txt, rate limit, user agent), snapshots stored with dates | 6 |
| S05-03 | Collect public sources: WE, Vodafone EG, Orange EG, e& EG (offers, FAQs, T&Cs, roaming), NTRA consumer rules, router/ONT manuals. **List sizes and ask before bulk downloads** | 10 |
| S05-04 | Sprint review | 2 |
| S06-01 | Extractors v2: native-text PDF first, OCR only when needed (keep Gemini OCR for now; local OCR evaluated in M3 if small enough), XLSX price tables (row-aware), FAQ JSON/CSV, HTML with JS-rendered pages only if needed | 12 |
| S06-02 | Cleaning + Arabic normalisation (alef/yaa/taa marbuta, diacritics, tatweel, digits), boilerplate removal, dedup (exact + near-duplicate) | 8 |
| S06-03 | Data-quality checks per stage (empty/short docs, encoding, language detection, missing prices/numbers vs source, table integrity) with a quality report per run | 8 |
| S06-04 | Sprint review | 2 |
| S07-01 | Chunking v2: rule/section-aware chunks, contextual chunk headers, parent-document links, metadata (source, version, date, language, intent, section) | 10 |
| S07-02 | Change detection + re-index job; freshness in citations | 6 |
| S07-03 | Gold eval sets: extraction ground truth for new sources + ≥ 150 retrieval questions AR/EN, human-verified with the existing HITL tool | 12 |
| S07-04 | Eval harness skeleton `evals/harness/` (dataset loader, runner, metrics registry, md + json reports); extraction + data-quality reports | 8 |
| S07-05 | Sprint + M2 review | 3 |
**Exit**: `evals/reports/kb/A/` with extraction metrics per format, data-quality metrics per stage, freshness; ≥ 150 verified questions.

## M3 — Model providers + retrieval baseline (S08–S09)
| ID | Ticket | Est |
|---|---|---|
| S08-00 | **Model selection study** for all 5 roles (LLM, embedding, reranker, ASR, vision/OCR) following `docs/design/MODEL_SELECTION.md`: shortlist via the Hugging Face MCP/Hub, licences, sizes, Egyptian dialect + code-switching + Franco test slices; **Design pack M3**: provider interfaces (class diagram), serving topology and VRAM budget | 8 |
| S08-01 | LLM interface (`generate_json`, `stream`, usage, timeouts): Gemini + OpenAI-compatible (llama.cpp / vLLM) | 6 |
| S08-02 | Embedding + rerank interfaces: Cohere, local BGE-M3 / bge-reranker (CPU), TEI (HTTP); collection name includes embedder id | 6 |
| S08-03 | **Ask Ziad** before downloads: llama.cpp CUDA build + the shortlisted models (sizes listed; prefer GGUF/int8/ONNX) | 1 |
| S08-04 | `deploy/local/`: start `llama-server` tuned for 4 GB; v1 runs fully local | 4 |
| S08-05 | Load-test skeleton (Locust) + capacity finder | 4 |
| S08-06 | Sprint review | 2 |
| S09-01 | Retrieval suite on the M2 gold set: hit@k, MRR, context recall/precision, AR vs EN | 6 |
| S09-02 | Compare Cohere vs BGE-M3 dense, BM25 vs BGE-M3 sparse, rerank on/off, RRF params; decide ADR-4 | 10 |
| S09-03 | Performance (p50/p95, QPS) + KPI (policy lookup time) reports; M3 review | 8 |
**Exit**: retrieval reports A; default local retrieval config chosen.

## M4 — Generation baseline (S10–S11)
| ID | Ticket | Est |
|---|---|---|
| S10-00 | **Design pack M4**: prompt/context architecture, output schema, judge setup | 3 |
| S10-01 | Grounding prompt v2 (facts only from context, all fees/thresholds, citation per step, "not in policy") | 8 |
| S10-02 | JSON robustness (grammar / `response_format`, one repair retry) ≥ 98% valid | 5 |
| S10-03 | Faithfulness / claim-check metric with an independent judge; AR vs EN; dialect match | 10 |
| S10-04 | Streaming on llama.cpp; TTFT and tokens/s | 5 |
| S11-01 | Context budget for 4 GB; token accounting in Langfuse | 6 |
| S11-02 | Compare Qwen 3B vs 1.5B vs Gemini | 8 |
| S11-03 | Concurrency (parallel slots) + Locust `/solve` capacity; acceptance proxy KPI; M4 review | 12 |
**Exit**: faithfulness ≥ 0.75 local, JSON ≥ 98%, capacity published.

## M5 — Channels (S12–S13)
S12-00 design pack (channel adapter pattern, message ERD, sequence diagrams per channel) · Conversation/Message model +
Redis pub/sub · WhatsApp simulator in exact Meta Cloud API format + signature check + adapter for the real API ·
outbound sender · routing to CSRs · web chat widget on a landing page · email/form → ticket · copilot updates per
customer message · channel reports (delivery, msgs/s, p95, queue wait, SLA). **Exit**: 3 channels in one inbox.

## M6 — Agent copilot (S14–S16)
S14-00 design pack (LangGraph state diagram, tool catalogue, memory ERD, guardrail flow) · agent graph with streaming ·
read tools (customer, bills, usage, outage, line test, kb_search) · tool-call eval (60 scenarios) · write tools with
CSR approval (ticket, field visit, credit ≤ limit, escalate) · memory (session Redis, customer summary, CSR feedback) ·
context builder · guardrails + PII masking · auto wrap-up · AHT simulation vs KB-search baseline · reports.
**Exit**: tool accuracy ≥ 0.9; measured AHT/ACW reduction.

## M7 — Speech (S17–S19)
S17-00 design pack (audio pipeline, live-call topology with LiveKit) · **ask before download** faster-whisper small ·
STT service with VAD · voice notes in the simulator · recordings → transcript → diarisation (check size/licence) →
summary · Egyptian speech eval (40–60 consented recordings, WER/CER) · small vs turbo · live calls (LiveKit, browser
softphone, customer tab) · streaming STT + incremental suggestions · live-call load test. **Exit**: WER + limits reported.

## M8 — MCP + hardening (S20–S21)
S20-00 design pack · MCP servers (crm, kb, tickets) · tool eval through MCP · Prometheus + Grafana + alerts · CI eval
gate · security pass (rate limits, secrets, audit completeness, backups) · checklist audit + runbook. **Exit**: ≥ 90%.

## M9 — Stage A baseline report (S22)
Re-run all suites + load tests on the laptop → `evals/reports/STAGE_A.md`; README with capacity + KPI table; demo.

## M10 — Stage B / C (S23–S24)
Kaggle/Colab scripts (vLLM Qwen 7B/14B AWQ, TEI, whisper large-v3; downloads on the cloud box) → `STAGE_B.md`;
optional ≤ $10 run → final side-by-side table (quality, latency, capacity, cost per 1k contacts).

---

## Status
| Sprint | Status |
|---|---|
| S01 | not started |
