# M0 — Restructure & Foundation (design pack, S01-00)

Status: **approved by Ziad (2026-10-25)** with the corrections in section 11.
Branch: `sprint/01-foundation`. Covers tickets S01-01 … S01-09 in [../SPRINTS.md](../SPRINTS.md).

**Goal of M0 in one sentence:** the v1 app keeps doing exactly what it does today (same endpoints, same JSON),
but it lives in a proper installable package, starts fast, and has Postgres, Redis, migrations, settings and CI
ready for M1.

---

## 1. Where we are today

```text
src/                      ← put on sys.path by hand (fragile)
├── api/main.py           app + startup ingestion + CORS "*"
├── controllers/          5 routers
├── dependencies/         FastAPI DI
├── services/             agent_assist · ingestion · cohere · gemini · sparse BM25
├── repositories/         base + qdrant
├── ingestion/            extractors · chunkers · factories
├── models/               api_models · document_models
├── core/                 logger · singletons · observability
└── config/settings.py
experiments/              notebooks + extraction_eval + rag_eval + reports  (imports src via sys.path hack)
static/                   v1 UI
data/                     raw · ground_truth
```

What hurts today, and which ticket fixes it:

| Problem | Why it matters | Fixed in |
|---|---|---|
| `sys.path` is edited in `main.py`, `conftest.py`, `pytest.ini`, the Dockerfile and every notebook | Imports only work from some folders; top-level names like `config`, `core`, `models` can clash with other installed libraries | S01-01 |
| Folders are grouped by *kind* (controllers, services, models) instead of by *feature* | When M1 adds CRM and M5 adds channels, `services/` would mix KB, CRM and channel code | S01-02 |
| The app scrapes te.eg and runs OCR **during startup** | Start-up takes minutes and needs the internet and API keys; a failure is only logged as a warning | S01-07 |
| `CORS allow_origins=["*"]`, Qdrant `timeout=10.0` hard-coded | Hard-coded config (anti-pattern); `*` with credentials is unsafe | S01-04, S01-08 |
| One unpinned `requirements.txt` with test tools, unused packages (`google-genai`, full `langchain`) | Bigger Docker image, builds not reproducible | S01-08 |
| No Postgres, Redis, migrations, lint in CI | M1 needs them on day one | S01-04 … S01-08 |

---

## 2. Target layout after S01

```text
src/telecopilot/          installed with pip install -e .
├── api/                  main.py · dependencies.py · schemas.py · readiness.py
│   └── routers/          assist · ingest · scraper · documents · health
├── agent/                assist_service.py (today's AgentAssistService)
├── kb/                   models.py · extractors/ · chunkers/ · factories.py
│                         repositories/ (base, qdrant) · sparse.py · retrieval.py
│                         ingestion_service.py · ingest.py (CLI)
├── llm/                  cohere.py · gemini.py (unchanged behaviour)
├── db/                   base.py · session.py
├── audit/                models.py (AuditLog table)
├── core/                 logger · singletons · observability
└── config/               settings.py
migrations/ + alembic.ini Alembic
evals/                    notebooks/ · extraction/ · rag/ · reports/
deploy/compose/           docker-compose.yml: qdrant · postgres · redis · app
docker-compose.yml        thin root file: include deploy/compose/…
```

