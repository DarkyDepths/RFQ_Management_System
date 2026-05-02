"""CI guard §11.3 — deterministic stages must never import an LLM SDK.

See ``docs/11-Architecture_Frozen_v2.md`` §11.3.

The Tool Executor and the other deterministic stages (FastIntake,
PlannerValidator, Resolver, Access, Memory Load, Evidence Check,
Context Builder, Guardrails, Finalizer, Persist) must remain pure code
— no LLM call from any of them. The freeze (§8) explicitly forbids
"renaming Tool Executor back to an LLM tool-caller or letting it call
an LLM."

This test walks the AST of each named deterministic-stage module and
fails if it imports any well-known LLM SDK. The Planner, Compose, and
Judge stages legitimately call the LLM (via ``connectors/llm_connector``,
which encapsulates the SDK call) — those modules are NOT scoped here.
"""

from __future__ import annotations

import ast
from pathlib import Path


PIPELINE_DIR = Path(__file__).resolve().parents[2] / "src" / "pipeline"

# Stage modules that MUST stay deterministic (no LLM SDK imports).
DETERMINISTIC_STAGE_FILES = [
    PIPELINE_DIR / "fast_intake.py",
    PIPELINE_DIR / "fast_intake_patterns.py",
    PIPELINE_DIR / "planner_validator.py",
    PIPELINE_DIR / "execution_plan_factory.py",
    PIPELINE_DIR / "execution_state.py",
    PIPELINE_DIR / "tool_executor.py",
    PIPELINE_DIR / "escalation_gate.py",
    PIPELINE_DIR / "finalizer.py",
    # Future deterministic stages (not yet stubbed; uncomment when added):
    # PIPELINE_DIR / "resolver.py",
    # PIPELINE_DIR / "access.py",
    # PIPELINE_DIR / "memory.py",
    # PIPELINE_DIR / "evidence_check.py",
    # PIPELINE_DIR / "context_builder.py",
    # PIPELINE_DIR / "persist.py",
]

FORBIDDEN_TOP_LEVEL = {
    "openai",
    "anthropic",
    "langchain",
    "langgraph",
    "llama_index",
    "litellm",
    "instructor",
    "mistralai",
    "cohere",
    "together",
}
# google.generativeai - matched by top-level "google" + ".generativeai" suffix check


def _imported_top_levels(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                out.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.add(node.module.split(".")[0])
    return out


def test_deterministic_stages_have_no_llm_sdk_imports():
    offenders: dict[str, set[str]] = {}
    for stage_path in DETERMINISTIC_STAGE_FILES:
        if not stage_path.exists():
            continue  # not yet stubbed; covered when the stage ships
        imported = _imported_top_levels(stage_path)
        leaked = imported & FORBIDDEN_TOP_LEVEL
        # Special case: google has many subpackages; only google.generativeai is the LLM
        if "google" in imported:
            tree = ast.parse(stage_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.ImportFrom)
                    and node.module
                    and node.module.startswith("google.generativeai")
                ) or (
                    isinstance(node, ast.Import)
                    and any(a.name.startswith("google.generativeai") for a in node.names)
                ):
                    leaked.add("google.generativeai")
                    break
        if leaked:
            offenders[stage_path.name] = leaked

    assert not offenders, (
        f"Deterministic stages must not import any LLM SDK. "
        f"Offenders: {offenders}. "
        f"See docs/11-Architecture_Frozen_v2.md §11.3 / §8."
    )
