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

### S01-06 — SQLAlchemy 2 + Alembic + `audit_log` — ✅ done
**What changed**: `db/base.py`, `db/session.py`, `audit/models.py`, `alembic.ini`, `migrations/` (env, template,
`0001_create_audit_log.py`), `tests/test_db.py`; layer rules gained `db → config`, `audit → db`, `api → db`.

**Why**
- *Engine in `db/session.py` (cached with `lru_cache`), not in `core/singletons.py`*: CLAUDE.md puts clients in
  `core/singletons.py`, but the approved layer rule says `core` must not import `db` and `db` depends only on
  `config`. A cached factory gives the same "one pool per process" guarantee inside the layer that owns it.
- *Sync SQLAlchemy*: matches every existing service; FastAPI runs sync dependencies in a thread pool; 20–100 CSRs
  is far below any limit. Async only if a Locust run shows a need (design D-section 5).
- *`pool_pre_ping`*: a connection Postgres closed (restart, idle timeout) is replaced instead of failing a request.
- *Naming convention on `Base.metadata`*: constraint names (`pk_audit_log`) are deterministic, so later migrations
  can alter/drop them by name on every machine.
- *Type variants* (`BigInteger`→`Integer` on SQLite, `JSON`→`JSONB` on Postgres): one model works for production
  Postgres and for SQLite in CI. The migration uses `sa.func.now()` (autogenerate wrote a Postgres-only literal
  `now()`, which SQLite rejects).
- *URL from settings in `env.py`*: no credentials in `alembic.ini`; I also dropped Alembic's default
  `prepend_sys_path = .` (a `sys.path` edit; not needed with the installed package) and set
  `disable_existing_loggers=False` so running migrations in a process doesn't silence its loggers.
- *No indexes or audit writes yet*: which actions are audited and how they are queried is part of the M1 ERD.
- Rejected: `Base.metadata.create_all()` at startup — it can't change existing tables; migrations can.

**Evidence**
- `alembic upgrade head` on the compose Postgres: `Running upgrade -> 0001`; `alembic current` = `0001 (head)`;
  `\d audit_log` shows `bigint` identity, `timestamptz default now()`, `jsonb`, `pk_audit_log`.
- `alembic check`: "No new upgrade operations detected" (models and migrations agree).
- Tests on SQLite (4): upgrade + downgrade, `command.check`, round trip with Arabic JSON and DB-filled
  `occurred_at`, uncommitted work rolled back when the request's session closes. `pytest` 35 passed; ruff clean.

**Behaviour change**: none (nothing writes to Postgres yet).

### S01-07 — ingestion CLI, `/api/ready`, logger clean-up — ✅ done
**What changed** (3 commits)
1. *Logger*: `configure_logging()` installs the console / JSON Lines / rolling-file sinks; importing
   `core/logger.py` changes nothing. Called by the API lifespan and the CLI. Logs folder = new `LOG_DIR` setting.
2. *Ingestion CLI* `python -m telecopilot.kb.ingest --all` (`kb/ingest.py`); the API lifespan only configures logging.
3. *Readiness*: `ping()` on `BaseVectorRepository` (Qdrant asks the server), `db.session.ping()` (`SELECT 1`), a Redis
   client singleton in `core/singletons.py`; `api/readiness.py` composes them; `GET /api/ready` → 200 / 503.
   Default `DATABASE_URL` / `REDIS_URL` now use `127.0.0.1`.

**Why**
- *CLI exit code 1 if any source fails*: the old start-up hook logged ingestion errors as a warning and served
  anyway. A script or CI job can now see a partial index. Re-runs are safe (point id = `uuid5(chunk_id)`).
- *The CLI builds its own `IngestionService`*: reusing `api/dependencies.py` would be a `kb → api` import. Two entry
  points (API, CLI) each wiring their objects is normal; the duplication is one line.
- *Readiness lives in `api/`* (approved correction): only the API layer knows all three dependencies; each layer
  exposes just a ping. A failing check is **reported** (`ok: false`, error text, HTTP 503), not hidden — the one
  place where catching any exception is the point.
