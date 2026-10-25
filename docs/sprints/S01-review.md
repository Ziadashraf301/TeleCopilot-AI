# S01 review — M0 Restructure & foundation

Status: **done — awaiting merge.** Review accepted by Ziad with one condition (S01-11 + live smoke test), now met.
Branch `sprint/01-foundation` (not pushed, not merged; Ziad pushes and merges).
v1 behaviour on success paths is unchanged (golden contract tests: same 12 endpoints, same JSON); behaviour changes
only on errors (S01-10) and in start-up (ingestion is a separate job, S01-07). M0 exit criteria: new package layout ✅,
config ✅, Postgres/Redis/Alembic ✅, ingestion as a job ✅, CI ✅ (simulated on 3.11; runs for real on the first PR).

## Done / not done
| Ticket | Status | Evidence (details in the ticket reports below) |
|---|---|---|
| S01-00 Design pack | ✅ approved | `docs/design/M0-foundation.md`, corrections applied (section 11) |
| S01-01 pyproject + `src/telecopilot` | ✅ | `pip install -e .`; `uvicorn telecopilot.api.main:app` serves; no `sys.path` edits left |
| S01-02 group into `api/agent/kb/llm` | ✅ | golden contract tests generated before the refactor and never regenerated (only `/api/ready` added in S01-07); layer test |
| S01-03 `experiments/` → `evals/` | ✅ | `nbformat.validate` ok; setup + import cells of all 3 notebooks run in real kernels |
| S01-04 Settings v2 | ✅ | settings tests run without `.env`; `.env.example` covers every new key |
| S01-05 `deploy/compose/` | ✅ | stack up; `/api/health` live with 651 chunks; no `.env` in the image; image 709 MB (was 977 MB) |
| S01-06 SQLAlchemy + Alembic + `audit_log` | ✅ | `alembic upgrade head` on compose Postgres (host and container); `alembic check` no drift; SQLite tests |
| S01-07 ingestion CLI + `/api/ready` + logger | ✅ | API start-up never ingests (test + real run on an empty collection); `/api/ready` 200 → 503 (Redis stopped) → 200 |
| S01-08 CORS, deps split, pins, ruff in CI | ✅ | CORS tests; CI steps; simulated CI on Python 3.11.17 without `.env`: ruff clean, 48 passed |
| S01-10 remove silent fallbacks | ✅ | Cohere/Qdrant raise; autouse embedded Qdrant in tests; real run with Qdrant down: health 500, ready 503, solve 500 |
| S01-11 FastEmbed `Qdrant/bm25` + re-index + smoke test | ✅ | indices identical across processes (and Windows vs Linux); IDF collection; keyword ranking tests; language choice measured; re-index 653 points; live AR + EN `/solve` correct |
| S01-09 review | ✅ | this file; Status table in `docs/SPRINTS.md` |

**Final state**: `pytest` **66 passed** (also with Hugging Face forced offline and empty caches; sprint start: 16 passed
in 42 s) · `ruff check` clean · `ruff format --check` clean · every commit message starts with its ticket ID · no secrets,
`.env` or local absolute paths committed (checked with grep over the sprint diff).

**Not done / not verified**
- GitHub CI has not run (it runs only on push/PR, which needs Ziad's OK); simulated locally on Python 3.11 instead.
- RAGAS was not re-run with the new BM25 (belongs to M3, S09-01).

## Decisions taken during the sprint
1. **Golden-file contract tests before refactoring** (S01-02): every field of the v1 responses and ingestion
   outputs is pinned, so "behaviour unchanged" is checked, not assumed.
2. **S01-08's dependency work pulled forward** (before S01-05's first build): unpinned, Docker would have installed
   untested major versions (cohere 7, langfuse 5, pymupdf 2 + onnxruntime) and downloaded everything twice.
3. **DB packages added together with the pins** (before S01-06) so the image is built once.
4. **Engine in `db/session.py`, not `core/singletons.py`**: follows the approved layer rule (`core` must not import `db`).
5. **Readiness in `api/`** composing per-layer pings (approved correction); the Qdrant check builds the repository
   inside the check so a down Qdrant is a 503, not a 500.
6. **`127.0.0.1` instead of `localhost`** in the default DB/Redis URLs (2.1 s → 23 ms per new connection on Windows).
7. **Compose host ports overridable** (`QDRANT_HOST_PORT`, …; defaults unchanged) instead of stopping another
   project's containers that hold 6333/6334 on this laptop.
