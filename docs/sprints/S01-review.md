# S01 review — M0 Restructure & foundation

Status: **in progress** (filled ticket by ticket; finalised in S01-09).

## Ticket reports

### S01-01 — pyproject, `src/telecopilot`, absolute imports — ✅ done
**What changed**
- `src/*` moved to `src/telecopilot/*` with `git mv` (history kept; `git log --follow` works).
- `pyproject.toml` (setuptools, `requires-python >= 3.11`): runtime deps copied unchanged from `requirements.txt`,
  a `dev` extra (pytest, pytest-asyncio, ruff), pytest config (from `pytest.ini`), ruff config.
  `requirements.txt`, `pytest.ini` and `tests/conftest.py` deleted (their only job was dependency lists / `sys.path`).
- 148 imports rewritten `from config.…` → `from telecopilot.config.…` (script, then grep for leftovers).
- `sys.path` edits removed from `telecopilot/__init__.py`, `api/main.py`, `conftest.py`.
- `api/__init__.py` no longer imports the app: importing *any* `telecopilot.api.*` module used to build the whole
  FastAPI app (slow, and a circular-import trap once `api/dependencies.py` moves there in S01-02).
- Dockerfile: `pip install .` with a BuildKit pip cache mount; CMD `telecopilot.api.main:app`. CI: `pip install -e ".[dev]"`.
- ruff: `ruff format` + `ruff check --fix` over the repo in its own commit, plus manual fixes: `raise … from e`,
  dead counters in the eval code, and a **real bug**: `experiments/extraction_eval/hitl.py` used a nested f-string
  that is only valid on Python 3.12, so it failed on 3.11 (Docker/CI).

**Files**: `pyproject.toml`, `Dockerfile`, `.github/workflows/ci.yml`, `README.md`, `CLAUDE.md`, all of `src/`, `tests/`
(imports), `experiments/extraction_eval/*`, `experiments/rag_eval/build_notebook.py` (format/lint only).

**Why**
- *setuptools* (D1): already installed, standard, no second package manager to learn.
- *Three commits* (move → imports → format): each diff is readable on its own; the format commit can be skipped
  when reviewing logic.
- *E501 off*: ruff's formatter already wraps code at 120 chars; what's left over 120 are prompt and HTML string
  literals, and splitting those makes them harder to read. Rejected: per-line `# noqa` (noise in 30+ places).
- *B008 whitelist for `Depends`*: that is FastAPI's documented DI idiom, not a bug.
- *Pip cache mount now, not in S01-08*: `pip install .` needs the source, so the dependency layer is rebuilt on
  every code change; without the cache that would re-download all wheels each build (bandwidth rule).
- Notebook imports are left for S01-03, which moves and fixes the notebooks in one go.

**Evidence**
- `pip install --no-build-isolation --no-deps -e .` OK; `import telecopilot` works from another folder.
- `uvicorn telecopilot.api.main:app` (API keys blanked, Qdrant down): `/api/health` 200 after 7 s, `/` 200,
  `/api/v1/policies` 200.
- `pytest`: 16 passed (15–19 s; baseline was 42 s. Cause of the difference not investigated; the remaining time is Qdrant
  connection timeouts, which S01-10 removes).
- `ruff check`: all checks passed; `ruff format --check`: 78 files already formatted.
- **Not yet verified**: `docker build` (Docker Desktop not running) — verified in S01-05.

**Behaviour change**: none.