- *`/api/ready` is a sync route*: the pings block; FastAPI runs sync routes in a thread pool, so the event loop
  isn't stalled.
- *`127.0.0.1` defaults*: compose binds Postgres/Redis to IPv4 only and Windows resolves `localhost` to IPv6 first.
  Measured: a new Redis connection took **2,126 ms via `localhost` vs 23 ms via `127.0.0.1`**.
- *`LOG_DIR` setting*: replaces a hard-coded path; the folder is created once, not on every JSON log line.
- Rejected: keeping start-up ingestion behind a flag (a speculative option, and the failure mode stays hidden).

**Evidence**
- Tests: logger (no side effects at import, checked in a fresh process in an empty folder; JSON + text sinks),
  CLI (exit 0 / 1, `--all` required, wiring), API start-up fails the test if ingestion is called, readiness
  (200 all up; 503 for each of qdrant / postgres / redis down, with the error). Golden OpenAPI: the **only**
  difference is the added `/api/ready` path (all existing paths and schemas identical). `pytest` 46 passed; ruff clean.
- Real stack, API on the host against an **empty** collection: no ingestion lines in the log, `indexed_chunks_count: 0`;
  `/api/ready` 200 → `docker compose stop redis` → **503** `redis: TimeoutError` (Qdrant/Postgres ok) → start → 200.
- In compose after rebuild (0 wheels downloaded, 244 cache hits; image still 709 MB): `/api/ready` 200 in 17 s from
  `up`, all checks < 10 ms; `docker compose run --rm app alembic current` → `0001 (head)`; the CLI is in the image
  (`--help`; exit 2 without `--all`). A real `--all` run was **not** done (it calls Gemini OCR + Cohere with live
  keys; the 651 chunks are already indexed).

**Behaviour change**: the API no longer indexes on start-up; run the CLI once on an empty Qdrant. `/api/ready` is new.

**Found**
- *Start-up is now import-bound*: importing the app takes ~19 s on the laptop; 8.9 s of it is
  `langchain_text_splitters`, whose `__init__` imports every splitter incl. NLTK/sklearn ones (installed locally by
  the eval extras; not in the Docker image, where the app is up in ~9–17 s). Proposal (M2, chunking v2): import only
  the splitter modules used.
- *Race → silent in-memory mode*: two first requests at once built two `QdrantVectorRepository` instances; both tried
  to create the collection, the second got `409 Conflict`, and its `except` switched it to in-memory mode — and that
  instance was cached (`live_connection: false` while Qdrant was up). S01-10 removes the fallback; collection
  creation should also treat "already exists" as success.
