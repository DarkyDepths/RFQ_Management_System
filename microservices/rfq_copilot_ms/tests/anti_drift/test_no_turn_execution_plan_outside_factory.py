"""CI guard §11.5.1 — only ExecutionPlanFactory may construct TurnExecutionPlan.

See ``docs/11-Architecture_Frozen_v2.md`` §11.5.1.

Walks the AST of every ``.py`` file under ``src/`` and flags any
``ast.Call`` node whose callee is the bare name ``TurnExecutionPlan``,
unless the file is the single allowed factory module
(``src/pipeline/execution_plan_factory.py``).

The class **definition** in ``src/models/execution_plan.py``
(``class TurnExecutionPlan(BaseModel):``) is not an ``ast.Call``, so it
is not flagged.

In Batch 0 there are no instantiations anywhere yet — the test is
expected to pass trivially. The guard becomes load-bearing in Slice 1
when the factory is implemented.
"""

from __future__ import annotations

import ast
from pathlib import Path


SRC = Path(__file__).resolve().parents[2] / "src"
ALLOWED = (SRC / "pipeline" / "execution_plan_factory.py").resolve()
TARGET_NAME = "TurnExecutionPlan"


def _iter_py_files() -> list[Path]:
    return [p for p in SRC.rglob("*.py") if p.is_file()]


def _find_calls(path: Path) -> list[int]:
    """Return line numbers of `TurnExecutionPlan(...)` call sites in this file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == TARGET_NAME:
                hits.append(node.lineno)
            elif isinstance(func, ast.Attribute) and func.attr == TARGET_NAME:
                # e.g. some_module.TurnExecutionPlan(...) — also forbidden
                hits.append(node.lineno)
    return hits


def test_only_factory_constructs_turn_execution_plan():
    offenders: list[tuple[str, int]] = []
    for py in _iter_py_files():
        if py.resolve() == ALLOWED:
            continue
        for line in _find_calls(py):
            offenders.append((str(py.relative_to(SRC.parent)), line))

    assert not offenders, (
        f"Only ExecutionPlanFactory may construct {TARGET_NAME}. "
        f"Offending sites: {offenders}. "
        f"See docs/11-Architecture_Frozen_v2.md §2.7 / §11.5.1."
    )