8. **`LOG_DIR` setting** added (the logger had a hard-coded `logs/`).
9. **Notebook source cells edited in place** (outputs kept) rather than regenerating notebook 03.
10. **Secrets only at runtime**: `.dockerignore` keeps `.env` out of the image; compose passes it via `env_file`.
11. **ruff**: `E, F, W, I, B, UP` enforced; E501 off (formatter owns line length), FastAPI `Depends` whitelisted for B008.

## Downloads and sizes
| What | Where | Size |
|---|---|---|
| ruff 0.17.2 (Windows wheel) | laptop | 10.3 MB |
| psycopg 3.3.6 + psycopg-binary (Windows wheels) | laptop | 3.9 MB |
| App image build: 104 pinned runtime wheels (Linux, 3.11) | Docker pip cache | **132 MB** (from the build log; second build 0 MB, 244 cache hits) |
| pytest / pytest-asyncio / ruff for the CI simulation | throwaway container | ~15 MB |
| Package metadata for dry-run resolutions, PyPI HEAD requests, registry manifests | — | a few MB |
| te.eg pages fetched by the S01-01 smoke run (start-up ingestion, before S01-07) | — | < 1 MB |
| Docker images pulled | — | **none** (qdrant v1.13.0, postgres:16-alpine, redis:7-alpine, python:3.11-slim were cached) |
| fastembed 0.9.1 + mmh3 + py-rust-stemmers (laptop; onnxruntime, tokenizers, hf-hub already installed) | laptop | 0.4 MB |
| Same for the image: fastembed, onnxruntime 1.31 (23.8 MB), huggingface-hub, mmh3, py-rust-stemmers, flatbuffers | Docker pip cache | **25.3 MB** |
| `Qdrant/bm25` files (stopword lists; downloaded once on the laptop to inspect, then 3 files vendored, 7 KB) | laptop | 30 KB |
| Model weights | — | none (as required; `Qdrant/bm25` has no weights) |

Image sizes: app **780 MB** after S01-11 (709 MB before fastembed/onnxruntime; old v1 image 977 MB) · qdrant 189 MB · postgres 294 MB · redis 39 MB · base 125 MB.