### S01-02 — group into `api / agent / kb / llm` + approved clean-ups — ✅ done
**What changed** (8 commits, each green on its own)
1. *Contract tests first* (`tests/test_v1_contract.py` + `tests/golden/*.json`), generated from the code **before**
   any refactor: the full OpenAPI spec (all 12 endpoints and every request/response schema), the `/solve` JSON, the
   SSE event sequence, and the outputs of `ingest_file` / `ingest_url` (result dict + every chunk's metadata).
   Shared fakes moved from `test_controllers.py` to `tests/fakes.py` and a `conftest.py` fixture.
2. *Moves* (`git mv`): `controllers/` → `api/routers/{assist,ingest,scraper,documents,health}.py`,
   `dependencies/` → `api/dependencies.py`, `api_models` → `api/schemas.py`; `ingestion/`, `repositories/`,
   BM25, ingestion service, document models → `kb/`; Cohere/Gemini → `llm/`; `AgentAssistService` →
   `agent/assist_service.py`. Re-export `__init__.py` files became plain package markers. `tests/test_layers.py`
   enforces the approved arrows.
3. *D4.1* `kb/retrieval.py` `HybridRetriever` (embed query, hybrid search, rerank) extracted from `AgentAssistService`.
4. *D4.2* `IngestionService._index_source`: one extract → chunk → embed → upsert path for URLs and files.
5. *D4.3* `SparseVectorData` is the only sparse vector type (pinned-weights test committed first).
6. Deleted the unused sync `GeminiService.generate_reply_stream`.

**Why**
- *Golden files instead of hand-written asserts*: they compare **everything** (every field, every chunk), so a
  refactor that silently changes one value fails. Timing fields and absolute paths are excluded (they differ per
  run/machine). Rejected: relying on the existing controller tests, which only check a few keys.
- *Empty `__init__.py`*: the re-exports were pass-through code, and importing `kb.models` loaded every extractor
  (PyMuPDF, clients). Direct imports are explicit and cheap.
- *Retriever exposes three public steps, not one `retrieve()`*: the service times and traces each step separately
  (latency breakdown in the JSON). A combined method would have no caller yet (YAGNI); M3's retrieval eval can add it.
- *Retriever and ingestion take the BM25 model as a constructor argument*: they now share the DI singleton instead
  of each building its own (dependency inversion; tests can pass any model).
- *Layer test with `ast`* instead of `import-linter`: ~40 lines, no new dependency. Verified it fails on a planted
  `kb → api` import.
- Diagram correction: `api → llm` (DI wiring builds the clients) and `* → config` were real edges missing from the
  section 3 drawing; added to the design pack.

**Evidence**: `pytest` 25 passed; `ruff check` / `ruff format --check` clean. Golden files unchanged across all
S01-02 commits (no golden file was regenerated after commit 1). EMPTY-branch test also run against the old
`IngestionService`: same dicts.

**Behaviour change**: none. (Internal constructor signatures changed: `AgentAssistService(retriever, gemini_service)`,
`IngestionService(vector_repo, cohere_service, sparse_model)`; the eval notebook call sites are fixed in S01-03.)

**Found: BM25 indices are not stable across processes** (not fixed, needs a decision). `SparseEmbeddingModel` maps
tokens with Python's built-in `hash()`, which is randomised per process (`PYTHONHASHSEED`). Verified: the same text
gives `[18954, 20557, 76511]` in one process and `[22140, 23136, 44453]` in the next. Sparse vectors stored by one
process never match queries from another, so BM25 silently contributes noise after any API restart in v1, and on
**every** query once S01-07 moves ingestion to its own CLI process. Proposal: a stable hash (e.g. `zlib.crc32` or
`hashlib.blake2b` of the UTF-8 token) + re-index. Changes stored indices only; weights stay the same.

### S01-03 — `experiments/` → `evals/` — ✅ done
**What changed**
- `evals/notebooks/` (3 notebooks), `evals/extraction/` (ground truth builder, metrics, LLM judge, HITL),
  `evals/rag/` (`build_notebook.py`, `eval_questions.json`), `evals/reports/kb/v1/` (HITL log) and
  `evals/reports/generation/v1/` (RAGAS csv/json/png). `.gitignore` log rule follows the move.
- Notebook setup cells: `os.chdir(<repo root>)` instead of three `sys.path.insert` calls; `telecopilot` comes from
  the installed package, `evals` from the repo root. Old imports (`from ingestion…`, `from services…`,
  `from extraction_eval…`) rewritten; notebook 03 uses the S01-02 constructors (`HybridRetriever`, `sparse_model`).
- `build_notebook.py` (the generator of notebook 03) got the same edits and now writes into `evals/notebooks/`.
- `HITLReviewer` default report dir, module docstrings, README and CLAUDE.md point at the new paths.

**Why**
- *Edit source cells in place, not regenerate*: regenerating notebook 03 with `build_notebook.py` would wipe the
  saved outputs (the published RAGAS run). I edited only `source` fields via JSON and checked first that a
  load/save round-trip is byte-identical, so the diff shows only real changes.
- *chdir instead of sys.path*: the notebooks need the repo root as working directory anyway (`data/`, `.env`), and
  Jupyter resolves imports from the working directory, so `import evals` works with no path edits (D10).
- *Reports under `<service>/v1/`*: PLAN.md's `evals/reports/<service>/<stage>/` rule; `v1` marks them as the
  pre-v2 baseline so Stage A reports won't overwrite them.

**Evidence**
- `nbformat.validate` passes for all 3 notebooks (they open).
- Real Jupyter kernels started in `evals/notebooks/` ran the setup + import cells of every notebook: all `ok`
  (01: cells 2–4; 02: cells 2–3; 03: cell 2 + the import lines of cell 4; cells that call Gemini/Cohere or run
  ingestion were not executed). In each kernel `os.getcwd()` = repo root and `telecopilot` resolves to `src/telecopilot`.
- No `experiments` path, `sys.path` edit or old-style import left in the notebooks or eval code (grep).
- `pytest` 25 passed; ruff clean.

**Behaviour change**: none for the app. Eval reports are now written to `evals/reports/...`.

**Found: no `.dockerignore`** — `COPY . .` copies `.env` (API keys), `.git`, `data/ground_truth`, notebooks and
local logs into the image. Fixing it in S01-08 (image size is that ticket's criterion; keeping secrets out of the
image is a hard rule).

### S01-04 — Settings v2 — ✅ done
**What changed** (`config/settings.py`, `.env.example`, `tests/test_settings.py`)
- New: `DATABASE_URL`, `DB_TIMEOUT_S` (5 s), `REDIS_URL`, `REDIS_TIMEOUT_S` (2 s), `CORS_ORIGINS`,
  `LLM_PROVIDER` / `EMBED_PROVIDER` / `RERANK_PROVIDER`, `DATA_RAW_DIR`, `STATIC_DIR`, `QDRANT_TIMEOUT_S`,
  `SCRAPER_TIMEOUT_S`.
- Wired now: Qdrant client timeout, scraper timeout, the three data/static path lookups (`api/main.py`,
  `api/routers/documents.py`, `kb/ingestion_service.py`). DB/Redis settings are used from S01-06/07, CORS in S01-08.

**Why**
- *Providers as `Literal["gemini"]` / `Literal["cohere"]`*: a placeholder that accepts any string would let
  `LLM_PROVIDER=llamacpp` start the app and silently still use Gemini — a hidden fallback. With a `Literal`, an
  unimplemented or misspelled provider fails at startup; M3 widens the `Literal` when it adds the classes.
  Rejected: an `Enum` (more code for the same check) and plain `str` (no validation).
- *Paths relative to the working directory*: the old code looked for `static/` and `data/raw/` next to the source
  file and fell back to the working directory. In an installed package the first guess points into
  site-packages, so the fallback was what actually ran. Making that the only rule removes the guesswork and works
  the same locally (repo root) and in Docker (`/app`).
- *Suffix `_S` on timeouts*: the unit is in the name, so `5` can't be misread as milliseconds.
- *Dev credentials in the default `DATABASE_URL`*: they match the local compose Postgres only (no data, not
  exposed beyond localhost); any real deployment sets `DATABASE_URL` in `.env`. Trade-off noted for the M8
  security pass.

**Evidence**: settings tests (6) run with `_env_file=None` and a cleaned environment, so the developer `.env` can't
mask a wrong default. `/` (static UI), `/api/v1/policies` (all 10 files found) and a raw file download return 200.
`pytest` 31 passed; ruff clean.

**Behaviour change**: none (all defaults equal the old hard-coded values).

### S01-08 (dependency part, pulled forward) — pins, extras, `.dockerignore`
Done before the first image build of the sprint; the rest of S01-08 (CORS, ruff in CI) stays in S01-08.
- **Why pull it forward**: measured before building. Unpinned, the image would have installed **cohere 7, langfuse 5
  and pymupdf 2** (major versions the code was never tested with; pymupdf 2 also pulls `onnxruntime`) and
  downloaded 189 MB. Building now and pinning later would have downloaded most of it twice.
- Direct deps pinned with `==` to the laptop's tested versions. **Python 3.11 support verified** by resolving the full
  runtime and dev+eval sets inside `python:3.11-slim` (Linux, 3.11) with `pip install --dry-run --report`: both
  resolve (a cross-platform dry-run on Windows gives a false `pywin32` conflict, so the check runs on Linux).
- Removed unused `google-genai`, full `langchain` (only `langchain-text-splitters` is imported) and
  `python-multipart` (no forms/uploads). Added the S01-06/07 DB deps now (`sqlalchemy`, `alembic`, `psycopg[binary]`,
  `redis`) so the image is built once this sprint.
- Extras: `dev` (pytest, pytest-asyncio, ruff), `eval` (ragas, langchain-openai/cohere, pandas, matplotlib,
  nbformat, ipykernel, python-dotenv, pyyaml).
- `.dockerignore` keeps `.env`, `.git`, docs, evals, tests and ground truth out of the image.
- Dockerfile: no apt step at all; all 104 runtime packages ship manylinux wheels (checked: 0 source-only packages).
- Trade-off: only **direct** deps are pinned; transitive versions can still move. A full lock file (pip-tools/uv)
  is a proposal for later, not needed at this scale.

### S01-05 — `deploy/compose/` with Postgres + Redis — ✅ done
**What changed**: `deploy/compose/docker-compose.yml` (qdrant, postgres, redis, app) and a root
`docker-compose.yml` with `name: telecopilot-ai` + `include:`. README Docker section updated.

**Why**
- *Same container names, volume and project name for Qdrant*: the existing `telecopilot-ai_qdrant_storage` volume
  (651 chunks) is picked up unchanged, so `docker compose up` behaves as before (no re-ingestion, no API calls).
- *Postgres/Redis bound to `127.0.0.1`*: reachable from the laptop (Alembic, CLI) but not from the network.
- *Healthchecks + `depends_on: service_healthy`*: the app starts only when Postgres and Redis accept connections.
- *API keys via `env_file` at runtime*: with `.dockerignore` the image holds no secrets; `environment:` overrides
  service hosts so a `.env` written for local runs (`localhost`) still works in compose.
- *Host ports as `${X_HOST_PORT:-default}`*: another project on this laptop (`crm_docker`, `restart=always`) holds
  6333/6334. Rather than stopping someone else's containers, our host ports can be moved per run; defaults are
  unchanged. Rejected: hard-coding new ports (changes "as today" for everyone).
- *No Redis volume yet*: Redis holds only short-lived data until M5 (sessions, pub/sub); add persistence with the
  job queue if it needs it.

**Evidence** (run with `QDRANT_HOST_PORT=6343 QDRANT_GRPC_HOST_PORT=6344` because of the port clash)
- `docker compose config` valid; volumes resolve to `telecopilot-ai_qdrant_storage` / `telecopilot-ai_postgres_data`.
- `docker compose up`: postgres + redis healthy; app `/api/health` 200 after 9 s with `live_connection: true`,
  651 chunks, startup ingestion skipped; UI 200; `/api/v1/policies` finds all 10 files.
- Inside the container: no `.env`, `telecopilot` imported from site-packages.

**Images** (uncompressed sizes as reported by Docker)
| Image | Size | Downloaded this sprint |
|---|---|---|
| `qdrant/qdrant:v1.13.0` | 189 MB | no (cached; 77 MB compressed if pulled) |
| `postgres:16-alpine` | 294 MB | no (cached) |
| `redis:7-alpine` | 39 MB | no (cached) |
| `python:3.11-slim` (base) | 125 MB | no (cached) |
| `telecopilot-ai-app` (new) | **709 MB** | 132 MB of wheels (pip) |
| `telecom-agent-assist:latest` (old v1 image, for comparison) | 977 MB | — |

**Found**: before S01-10, `test_sparse_hybrid.py` / `test_dependencies.py` talk to whatever Qdrant listens on
`localhost:6333`. On this laptop that is `crm_docker`'s Qdrant, which now contains a `telecom_customer_policies`
collection with 1 test point. S01-10 makes the tests use in-memory/fake stores; removing that stray collection is
left to Ziad (it is in another project's database).
