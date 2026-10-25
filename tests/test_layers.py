"""Layer rule from docs/design/M0-foundation.md section 3: imports between telecopilot packages point downwards only."""

import ast
from pathlib import Path

PACKAGE_ROOT = Path(__file__).parents[1] / "src" / "telecopilot"

# package -> packages it may import (besides itself). `config` is the bottom layer, importable from everywhere.
ALLOWED_IMPORTS: dict[str, set[str]] = {
    "api": {"agent", "kb", "llm", "core", "config"},
    "agent": {"kb", "llm", "core", "config"},
    "kb": {"llm", "core", "config"},
    "llm": {"core", "config"},
    "core": {"config"},
    "config": set(),
}


def imported_packages(source_file: Path) -> set[str]:
    """Top-level telecopilot sub-packages imported anywhere in the file (including inside functions)."""
    packages = set()
    for node in ast.walk(ast.parse(source_file.read_text(encoding="utf-8"))):
        names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else []
        if isinstance(node, ast.ImportFrom) and node.module:
            names = [node.module]
        packages.update(name.split(".")[1] for name in names if name.startswith("telecopilot."))
    return packages


def test_every_package_has_a_layer_rule():
    packages = {p.name for p in PACKAGE_ROOT.iterdir() if (p / "__init__.py").exists()}
    assert packages == set(ALLOWED_IMPORTS)


def test_imports_point_downwards_only():
    violations = []
    for source_file in PACKAGE_ROOT.rglob("*.py"):
        relative = source_file.relative_to(PACKAGE_ROOT)
        if len(relative.parts) == 1:
            continue  # telecopilot/__init__.py belongs to no layer
        package = relative.parts[0]
        for imported in imported_packages(source_file) - {package} - ALLOWED_IMPORTS[package]:
            violations.append(f"{relative.as_posix()}: {package} -> {imported}")
    assert not violations, "Wrong-way imports:\n" + "\n".join(violations)