File-by-file moves (done with `git mv`, so `git log --follow` keeps each file's history):

| Today | After S01 | Note |
|---|---|---|
| `src/api/main.py` | `telecopilot/api/main.py` | No more `sys.path`; no startup ingestion (S01-07) |
| `src/controllers/*_controller.py` | `telecopilot/api/routers/{assist,ingest,scraper,documents,health}.py` | Same paths, same JSON |
| `src/dependencies/dependencies.py` | `telecopilot/api/dependencies.py` | DI wiring belongs to the API layer |
| `src/models/api_models.py` | `telecopilot/api/schemas.py` | HTTP request/response shapes |
| `src/models/document_models.py` | `telecopilot/kb/models.py` | Chunks, search results, extracted docs |
| `src/ingestion/*` | `telecopilot/kb/{extractors,chunkers,factories.py,base.py}` | Unchanged code |
| `src/repositories/*` | `telecopilot/kb/repositories/{base,qdrant}.py` | Vector store is a KB concern |
| `src/services/sparse_embedding_model.py` | `telecopilot/kb/sparse.py` | BM25 is retrieval, not an LLM |
| `src/services/ingestion_service.py` | `telecopilot/kb/ingestion_service.py` | |
| `src/services/cohere_service.py`, `gemini_service.py` | `telecopilot/llm/cohere.py`, `gemini.py` | Unchanged until M3 provider interfaces |
| `src/services/agent_assist_service.py` | `telecopilot/agent/assist_service.py` | See decision D3 |
| `src/core/*`, `src/config/*` | `telecopilot/core/*`, `telecopilot/config/*` | |
| `experiments/*.ipynb` | `evals/notebooks/*.ipynb` | |
| `experiments/extraction_eval/` | `evals/extraction/` | |
| `experiments/rag_eval/` | `evals/rag/` | |
| `experiments/reports/*` | `evals/reports/kb/v1/` (extraction, HITL log), `evals/reports/generation/v1/` (RAGAS) | Matches the `evals/reports/<service>/<stage>/` rule in PLAN.md |
| `requirements.txt` | `pyproject.toml` (runtime deps + `dev` and `eval` extras) | One source of truth |
| `docker-compose.yml` | `deploy/compose/docker-compose.yml` + thin root file | Root keeps `docker compose up` working |
| `static/`, `data/` | unchanged | Reflex replaces `static/` in M1 |

`crm/`, `channels/`, `speech/`, `mcp_servers/`, `worker/` and `apps/web/` from the PLAN layout are **not** created in
S01. Empty folders for the future would be YAGNI; each appears in the milestone that fills it.

---

## 3. Layer dependencies (which package may import which)

```mermaid
%%{init: {"themeVariables": {"fontSize": "18px"}}}%%
flowchart TB
  api["api"] --> agent["agent"]
  api --> kb
  api --> llm
  api --> db
  api --> core
  agent --> kb["kb"]
  agent --> llm
  agent --> core
  kb --> llm["llm"]
  kb --> core
  llm --> core["core"]
  audit["audit"] --> db["db"]
  db --> config["config"]
  core --> config
```

| Package | Job |
|---|---|
| `api` | HTTP: routers, schemas, DI, readiness |
| `agent` | Orchestration: retrieve → generate |
| `kb` | Extract, chunk, index, retrieve |
| `llm` | Cohere and Gemini clients |
| `db` / `audit` | SQLAlchemy base + session / AuditLog table |
| `core` | Logging, singletons, tracing |
| `config` | Settings |

Rule: **arrows point downwards only.** A lower package never imports a higher one (for example `kb` never imports
`agent` or `api`). This is the "no wrong-way imports" rule from CODE_GUIDELINES. In plain words: the parts at the
bottom (settings, logging, database) don't know who uses them, so they can be tested alone and reused by the
worker, the CLI and the future Reflex app.

Every package may also import `config` (the bottom layer); those arrows are left out of the drawing to keep it
readable. `api → llm` exists because the DI wiring in `api/dependencies.py` builds the Cohere and Gemini services.

`core` and `db` are both foundation packages and depend **only on `config`** (and third-party libraries). They
never import each other. Anything that needs several of them at once (for example readiness) lives in `api`.

The rule is enforced by a test (`tests/test_layers.py`) that parses every module's imports with `ast` and fails on
any arrow not in the diagram.

`kb → llm` exists because ingestion and retrieval need embeddings and reranking (Cohere today). In M3 this becomes
`kb → llm.Embedder / llm.Reranker` interfaces (ADR-2); the direction stays the same.

---

## 4. Startup and readiness (S01-07)

Today startup scrapes and indexes everything. After S01-07 the API only connects; indexing is a separate command.

```mermaid
%%{init: {"themeVariables": {"fontSize": "18px"}}}%%
sequenceDiagram
  participant Dev as Ziad / CI
  participant CLI as Ingest CLI
  participant API
  participant Q as Qdrant
  participant P as Postgres
  participant R as Redis
  Dev->>API: start
  API-->>Dev: up in seconds
  Dev->>CLI: kb.ingest --all
  CLI->>Q: upsert chunks
  Dev->>API: GET /api/ready
  API->>Q: list collections
  API->>P: SELECT 1
  API->>R: PING
  API-->>Dev: 200 ready / 503 not_ready
```
The ingestion command is `python -m telecopilot.kb.ingest --all`. The `/api/ready` response is
`{"status": "ready" | "not_ready", "checks": {...}}`.

- `/api/health` keeps today's response shape exactly (v1 UI and tests use it).
- `/api/ready` is new infrastructure, not a feature: it answers "can this instance serve traffic?" Each check
  returns `ok`, `latency_ms` and, on failure, a short `error`. An empty Qdrant is *ready* (the CLI fills it); a
  Qdrant, Postgres or Redis that cannot be reached makes the whole response **503 not ready**.
- `api/readiness.py` composes small checks owned by each layer: `db.session.ping()`, the Redis client's `ping()`
  (client is a singleton in `core/singletons.py`), and `ping()` on the vector repository interface. The API layer is
  the only place allowed to know all three.
- Logging: `core/logger.py` gets `configure_logging()`; importing the module has no side effects (no sinks, no
  `logs/` folder). The app lifespan and the ingestion CLI call it once at start-up.
- In Docker Compose the ingestion job is a one-off command:
  `docker compose run --rm app python -m telecopilot.kb.ingest --all`.

---

## 5. Data foundation (S01-04 … S01-06)

```mermaid
%%{init: {"themeVariables": {"fontSize": "18px"}}}%%
flowchart LR
  app["app<br/>python:3.11-slim"] --> qd[("Qdrant 1.13")]
  app --> pg[("Postgres 16")]
  app --> rd[("Redis 7")]
```

First (and only) table in S01, so Alembic and the session dependency are proven end to end:

```mermaid
%%{init: {"themeVariables": {"fontSize": "18px"}}}%%
erDiagram
  AUDIT_LOG {
    bigint id PK
    timestamptz occurred_at
    string actor
    string action
    string entity_type
    string entity_id
    json details
  }
```

| Column | Meaning |
|---|---|
| `occurred_at` | Server default `now()` |
| `actor` | CSR id, or `system` until auth exists (M1) |
| `action` | e.g. `ingest.run`, `ticket.update` |
| `entity_type`, `entity_id` | Nullable: what the action touched |
| `details` | Free-form JSON context |

- **Sync SQLAlchemy 2** (not async): every existing service is synchronous, FastAPI runs sync dependencies in a
  thread pool, and at 20–100 CSRs this is far below any limit. Async can be added if a load test (ADR-9) shows a need.
- Driver: `psycopg` 3 (binary wheel). Tests use **SQLite in memory**, so CI needs no Postgres.
- `get_db_session()` is a FastAPI dependency in `db/session.py`, exposed through `api/dependencies.py` like the others.
- Alembic lives at the repo root (`alembic.ini`, `migrations/`); `migrations/env.py` reads `DATABASE_URL` from
  settings, never from the ini file, so no credentials are committed.
- S01 writes **no** audit rows yet; who writes what is decided in the M1 ERD (S02-00). The table only proves the
  plumbing.

New settings (S01-04), all overridable from `.env`, defaults keep today's behaviour:

| Setting | Default | Why |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://telecopilot:telecopilot@127.0.0.1:5432/telecopilot` | Local compose Postgres (IPv4: see S01-07 report) |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Local compose Redis |
| `QDRANT_TIMEOUT_S`, `DB_TIMEOUT_S`, `REDIS_TIMEOUT_S`, `SCRAPER_TIMEOUT_S` | today's values: Qdrant 10 s, scraper 30 s; DB 5 s and Redis 2 s (new) | Replaces hard-coded numbers |
| `CORS_ORIGINS` | `["http://localhost:8000"]` | Replaces `*` (S01-08 wires it) |
| `LLM_PROVIDER` / `EMBED_PROVIDER` / `RERANK_PROVIDER` | `gemini` / `cohere` / `cohere` | Placeholders for ADR-2; validated as a fixed list of names, only today's value is accepted until M3 adds the others |
| `DATA_RAW_DIR`, `STATIC_DIR` | `data/raw`, `static` (relative to the working dir) | Needed once code runs from an installed package (see risk R2) |

---

## 6. Migration steps (order of commits)

```mermaid
%%{init: {"themeVariables": {"fontSize": "18px"}}}%%
flowchart TB
  s0["S01-00 design"] --> s1["S01-01 package + imports"]
  s1 --> s2["S01-02 kb / llm / agent / api"]
  s2 --> s3["S01-03 experiments → evals"]
  s3 --> s4["S01-04 settings v2"]
  s4 --> s5["S01-05 compose + PG + Redis"]
  s5 --> s6["S01-06 SQLAlchemy + Alembic"]
  s6 --> s7["S01-07 ingest CLI + /api/ready"]
  s7 --> s8["S01-08 CORS, deps, CI"]
  s8 --> s10["S01-10 no silent fallbacks"]
  s10 --> s11["S01-11 FastEmbed BM25"]
  s11 --> s9["S01-09 review"]
```

How each step stays safe:
1. **S01-01 in three commits**: (a) `git mv src/* src/telecopilot/` + `pyproject.toml`; (b) mechanical import
   rewrite `from config.` → `from telecopilot.config.` etc., delete `sys.path` code; (c) `ruff format` +
   `ruff check --fix` on the whole repo as its own commit, so the move commits stay readable and formatting noise
   is isolated. Tests must be green after (b) and (c).
2. **S01-02** is moves plus the three small behaviour-neutral clean-ups in D4. Endpoint paths and JSON shapes are
   checked by the existing controller tests plus one new test that snapshots the OpenAPI path list before/after.
3. Every ticket ends with `pytest`, `ruff check`, `ruff format --check` green before it is ticked.

---

## 7. Decisions (options, choice, why)

**D1 — Package build tool.** Options: setuptools · hatchling · poetry · uv. **Choice: setuptools** with a
`src/` layout in `pyproject.toml`. Why: already installed, no new tool to learn or download, standard
`pip install -e .`. Poetry/uv would add a second dependency manager.

**D2 — Group by feature (`kb`, `llm`, `agent`) instead of by kind (`services`, `controllers`).** Why: M1+ adds CRM,
channels and speech; feature folders keep each feature's model, service and repository together, so a change to
"KB" touches one folder. Controllers stay together under `api/routers/` because they are all HTTP and thin.

**D3 — Where `AgentAssistService` goes.** Options: (a) `kb/` · (b) a new `assist/` package · (c) **`agent/`**.
Choice: (c). It orchestrates retrieval + generation, which is exactly what the M6 LangGraph agent will do; the
PLAN layout already has `agent/`. Putting it in `kb/` would make `kb` depend on the LLM generator and blur the KB's
job.

**D4 — Small clean-ups done while moving (behaviour-neutral, covered by tests).** I propose these three because
they touch the files being moved anyway and each removes a CODE_GUIDELINES violation:
1. *Extract retrieval*: move `_embed_query`, `_hybrid_search`, `_rerank` out of `AgentAssistService` (342 lines,
   two jobs) into `kb/retrieval.py` (`HybridRetriever`). The ticket lists "retrieval" under `kb/`, and the M3
   retrieval eval (S09-01) needs retrieval without the LLM.
2. *DRY ingestion*: `ingest_url` and `ingest_file` repeat the same extract → chunk → embed → upsert code; one
   private helper. Returned dicts stay byte-for-byte the same.
3. *One sparse vector type*: `SparseVector` (BM25 model) duplicates `SparseVectorData` (pydantic); keep the
   pydantic one.
Anything bigger is a proposal for later (section 9), not done in S01.

**D5 — Ingestion as a CLI, not a startup hook (ADR-10 direction).** Options: keep startup ingestion behind a flag ·
background task inside the API · **separate CLI job**. Choice: CLI. Why: the API starts in seconds, ingestion
errors are visible (non-zero exit code instead of a warning), and in M2 the same entry point becomes the pipeline
job. A flag would be a "speculative option" and a background task hides failures.

**D6 — Dependencies.** Runtime deps in `[project.dependencies]` pinned with `==` to the versions already installed
on the laptop (no new downloads, reproducible), each checked to support Python 3.11 (Docker/CI use 3.11; CI green
is the proof); `dev` extra = pytest, pytest-asyncio, httpx, ruff; `eval` extra =
ragas, langchain-openai, langchain-cohere, jupyter bits used by the notebooks. Remove unused `google-genai` and the
full `langchain` (only `langchain-text-splitters` is imported). `requirements.txt` is deleted (one source of truth).

**D7 — Docker.** Same `python:3.11-slim` base (already cached). Pip cache mount
(`RUN --mount=type=cache,target=/root/.cache/pip`) so rebuilds reuse downloaded wheels instead of downloading again.
Try dropping `build-essential` (≈ 200 MB in the image) if every dependency has a wheel; keep it only if a build
fails. `pip install .` (non-editable) inside the image.

**D8 — Compose file location.** `deploy/compose/docker-compose.yml` holds the services; the root file is
`include: [deploy/compose/docker-compose.yml]` (Compose ≥ 2.20) and keeps `name: telecopilot-ai`, so the existing
Qdrant volume and `docker compose up` keep working. Container names and the `qdrant_storage` volume stay the same.
Later profiles (`local-gpu`, `api-fallback`, `cloud-gpu`) go in the same folder when M3 needs them.

**D9 — Ruff rules.** `E, F, W, I, B, UP`, line length 120 (matches the current code). Started in S01-01 so every
later ticket can run `ruff check` as the agent prompt requires; CI enforcement is added in S01-08.

**D10 — Evals import path.** Notebooks set the working directory to the repo root (they need `data/` anyway) and
import `telecopilot` from the installed package. `evals/` is a plain folder with `__init__.py`, imported from the
repo root; it is not installed with the app because the app must never depend on eval code.

---

## 8. Risks

| # | Risk | Mitigation |
|---|---|---|
| R1 | Big import rewrite breaks something tests don't cover (notebooks, `build_notebook.py`, scripts) | Grep for every old top-level name after the rewrite; open each notebook's import cell with `python -c` equivalents |
| R2 | After `pip install .` in Docker, `__file__`-based paths (`static/`, `data/raw/`) point into site-packages | `STATIC_DIR` / `DATA_RAW_DIR` settings relative to the working dir (`/app` in Docker) |
| R3 | Rebuilding the Docker image re-downloads Python packages (estimate 150–250 MB) | Pip cache mount; I will measure the first rebuild and **ask before it if the estimate is over 200 MB** |
| R4 | New images: `postgres:16-alpine` ≈ 100 MB, `redis:7-alpine` ≈ 15 MB download | Under the 200 MB limit; sizes will be listed in the review |
| R5 | Docker Desktop is not running right now | S01-05/06 need it; I'll ask you to start it when I get there |
| R6 | Tests take ~42 s today because they wait on Qdrant timeouts | S01-07 removes startup ingestion; S01-10 makes tests inject fakes instead of waiting for fallbacks |
| R7 | Moving `ingestion` code changes the `logger` module name shown in logs | Cosmetic only; noted |
| R8 | `pip install -e .` on OneDrive paths can be slow or lock files | If it fails, fall back to a `.pth` editable install mode (`--config-settings editable_mode=compat`) |

---

## 9. Found while reading — proposals, **not** built in S01

These conflict with CLAUDE.md rules but fixing them changes behaviour, so they belong to later tickets:
- ~~Silent fallbacks~~ → now ticket **S01-10** (see section 11).
- ~~Logger side effects at import~~ → now part of **S01-07**.
- **`documents` router holds a hard-coded catalogue and ~250 lines of HTML templates** (business logic in a route).
  Proposal: the KB source registry in M2 (S05-01) replaces the catalogue; preview rendering moves into `kb/`.
- **Deprecated SDK**: `google-generativeai` is deprecated in favour of `google-genai`. Proposal: switch inside the
  Gemini provider in S08-01.
- ~~Dead code `GeminiService.generate_reply_stream`~~ → deleted in S01-02 (approved).

---

## 10. Open questions for Ziad

1. OK to do the three D4 clean-ups (retrieval extraction, DRY ingestion, one sparse vector type) and delete the dead
   sync stream method inside S01-02, or should S01 be strictly moves only?
2. Should `/api/ready` also return `503` when Postgres/Redis are down even though v1 doesn't use them yet? (My
   default: yes, since they are part of the compose stack from S01-05 on.)