## Risks found
| # | Risk | Impact | Status |
|---|---|---|---|
| 1 | BM25 indices used Python's per-process `hash()`, no IDF, TF-weighted queries | Sparse half of hybrid search was noise across processes | **fixed in S01-11** (FastEmbed `Qdrant/bm25`, Qdrant IDF, re-indexed) |
| 1b | **v1 RAGAS scores (faithfulness 0.61 etc.) were measured with the broken BM25** | v1 numbers understate hybrid retrieval; not comparable with later runs | re-run in M3 (S09-01) on the new index |
| 1c | Two files named `arabic_*.pdf` (family bundles, router diagnostics) contain **English** text (0% Arabic letters in index and ground truth) while the catalogue lists them as AR with Arabic titles | Arabic coverage is smaller than it looks (only the SLA XML is Arabic); AR/EN eval slices are skewed | M2 (S05-01 source registry: language from content, not file name) |
| 1d | One Gemini OCR call failed with `SSL: CERTIFICATE_VERIFY_FAILED` (self-signed certificate in chain); retry succeeded | Possible TLS interception on the network (antivirus/proxy); ingestion runs can fail randomly | watch; the CLI exit code made it visible |
| 1e | Gemini OCR output is not deterministic (router PDF: 69 chunks before, 61 after re-index) | Index content changes between runs | M2 (S05-01 versioning, S06-03 quality checks) |
| 2 | qdrant-client 1.19 vs server v1.13 (client warns "incompatible") | Subtle API mismatches | open (P4) |
| 3 | Other quiet degradations: Gemini OCR keeps partial pages, chunker/XML parser fallbacks, singletons swallow client-init errors | Content missing from the index without a failure | open (P3) |
| 4 | Any image built **before** this sprint contains `.env` (no `.dockerignore` existed) | API keys inside old local images | rotate keys if such an image was ever pushed/shared; consider deleting old images |
| 5 | Old tests wrote into whatever Qdrant listened on `localhost:6333` (here `crm_docker`'s, now holding a stray `telecom_customer_policies` collection with 1 point) | Pollution of another project's DB | fixed for the future (S01-10); stray collection left for Ziad to delete |
| 6 | Only direct deps are pinned; transitive versions can move | Rare "works on my machine" drift | accepted for now (P6) |
| 7 | Local app import takes ~19 s (8.9 s `langchain_text_splitters` → NLTK/sklearn, installed by the eval extras) | Slow local start/reload; Docker unaffected (~9–17 s to ready) | open (P5) |
| 8 | `/api/health` now returns 500 when Qdrant is down (was 200 + `live_connection: false`) | Monitors that treated health as liveness see failures | intended (S01-10); P7 if a pure liveness probe is wanted |
| 9 | Default `DATABASE_URL` carries local dev credentials | Fine for the local stack only | M8 security pass |

## Proposals (not built)
- ~~P1 — stable BM25 hash~~ → done properly in S01-11 (FastEmbed `Qdrant/bm25` instead of a patched hash).
- **P2 — Re-run RAGAS on the new index in M3** (S09-01), next to the v1 numbers, to see how much BM25 changed.
- **P8 — Arabic normalisation in M2 (S06-02)** for both indexing and queries (alef forms, diacritics, tatweel): the
  Arabic stemmer maps `إلغاء` and hamza-less `الغاء` to different stems; no measurable effect on today's corpus.
- **P3 — Fail-loud extraction in M2 (S06-01 / S06-03)**: per-page OCR failures, chunker fallbacks and the XML fallback
  become counted data-quality records instead of warnings; singletons re-raise client-init errors.
- **P4 — Align Qdrant client and server** in M3 (server image pull ~80 MB, needs Ziad's OK) or pin the client to 1.13.x.
- **P5 — Import only the LangChain splitter modules used** (M2 chunking v2), cutting ~9 s from local start-up.
- **P6 — Lock file** (pip-tools or uv) if transitive drift ever bites; not needed yet.
- **P7 — Optional `/api/live`** (process up, no dependencies) if container liveness probes are added in M8.
- **For S02 planning**: the Reflex desktop needs its origin in `CORS_ORIGINS`; the M1 ERD should decide which actions
  write to `audit_log` and its indexes; add an audit repository class when the first writer appears, not before.

## Local environment notes
- Our compose stack is still running (`telco_qdrant` on host ports 6343/6344 for this run, `telco_postgres`,
  `telco_redis`, `telco_agent_assist` on 8000). `docker compose stop` stops it; the Qdrant/Postgres volumes are kept.
- Before the drop, the old collection was saved as a Qdrant snapshot inside our volume
  (`telecom_customer_policies-3172527913023941-2026-10-25-12-03-19.snapshot`, 7.7 MB); delete it once the merge is final.
- Other projects' containers (`crm_docker`, `real_estate`) start with Docker Desktop (`restart=always`) and hold
  6333/6334; start ours with `QDRANT_HOST_PORT=6343 QDRANT_GRPC_HOST_PORT=6344 docker compose up` while they run.

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

### S01-11 — FastEmbed `Qdrant/bm25` with Qdrant-side IDF; re-index; live smoke test — ✅ done
**What changed**
- `kb/sparse.py` is now a thin wrapper around FastEmbed `SparseTextEmbedding("Qdrant/bm25")`:
  `embed_documents(texts)` (BM25 TF weights, k=1.2, b=0.75) for indexing and `embed_query(text)` (weight 1 per unique
  term) for search. The hand-written model is deleted. Callers: `IngestionService` and `HybridRetriever` (one line each).
- The Qdrant sparse vector is created with `modifier=IDF`, so Qdrant computes IDF from the collection at query time.
- Stopword files vendored in `kb/bm25_model/` (from `Qdrant/bm25`, Apache-2.0, revision `22b8d2af`, attribution in its
  README) and loaded with `specific_model_path`: no Hugging Face download in tests, CI, Docker or at runtime.
- `fastembed==0.9.1` pinned in runtime deps; `bm25_model/*` shipped as package data.
- Collection dropped (after a snapshot) and recreated; full re-index with `python -m telecopilot.kb.ingest --all`.

**Why**
- *Three bugs in the old model*: Python `hash()` is randomised per process (index and queries never matched across
  processes); no IDF at all despite the docstring; queries weighted like documents. FastEmbed uses murmur3 (stable),
  sends TF only, and lets Qdrant apply IDF — the standard Qdrant BM25 setup.
- *IDF in Qdrant, not in Python*: it is computed from the live collection, so it stays correct as documents are added
  or removed, with no statistics to store or rebuild.
- *Vendored stopwords*: 7 KB, licence allows it, and it keeps tests offline (hard rule) and the vectors reproducible
  (a changed upstream stopword list would silently change every sparse vector).
- *Language setting = "bilingual"* (Arabic Snowball stemmer for Arabic-script tokens, English for the rest, both
  stopword lists), chosen by measurement — full method and numbers in `evals/reports/kb/s01/bm25_language_choice.md`:

  | Config | All queries hit@1 / hit@3 (34) | EN hit@1 (19) | Arabic chunk found when `ال` toggled (60) |
  |---|---|---|---|
  | english | 23 / 25 | 17 | **1** |
  | arabic | 23 / 24 | **16** | 8 |
  | **bilingual** | **24 / 25** | 17 | 8 |

  `english` fails on Arabic morphology, `arabic` on English inflections; bilingual matches the better one on every
  slice. Alef normalisation added nothing measurable here → left to M2 (P8). FastEmbed's tokenizer splits words at
  **mid-word** diacritics, but the corpus has none (122 chunks have only word-final diacritics, which are dropped).
- Rejected: patching the old model with a stable hash (still no IDF, still TF-weighted queries, more code to own);
  BGE-M3 sparse (ADR-4: only if an M3 experiment shows it is clearly better and servable).

**Evidence**
- Tests (`test_bm25.py`, `test_sparse_hybrid.py`): document and query indices identical in **two separate processes**
  and in-process (also identical between the laptop and the Linux container); Arabic, English and mixed texts give
  non-empty vectors (queries weight 1.0); stopwords of both languages dropped; per-script stemming; the collection's
  sparse vector has `modifier=idf`; keyword queries rank the right chunk first in the embedded Qdrant (`eSIM`,
  `late fee waiver`, `red LOS light on the router`, the plan name `WE Mix` inside Arabic text, `الباقات العائلية`,
  `تعويض اتفاقية مستوى الخدمة`); hybrid search follows the sparse leg when dense vectors tie.
- Full suite: **66 passed**, also with `HF_HUB_OFFLINE=1` and empty HF/FastEmbed caches. ruff clean.
- Re-index (in the container, Ziad's keys): 14 sources, 13 succeeded on the first run; `arabic_router_diagnostics_scan.pdf`
  failed with `SSL: CERTIFICATE_VERIFY_FAILED` on a Gemini OCR call, so the CLI exited **1** (fail-loud working);
  re-running that file succeeded (61 chunks). Collection: **653 points**, sparse `modifier: idf`. Duration ~10 min + 4 min.

**Live smoke test** (compose stack, real Cohere + Gemini, port 8000)
- `GET /api/ready` → **200** `ready` (qdrant 24 ms, postgres 17 ms, redis 1 ms).
- **English** — "A customer says their phone was stolen an hour ago and they need a replacement SIM today. What should
  I do?" → HTTP 200 in 32.2 s (Gemini 26.6 s); intent `SIM_MANAGEMENT`; first step "Suspend Outgoing (OG) Calls & Data"
  in CRM BSS → Emergency Actions, then identity verification; reply mentions the 50 EGP fee and the VIP waiver.
  Citations: `sim_replacement_policy.html` §2 (stolen-line suspension), §3 (replacement fees), §7. Matches the verified
  reference for eval question Q01 (suspend first, then authenticate).
- **Arabic** — "شركة لديها خط ربط مؤسسي وانخفضت نسبة التشغيل الشهرية إلى 99.2%. ما هو التعويض المستحق…؟" →
  HTTP 200 in 6.5 s; intent `ENTERPRISE_B2B_SUPPORT`; answer in Arabic: the 99.2% band (below 99.5% down to 99.0%) gives
  a **25%** discount on the monthly rental, applied in the next billing cycle. Citations: `arabic_enterprise_sla_contracts.xml`
  (compensation table, contracts table). Matches the verified reference for eval question Q12 exactly.
- The 26.6 s Gemini time on the English call is far above the 4 s p95 target; Gemini latency is measured properly in M4.

**Behaviour change**: sparse vectors and their scores change (that is the fix); the API, JSON shapes and dense
retrieval are unchanged. **v1 RAGAS scores were measured with the broken BM25**; re-running RAGAS belongs to M3.

**Downloads**: laptop 0.4 MB (fastembed, mmh3, py-rust-stemmers) + 30 KB (`Qdrant/bm25` files, once); image +25.3 MB
(onnxruntime 23.8 MB). Measured before installing; image 709 → 780 MB.