- *Client/server mismatch*: `qdrant-client 1.19.0` warns it is incompatible with server `v1.13.0` (pre-existing:
  the laptop had 1.19 before this sprint). Proposal: move the server to a matching version when M3 touches
  retrieval (one image pull, ~80 MB, needs Ziad's OK), or pin the client to 1.13.x.

### S01-08 — CORS, requirements split, pins, ruff in CI — ✅ done
The dependency half (pins, extras, unused deps removed, `.dockerignore`, no apt step) was done before the first
build — see "S01-08 (dependency part, pulled forward)" above. This part:
- `CORSMiddleware(allow_origins=settings.CORS_ORIGINS)` instead of `"*"`. **Why**: `*` with
  `allow_credentials=True` lets any website a CSR visits call the API from the CSR's browser. The v1 UI is served by
  the same app (same origin) and needs no entry; the Reflex app (M1) adds its origin in `.env`.
- CI: `ruff check .` and `ruff format --check .` before pytest; `setup-python` pip cache keyed on `pyproject.toml`
  (its default key is `requirements*.txt`, which no longer exists, so the cache step would fail).

**Evidence**
- `tests/test_cors.py`: preflight from the configured origin → 200 with `access-control-allow-origin`; from another
  origin → 400 without it.
- **CI simulated on Python 3.11** (CI itself only runs on push/PR to master, which needs Ziad's OK): in the app image
  (Python 3.11.17, Linux) with the repo copied in **without `.env`** and no Qdrant reachable: `ruff check` passed,
  `ruff format --check` 98 files formatted, `pytest` **48 passed**. Downloads: pytest, pytest-asyncio, ruff into the
  throwaway container (~15 MB).
- Image: **709 MB vs 977 MB** before (criterion "not larger than before" met).

**Behaviour change**: cross-origin browser requests from origins not in `CORS_ORIGINS` are now refused.

### S01-10 — remove silent fallbacks — ✅ done
**What changed**
- `llm/cohere.py`: raises at construction without `COHERE_API_KEY` (same as `GeminiService`); embed/rerank errors
  propagate. Deleted the hash-based pseudo-embeddings and the fake `1.0 - 0.1·i` rerank scores.
- `kb/repositories/qdrant.py`: no in-memory store, no `_is_live`, no `except` around Qdrant calls; construction and
  every call raise when Qdrant is unreachable. `initialize_collection` uses `collection_exists` and treats a
  concurrent `409 Conflict` as success (the race found in S01-07); other errors propagate. Removed an
  old-client `FusionQuery` shim (client is pinned) and named the prefetch factor.
- `/api/health` keeps its JSON shape; `live_connection` is `true` whenever it answers. The readiness check builds the
  repository *inside* the check so a down Qdrant yields 503, not 500.
- Log messages that promised a fallback ("Fallback mode will be active") corrected.
- Tests: an **autouse embedded Qdrant** (`QdrantClient(":memory:")`) per test in `conftest.py`, so no test can reach
  or write into a real server; Cohere fail-fast tests (missing key, embed error, rerank error, 96-text batching);
  unreachable Qdrant raises; 409 race tolerated; other creation errors propagate.

**Why**
- *Pseudo-embeddings* would be **written into Qdrant** by the standalone ingestion job and look like real vectors;
  the S01-01 smoke run already "indexed" 502 chunks that way. *Fake rerank scores* reorder results arbitrarily
  while looking like model output.
- *In-memory mode* made a down database report `HEALTHY` and answered `/solve` with keyword overlap; worse, it was
  cached in the DI singleton, so the instance never recovered when Qdrant came back. Now a failed construction is not
  cached (`lru_cache` doesn't cache exceptions), so the next request reconnects.
- *Fakes/embedded Qdrant in tests* instead of the fallbacks: tests check our behaviour against a real Qdrant engine
  (in-process), not against a mock-mode code path that production never should run.

**Evidence**
- `pytest` **56 passed in ~9 s** (sprint baseline: 16 passed in 42 s); ruff clean. v1 contract (golden) tests
  unchanged → success paths identical.
- Real run, Qdrant down (port 9), keys blank: `/api/health` **500**, `/api/ready` **503** `qdrant: timed out`
  (postgres/redis ok), `/api/agent-assist/solve` **500**, UI 200.

**Behaviour change (errors only)**
| Situation | Before | After |
|---|---|---|
| Qdrant unreachable | `/api/health` 200 `live_connection: false`; search served from an in-memory keyword list | `/api/health` 500, `/api/ready` 503, `/solve` 500 |
| Cohere error / no key during ingestion | hash pseudo-vectors upserted into Qdrant | ingestion of that source fails (`FAILED`, CLI exit 1) |
| Cohere error during `/solve` | fake rerank order, answer generated anyway | HTTP 500 |
| Concurrent first requests creating the collection | second instance silently in-memory, cached | both succeed |

**Found (not fixed; proposals)**: other broad `except` blocks that degrade quietly — `GeminiOCRExtractor` keeps a
partial document when a page's OCR call fails (pages can go missing from the index), the HTML/Markdown chunkers fall
back to other splitters, the XML extractor falls back to BeautifulSoup, and `core/singletons.py` swallows client
initialisation errors (the service then raises "not initialised" and the original cause is only in the log).
Langfuse/tracing warnings are intentional (tracing must not break a request).