3. Do you want a small test that enforces the layer arrows in section 3 (parses imports, ~30 lines, no new
   dependency)? My recommendation: yes, it stops wrong-way imports from creeping in during M1–M6.
4. Logger clean-up (section 9): now in S01-07, or later?

---

## 11. Approval notes (Ziad, 2026-10-25)

Corrections applied above:
1. **`core` must not import `db`.** Readiness moved from `core/readiness.py` to `api/readiness.py`; it composes
   per-layer checks (`db.session.ping()`, Redis `ping()`, vector repository `ping()`). Section 3 diagram updated:
   `core` and `db` depend only on `config`.
2. **Pins**: pinned to installed versions, each verified to support Python 3.11; CI on 3.11 is the proof.

Answers to section 10:
1. Yes to the three D4 clean-ups and deleting the dead sync stream method, **each in its own commit**, with tests
   showing outputs are unchanged.
2. Yes, `/api/ready` returns 503 when Qdrant, Postgres or Redis is unreachable.
3. Yes, add the layer-import test with the corrected arrows.
4. Logger clean-up now, in S01-07.

New ticket **S01-10 — remove silent fallbacks** (3 h), done before the S01-09 review:
- `CohereService` raises on failure instead of returning pseudo-embeddings or fake rerank scores (fake vectors
  could silently corrupt Qdrant once ingestion runs as a standalone job).
- `QdrantVectorRepository` raises when Qdrant is unreachable instead of switching to in-memory mode.
- Tests inject fakes/stubs instead of relying on these fallbacks (also fixes the ~42 s test time).
- Behaviour changes only on errors; documented in the ticket report and the review.
