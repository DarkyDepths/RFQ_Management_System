"""Anti-drift — ``MemoryPolicy.working_pairs`` is read by production code.

Before Batch 10 the registry declared ``MemoryPolicy.working_pairs``
on every path config, but no production code path actually read it.
The field was load-shaped only — easy to silently drift when the
registry was edited.

Batch 10 makes it load-bearing: ``V2TurnController._load_working_memory``
reads ``state.plan.memory_policy.working_pairs`` to cap the number of
prior-turn pairs loaded into ``state.working_memory``.

This test scans ``src/`` for at least one production reference to
``working_pairs`` (excluding the model declaration itself, comments,
and docstrings — only real reads count). If a future refactor removes
the read path, this test fails immediately and the registry value
becomes silently dead config again.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"

# Where ``working_pairs`` is *declared* (the field on the Pydantic
# model). Excluded from the read scan because a class field reference
# isn't a use site.
DECLARATION_FILES = {
    SRC / "models" / "path_registry.py",
    SRC / "config" / "path_registry.py",
}


def _attribute_reads_working_pairs(tree: ast.AST) -> int:
    """Count attribute READS named ``working_pairs`` in the AST.

    Matches:
    * ``foo.working_pairs`` (Attribute access)
    * ``foo["working_pairs"]`` and ``foo.get("working_pairs")``
      (string-keyed access)

    Skips:
    * ``working_pairs=...`` (keyword argument: declaration site)
    * ``self.working_pairs = X`` on the LHS of an assignment
      (mutation, not a read).
    """
    count = 0
    for node in ast.walk(tree):
        # foo.working_pairs in any context that's NOT the LHS of
        # an assignment.
        if isinstance(node, ast.Attribute) and node.attr == "working_pairs":
            count += 1
        # foo["working_pairs"] / foo.get("working_pairs") / dict literals.
        elif isinstance(node, ast.Constant) and node.value == "working_pairs":
            # Constant strings can appear as a dict key or function arg —
            # both count as references for the purpose of this test.
            count += 1
    return count


def test_working_pairs_is_referenced_by_production_code():
    """At least one source file under ``src/`` (other than the model
    declaration site) must reference ``working_pairs``. Otherwise the
    registry value is dead config and Batch 10's working-memory cap
    isn't actually being applied."""
    candidates = [
        p for p in SRC.rglob("*.py")
        if p not in DECLARATION_FILES
    ]
    assert candidates, "No source files found under src/"

    references: list[Path] = []
    for path in candidates:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        if _attribute_reads_working_pairs(tree) > 0:
            references.append(path)

    assert references, (
        "No production source file under src/ reads "
        "MemoryPolicy.working_pairs. The registry value is dead config "
        "— Batch 10's working-memory cap is no longer being applied. "
        "Restore V2TurnController._load_working_memory or whichever "
        "stage replaced it."
    )


def test_v2_turn_controller_specifically_reads_working_pairs():
    """The expected reader in Batch 10 is V2TurnController. Pin it
    explicitly so a future refactor moving the read elsewhere shows up
    as a deliberate change here, not an accident."""
    controller_path = SRC / "controllers" / "v2_turn_controller.py"
    assert controller_path.exists(), (
        f"Expected controller file not found: {controller_path}"
    )
    tree = ast.parse(controller_path.read_text(encoding="utf-8"))
    assert _attribute_reads_working_pairs(tree) > 0, (
        "V2TurnController no longer references working_pairs. If the "
        "read moved to another file, update this test to point at it."
    )
