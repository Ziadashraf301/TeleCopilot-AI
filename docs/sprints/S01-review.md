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
- `pytest`: 16 passed (15 s; was 42 s — the old `conftest`/startup path no longer imports the app twice).
- `ruff check`: all checks passed; `ruff format --check`: 78 files already formatted.
- **Not yet verified**: `docker build` (Docker Desktop not running) — verified in S01-05.

**Behaviour change**: none.
