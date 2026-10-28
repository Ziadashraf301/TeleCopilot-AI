"""Readiness: can this instance serve traffic? Composes the small ping each layer exposes."""

import time
from collections.abc import Callable

from telecopilot.core.logger import get_logger

logger = get_logger()

# A check returns normally when the dependency is reachable and raises otherwise.
ReadinessCheck = Callable[[], object]


def run_check(name: str, check: ReadinessCheck) -> dict:
    start = time.perf_counter()
    try:
        check()
    except Exception as e:  # any failure means "not ready"; it is reported, not hidden
        logger.warning(f"Readiness check '{name}' failed: {e}")
        return {"ok": False, "latency_ms": _elapsed_ms(start), "error": f"{type(e).__name__}: {e}"}
    return {"ok": True, "latency_ms": _elapsed_ms(start)}


def check_readiness(checks: dict[str, ReadinessCheck]) -> tuple[bool, dict]:
    """Run every check; ready only if all pass. Returns (ready, response body)."""
    results = {name: run_check(name, check) for name, check in checks.items()}
    ready = all(result["ok"] for result in results.values())
    return ready, {"status": "ready" if ready else "not_ready", "checks": results}


def _elapsed_ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)
