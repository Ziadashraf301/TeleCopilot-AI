# Code Guidelines

The rules every ticket follows, each explained in plain language. The short version is in `CLAUDE.md`.

## Principles to follow
| Principle | Meaning | In this project |
|---|---|---|
| **KISS** (Keep It Simple) | Choose the simplest solution that works | A function before a class; a class before a framework |
| **YAGNI** (You Aren't Gonna Need It) | Build only what the current ticket needs, not what *might* be needed later | No "future-proof" options or plugins nobody asked for |
| **DRY** (Don't Repeat Yourself) | One piece of logic lives in one place | Shared helpers instead of copy-paste; reuse existing utilities |
| **SOLID: S**ingle responsibility | Each module/class has one reason to change | Extractor extracts, chunker chunks, repository stores |
| **SOLID: O**pen/closed | Add behaviour by adding code, not editing working code | New file format = new extractor registered in the factory |
| **SOLID: L**iskov substitution | Any implementation can replace another behind the same interface | llama.cpp, vLLM and Gemini providers are interchangeable |
| **SOLID: I**nterface segregation | Small, focused interfaces | `Embedder` and `Reranker` are separate, not one giant "AIService" |
| **SOLID: D**ependency inversion | High-level code depends on interfaces, not concrete classes | The agent asks for an `LLMProvider`, injected via FastAPI DI |
| **Clean code** | Readable names, small functions, comments explain *why* | Someone new understands a function without running it |

## Avoid over-engineering
Over-engineering = making code more complex than the problem needs. It costs time, hides bugs and makes changes harder.
Signs to avoid:
- An interface or abstract class with **only one implementation** and no planned second one. (Providers are fine: we
  have 2–3 real implementations.)
- Layers that only pass calls through (a "manager" that calls a "handler" that calls a "service" that does the work).
- Generic frameworks, plugin systems or config options for cases that don't exist yet.
- Design patterns used because they are patterns, not because they solve a problem here.
- Premature optimisation (caching, async, parallelism) before a measurement shows a need.
- Rule of thumb: **the third time** you need the same thing, generalise it. Before that, keep it simple.

## Anti-patterns to avoid
An anti-pattern is a common solution that looks reasonable but causes problems later.

| Anti-pattern | What it is | Why it hurts | Do instead |
|---|---|---|---|
| **God class / God module** | One class that does everything | Impossible to test or change safely | Split by responsibility |
| **Copy-paste programming** | Same logic duplicated | Fix a bug in one copy, the others stay broken | Extract a function |
| **Magic numbers / strings** | Unexplained values in code (`0.35`, `"gemini-..."`) | Nobody knows why; values drift | Named constants or settings |
| **Hard-coded config / secrets** | URLs, keys, paths in code | Breaks across environments; leaks secrets | `settings.py` + `.env` |
| **Swallowing exceptions** | `except Exception: pass` or silent fallbacks | Bugs hide; wrong answers look right | Fail fast, log with context, or handle a *specific* error |
| **Circular imports / wrong-way dependencies** | Lower layer importing an upper one | Tangled, fragile code | Dependencies point downwards only |
| **Global mutable state** | Module-level variables changed at runtime | Hidden coupling, flaky tests | Pass dependencies in (DI); singletons only for clients |
| **Business logic in controllers or UI** | Rules inside FastAPI routes or Reflex pages | Can't reuse or test the logic | Routes/pages call services |
| **Anemic tests / testing implementation details** | Tests that only check mocks were called | Pass while behaviour is broken | Test behaviour and outputs |
| **Leaky abstraction** | Callers need to know Qdrant/Gemini details behind an interface | Swapping providers breaks callers | Keep vendor specifics inside the implementation |
| **Primitive obsession** | Passing loose dicts/strings everywhere | Typos, unclear shapes | Pydantic models / dataclasses with types |
| **Dead code / commented-out code** | Unused functions, old blocks kept "just in case" | Noise and confusion | Delete it; git keeps history |
| **Long parameter lists / boolean flags** | `f(a, b, c, d, e, True, False)` | Hard to read and call correctly | Group into a model; split the function |

## Checks
- `ruff check` + `ruff format` (style, unused code, common bugs).
- Code review in each ticket report: the agent states how the change respects these rules and lists any trade-off.
