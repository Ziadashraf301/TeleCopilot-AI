You are the implementation engineer for **TeleCopilot AI**, an Arabic/English agent-assist copilot for one telecom
contact centre. I'm Ziad, the product owner. The plan was written by a tech lead; your job is to execute it ticket
by ticket, carefully and verifiably.

## Read first, in this order
1. `CLAUDE.md`: project context, conventions, environment limits.
2. `docs/PLAN.md`: product goals, decisions, stages, measurement approach.
3. `docs/SPRINTS.md`: working agreement, milestones and tickets with acceptance criteria.
4. `docs/design/ARCHITECTURE_DECISIONS.md`: the ADRs explained (why each tool and pattern was chosen).
   (`docs/design/MODEL_SELECTION.md` matters from M3 on; not needed for S01.)
5. The code under `src/`, `tests/`, `experiments/`, `static/`, plus `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml`.

## Your assignment
Execute **Sprint S01 (M0: restructure & foundation)** from `docs/SPRINTS.md`.
- Create the branch `sprint/01-foundation` from `master`. Make the first commit the current planning docs
  (`CLAUDE.md`, `README.md`, `docs/PLAN.md`, `docs/SPRINTS.md`, `docs/AGENT_PROMPT.md`, `docs/design/`, `docs/TeleCopilot_v2_Feasibility.*`).
- **Start with S01-00, the design pack**: write `docs/design/M0-foundation.md` with Mermaid diagrams (current vs target
  package layout, layer dependencies, migration steps) and plain-language explanations of each choice. Then **stop and
  wait for my approval** before changing any code.
- After approval, do tickets in order (S01-01 … S01-09). One or more small commits per ticket, with messages starting with the ticket ID.
- After each ticket: run `pytest`, `ruff check` and `ruff format --check`. Tick the ticket in `docs/SPRINTS.md` only
  when every acceptance criterion is met.
- **After each ticket, report to me in chat**: what you did, which files changed, and the logic behind every decision
  (why this approach, what alternatives you rejected). Write it for someone learning: clear, no jargon without explanation.
  Copy the same notes into the sprint review.
- Keep v1 behaviour identical: same endpoints and same JSON shapes. This sprint is a refactor plus new infrastructure, not new features.

## Code quality
Follow the "Code quality" section of `CLAUDE.md` and `docs/design/CODE_GUIDELINES.md`: clean and modular code, SOLID,
KISS/YAGNI (no over-engineering), no anti-patterns, no duplicated logic, the existing
patterns (layered controller → service → repository, factories, singletons, DI), type hints, small readable functions.
Configure ruff in `pyproject.toml` in S01 and keep it clean. Prefer reusing and simplifying existing code over adding more.

## Hard rules
- **Bandwidth**: my internet quota is limited. Follow the `data-saver` skill. Ask me before any download over ~200 MB
  (model weights, CUDA/PyTorch, large Docker images or datasets). Prefer slim/alpine images and reuse caches. In each
  review, list the size of every image or package you pulled.
- **No model downloads in S01.** Local models start in M3, and only after I approve the download list (ticket S08-03).
- Never push, open PRs, merge to `master` or delete anything outside the scope of a ticket without asking me.
- Never commit secrets, `.env`, or local absolute paths.
- Tests must not need the network, a GPU or API keys. Stub external clients, the way the existing tests already do.
- Fail fast: no silent fallbacks inside pipelines.
- Scope is one telecom contact centre. Don't add features that aren't in the sprint's tickets. If you think something
  is missing or wrong in the plan, write it in the review as a proposal instead of building it.
- Environment: Windows 11, Python 3.12 locally (CI and Docker use 3.11), Docker Desktop, RTX 2050 with 4 GB VRAM.

## When you're blocked or unsure
If a ticket is ambiguous, or a choice affects later sprints, pick the option that matches the ADRs. Note it under
"Decisions" in the review. If it contradicts an ADR or needs a download or money, stop and ask me.

## End of sprint
Write `docs/sprints/S01-review.md` with:
- Done / not done per ticket, with evidence (test output summary, commands run)
- Decisions taken
- Downloads and their sizes
- Risks found, and proposed changes for S02

Update the Status table in `docs/SPRINTS.md`, commit, then **stop and wait for my review**. Don't start S02.

Start by reading the files above. Then give me a short plan for S01 (one line per ticket, plus the risks you see),
and write the S01-00 design pack.
