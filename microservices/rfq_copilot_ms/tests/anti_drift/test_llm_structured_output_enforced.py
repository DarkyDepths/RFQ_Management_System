"""CI guard — Planner / Compose / Judge MUST call LlmConnector.complete()
with ``response_format`` set (Batch 9.1).

The Slice 1 audit found that all three stages were calling Azure
without the structured-output schema enforcement promised by the
freeze doc:

  freeze §2.1 / planner.py docstring:
    "JSON-schema-enforced output via Azure OpenAI's response_format
    parameter (no free text -- see §8 forbidden list)."

The implementation initially relied on prompt-only JSON formatting,
which let GPT-4o occasionally drop required fields and routed the
turn to Path 8.5 ``llm_unavailable``. Fix: pass
``response_format={"type": "json_schema", "json_schema": {...}}`` on
every Planner / Compose / Judge call.

This guard is a static AST scan over the three stage files. It looks
for any ``llm_connector.complete(...)`` or ``self._llm.complete(...)``
call expression and asserts the keyword argument ``response_format``
is provided. Catches a regression where someone removes the kwarg
("the model usually returns valid JSON anyway").

Same scan also asserts ``temperature`` is passed -- without it,
Azure defaults to ~1.0 which makes the schema-mismatch class of
flakiness much more likely.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[2] / "src"
PIPELINE_DIR = SRC_DIR / "pipeline"

# (file under audit, set of kwarg names that MUST appear on at least
#  one .complete(...) call inside the file)
_AUDITED_STAGES: tuple[tuple[str, frozenset[str]], ...] = (
    ("planner.py", frozenset({"response_format", "temperature"})),
    ("compose.py", frozenset({"response_format", "temperature"})),
    ("judge.py",   frozenset({"response_format", "temperature"})),
)


def _find_complete_calls(tree: ast.AST) -> list[ast.Call]:
    """Return every Call node whose attribute is ``.complete``."""
    out: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        # Match foo.complete(...) or self._llm.complete(...) shapes.
        if isinstance(func, ast.Attribute) and func.attr == "complete":
            out.append(node)
    return out


def _kwarg_names(call: ast.Call) -> set[str]:
    return {kw.arg for kw in call.keywords if kw.arg is not None}


@pytest.mark.parametrize("filename,required_kwargs", _AUDITED_STAGES)
def test_llm_complete_calls_pass_required_kwargs(
    filename: str, required_kwargs: frozenset[str],
):
    """Every ``.complete(...)`` call in the audited stage file must
    pass the required kwargs (response_format + temperature).

    Why both:
    * ``response_format`` enforces the JSON shape at the API level
      (the freeze doc promise that wasn't being kept).
    * ``temperature`` propagates the per-stage tuning value (Planner
      0.0, Compose ~0.3, Judge 0.0) -- without it Azure defaults to
      ~1.0, defeating the "deterministic classification" property.
    """
    path = PIPELINE_DIR / filename
    assert path.is_file(), f"audited stage file missing: {path}"

    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls = _find_complete_calls(tree)
    assert calls, (
        f"{filename}: expected at least one ``.complete(...)`` call. "
        f"If you removed the LLM call, also remove this stage from "
        f"_AUDITED_STAGES."
    )

    offending: list[tuple[int, set[str]]] = []
    for call in calls:
        kw = _kwarg_names(call)
        missing = required_kwargs - kw
        if missing:
            offending.append((call.lineno, missing))

    assert not offending, (
        f"{filename}: every LlmConnector.complete(...) call must pass "
        f"{sorted(required_kwargs)}. Offending lines (with missing kwargs): "
        f"{offending}. See Batch 9.1 audit P0-2 / P1-2 -- this is what "
        f"prevented the Slice 1 Planner from working in app testing."
    )


# ── Planner-constants sync ───────────────────────────────────────────────


def test_planner_module_constants_match_registry_config():
    """``src/pipeline/planner.py`` mirrors ``PLANNER_MODEL_CONFIG``
    values (temperature, max_tokens) as module-level constants because
    CI guard §11.5.2 forbids the planner from importing
    ``src.config.path_registry``. This test is the sync check: edit
    one, edit both.

    Importing the registry config from a TEST file is allowed (the
    guard only restricts production source under ``src/pipeline/``).
    """
    from src.config.path_registry import PLANNER_MODEL_CONFIG
    from src.pipeline import planner as planner_module

    assert planner_module._PLANNER_TEMPERATURE == PLANNER_MODEL_CONFIG.temperature, (
        "planner._PLANNER_TEMPERATURE drifted from PLANNER_MODEL_CONFIG.temperature. "
        "Update one (or both) so they match -- the registry is the design-time "
        "source of truth; the planner mirrors it because it cannot import the "
        "config module (CI guard §11.5.2)."
    )
    assert planner_module._PLANNER_MAX_TOKENS == PLANNER_MODEL_CONFIG.max_tokens, (
        "planner._PLANNER_MAX_TOKENS drifted from PLANNER_MODEL_CONFIG.max_tokens."
    )
