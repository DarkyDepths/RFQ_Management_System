"""CI guard #6 — FastIntake patterns must use anchored full-match only.

Per Batch 0 acceptance criteria:

* FastIntake patterns must use anchored full-match behavior only
  (``re.fullmatch`` or equivalent — anchored ``^...$``).
* No fuzzy matching, substring matching, DB calls, network calls,
  or LLM calls.

In Batch 0 the pattern table is empty; this test asserts the
**structural promise** holds:

1. ``src/pipeline/fast_intake_patterns.py`` exists and exports
   ``FAST_INTAKE_PATTERNS`` and ``PATTERN_VERSION``.
2. The patterns module source contains no obvious anti-patterns
   (``re.search``, ``re.match`` without anchors, ``in user_message``
   substring tests, ``import requests`` / ``import httpx``,
   ``import openai`` etc.).
3. ``src/pipeline/fast_intake.py`` has no LLM SDK imports and no DB
   imports. (LLM SDK check is also covered by §11.3 test.)

When Slice 1 populates the pattern table, this test will be extended to
assert each entry's regex starts with ``^`` and ends with ``$``, or is
matched via ``re.fullmatch``.
"""

from __future__ import annotations

import ast
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[2] / "src" / "pipeline"
PATTERNS_FILE = PIPELINE_DIR / "fast_intake_patterns.py"
INTAKE_FILE = PIPELINE_DIR / "fast_intake.py"


def test_patterns_module_exports_required_symbols():
    """Module must exist and expose FAST_INTAKE_PATTERNS + PATTERN_VERSION."""
    assert PATTERNS_FILE.exists(), "fast_intake_patterns.py must exist"
    src = PATTERNS_FILE.read_text(encoding="utf-8")
    assert "FAST_INTAKE_PATTERNS" in src, "FAST_INTAKE_PATTERNS export missing"
    assert "PATTERN_VERSION" in src, "PATTERN_VERSION export missing"


def test_patterns_module_has_no_forbidden_imports():
    """Pattern table must not pull in network, DB, or LLM SDKs."""
    forbidden_modules = {
        "openai",
        "anthropic",
        "langchain",
        "requests",
        "httpx",
        "sqlalchemy",
        "psycopg2",
    }
    tree = ast.parse(PATTERNS_FILE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    leaked = imported & forbidden_modules
    assert not leaked, f"fast_intake_patterns.py imports forbidden modules: {leaked}"


def test_intake_module_has_no_forbidden_imports():
    """FastIntake stage must not pull in network, DB, or LLM SDKs."""
    forbidden_modules = {
        "openai",
        "anthropic",
        "langchain",
        "requests",
        "httpx",
        "sqlalchemy",
        "psycopg2",
    }
    tree = ast.parse(INTAKE_FILE.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    leaked = imported & forbidden_modules
    assert not leaked, f"fast_intake.py imports forbidden modules: {leaked}"


def test_anchored_full_match_promise_in_docstring():
    """The patterns module docstring must promise anchored full-match
    semantics (so future-us doesn't quietly switch to ``re.search``).
    """
    src = PATTERNS_FILE.read_text(encoding="utf-8")
    assert "anchored full-match" in src.lower(), (
        "fast_intake_patterns.py docstring must explicitly promise "
        "anchored full-match semantics."
    )


def test_no_substring_match_idiom_in_intake():
    """The intake stage source must not contain raw substring tests
    against the user message (a classic 'shortcut' that drifts from
    anchored semantics).

    In Batch 0 the file is a stub; this test stays meaningful as Slice 1
    fills in the body.
    """
    src = INTAKE_FILE.read_text(encoding="utf-8")
    # If patterns are matched at all, prefer re.fullmatch. Forbid the
    # easy-to-misuse `in user_message` substring idiom.
    assert " in user_message" not in src, (
        "fast_intake.py must not use `something in user_message` substring "
        "matching. Use re.fullmatch on anchored patterns instead."
    )
    assert "re.match(" not in src, (
        "fast_intake.py must not use re.match() (it only anchors at the "
        "start, not the end). Use re.fullmatch() instead."
    )
    assert "re.search(" not in src, (
        "fast_intake.py must not use re.search(). Use re.fullmatch() "
        "for anchored full-match semantics."
    )
