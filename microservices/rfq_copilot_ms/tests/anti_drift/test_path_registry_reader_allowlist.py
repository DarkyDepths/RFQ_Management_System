"""CI guard §11.5.2 — only ExecutionPlanFactory and EscalationGate may
import the Path Registry **config** module.

See ``docs/11-Architecture_Frozen_v2.md`` §11.5.2 / §3.2.

================================================================
The "Path Registry" is two complementary modules — do not conflate.
================================================================

The architecture splits "Path Registry" into a TYPE module and a CONFIG
module. The CI guard restricts only the CONFIG module:

* **Type module — ``src/models/path_registry.py``**
  Defines ``PathId``, ``IntakeSource``, ``IntentConfig``, ``PathConfig``,
  ``TargetPolicy``, etc. (see freeze §14.1, §14.2). These types appear
  in plan model field declarations (``TurnExecutionPlan.path: PathId``),
  stage signatures, the factory protocol, and tests. **Importable from
  anywhere.** Importing a type carries no runtime policy data.

* **Config module — ``src/config/path_registry.py``**
  Holds the runtime ``PATH_CONFIGS: dict[PathId, PathConfig]`` data —
  the actual policy table read at plan-build time. Importing this
  module gives the importer the ability to enforce or bypass policy.
  **Restricted to ``ExecutionPlanFactory`` and ``EscalationGate`` only.**
  This guard fails the build if any other module under ``src/pipeline/``
  imports it. (Slice 1 will populate the config; Batch 0 leaves the
  config slot empty since the v3 stub was deleted.)

The split is the architectural commitment: types travel freely (so
stage signatures stay precise), policy data does not (so policy can
only be enforced at the single chokepoint).

================================================================
Scope of this guard
================================================================

Walks the AST of every ``.py`` file under ``src/pipeline/`` and flags
any ``from src.config.path_registry import ...`` (or
``import src.config.path_registry``) outside the two allowed files:

* ``src/pipeline/execution_plan_factory.py``
* ``src/pipeline/escalation_gate.py``

In Batch 0 nothing imports from ``src.config.path_registry`` (the v3
stub was deleted; the v4 ``PATH_CONFIGS`` lands in Slice 1). The guard
passes trivially today and becomes load-bearing in Slice 1.
"""

from __future__ import annotations

import ast
import importlib
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[2] / "src"
PIPELINE_DIR = SRC_DIR / "pipeline"
ALLOWED = {
    (PIPELINE_DIR / "execution_plan_factory.py").resolve(),
    (PIPELINE_DIR / "escalation_gate.py").resolve(),
}
FORBIDDEN_MODULE = "src.config.path_registry"
TYPES_MODULE = "src.models.path_registry"


def _iter_py_files() -> list[Path]:
    return [p for p in PIPELINE_DIR.rglob("*.py") if p.is_file()]


def _imports_module(path: Path, target: str) -> list[int]:
    """Return line numbers where the file imports the target module."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == target:
            hits.append(node.lineno)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == target:
                    hits.append(node.lineno)
    return hits


def test_only_factory_and_gate_import_registry_config():
    """The config module (runtime policy data) is restricted to the two
    allowed callers. This is the load-bearing CI guard."""
    offenders: list[tuple[str, int]] = []
    for py in _iter_py_files():
        if py.resolve() in ALLOWED:
            continue
        for line in _imports_module(py, FORBIDDEN_MODULE):
            offenders.append((str(py.relative_to(SRC_DIR.parent)), line))

    assert not offenders, (
        f"Only ExecutionPlanFactory and EscalationGate may import "
        f"{FORBIDDEN_MODULE} (the runtime config — runtime policy data). "
        f"Offending sites: {offenders}. "
        f"See docs/11-Architecture_Frozen_v2.md §3.2 / §11.5.2. "
        f"Note: importing types from {TYPES_MODULE} is allowed everywhere."
    )


def test_types_module_is_importable_from_anywhere():
    """Positive contract: the types module is importable without
    triggering the CI guard. This protects against future-us
    accidentally widening the guard to also restrict types — which would
    block plan models, stage signatures, and tests from declaring
    ``PathId`` / ``IntakeSource`` / ``IntentConfig``.

    Importing the types module from this test file (which is NOT in the
    allowlist) must work. If a future PR adds ``src.models.path_registry``
    to the guard's restriction list, this test fails the build.
    """
    module = importlib.import_module(TYPES_MODULE)
    assert module is not None
    # The types module exists and is freely importable. (Its body is a
    # stub in Batch 0; Slice 1 will populate the Pydantic types.)
    assert module.__name__ == TYPES_MODULE


def test_guard_does_not_target_types_module():
    """Belt-and-suspenders: assert the guard's FORBIDDEN_MODULE constant
    points at the config module, not the types module. A typo or paste
    error that swapped them would silently break the architecture by
    blocking type imports while letting policy data leak.
    """
    assert FORBIDDEN_MODULE == "src.config.path_registry", (
        f"CI guard target must be the runtime config module, not the "
        f"types module. Currently restricting: {FORBIDDEN_MODULE}"
    )
    assert TYPES_MODULE == "src.models.path_registry", (
        f"Types module reference drifted: {TYPES_MODULE}"
    )
    assert FORBIDDEN_MODULE != TYPES_MODULE, (
        "Types and config modules must be distinct — see freeze §3.2."
    )
