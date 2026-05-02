"""CI guard §11.5.2 — only ExecutionPlanFactory and EscalationGate may
import the Path Registry config module.

See ``docs/11-Architecture_Frozen_v2.md`` §11.5.2 / §3.2.

Walks the AST of every ``.py`` file under ``src/pipeline/`` and flags
any ``from src.config.path_registry import ...`` (or
``import src.config.path_registry``) outside the two allowed files:

* ``src/pipeline/execution_plan_factory.py``
* ``src/pipeline/escalation_gate.py``

Type-only imports from ``src/models/path_registry.py`` (the type
contract module) are fine and outside this guard's scope — that module
defines types like ``PathId``, ``IntakeSource``, ``IntentConfig``, which
are widely used and don't carry runtime policy data.

In Batch 0 nothing imports from ``src.config.path_registry`` (it's a
stub that doesn't exist yet — Slice 1 creates it). The guard passes
trivially and becomes load-bearing in Slice 1.
"""

from __future__ import annotations

import ast
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[2] / "src" / "pipeline"
ALLOWED = {
    (PIPELINE_DIR / "execution_plan_factory.py").resolve(),
    (PIPELINE_DIR / "escalation_gate.py").resolve(),
}
FORBIDDEN_MODULE = "src.config.path_registry"


def _iter_py_files() -> list[Path]:
    return [p for p in PIPELINE_DIR.rglob("*.py") if p.is_file()]


def _imports_forbidden(path: Path) -> list[int]:
    """Return line numbers where the file imports the forbidden module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == FORBIDDEN_MODULE:
            hits.append(node.lineno)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == FORBIDDEN_MODULE:
                    hits.append(node.lineno)
    return hits


def test_only_factory_and_gate_import_registry():
    offenders: list[tuple[str, int]] = []
    for py in _iter_py_files():
        if py.resolve() in ALLOWED:
            continue
        for line in _imports_forbidden(py):
            offenders.append((str(py.relative_to(PIPELINE_DIR.parent.parent)), line))

    assert not offenders, (
        f"Only ExecutionPlanFactory and EscalationGate may import "
        f"{FORBIDDEN_MODULE}. Offending sites: {offenders}. "
        f"See docs/11-Architecture_Frozen_v2.md §3.2 / §11.5.2."
    )
