"""Tool Executor — Stage 6 of the v4 canonical pipeline.

See ``docs/11-Architecture_Frozen_v2.md`` §5 (Tool Executor section)
and §8 (forbidden — the deterministic stage must never become an LLM
tool-caller).

**Deterministic invocation.** Reads ``plan.allowed_evidence_tools``
(a list set by the Path Registry, copied into the plan by the factory)
and invokes each tool with arguments derived from ``resolved_targets``
and ``plan.canonical_requested_fields``. **Never an LLM call. Never
selects which tool to run.** If a future intent needs a tool that isn't
in the registry mapping, the answer is *add the mapping* — not let the
LLM pick.

Hard discipline (CI-enforced — §11.3):

* No imports from ``openai``, ``anthropic``, ``langchain``, ``langgraph``,
  ``llama_index``, ``litellm``, ``instructor``, ``mistralai``,
  ``google.generativeai``, ``cohere``, ``together``. The CI test fails
  the build if any of them appear in this file.
* No tool-selection logic. No conditional branching based on free-form
  intent.
* This module supersedes the prior v3 LLM-driven tool-calling stage
  (forbidden by the freeze §8 / Appendix A).

Inputs (read-only): ``plan.allowed_evidence_tools``,
``state.resolved_targets``, ``plan.canonical_requested_fields``,
``state.actor``.

Outputs (written): ``state.tool_invocations`` (list of forensics
records), ``state.evidence_packets`` (per-target labelled, field-
minimized per §12.2).

Batch 0 status: STUB ONLY. No tool invocation wired yet.
"""

from __future__ import annotations

from src.models.execution_state import ExecutionState


def execute(state: ExecutionState) -> None:  # noqa: ARG001
    """For each tool in ``state.plan.allowed_evidence_tools``: build
    args deterministically, invoke, append a ``ToolInvocation`` to
    ``state.tool_invocations``, populate ``state.evidence_packets``.

    Pure deterministic invocation — no LLM call, no tool selection.
    CI guard §11.3 forbids any LLM SDK import in this module.
    """
    raise NotImplementedError(
        "tool_executor.execute() scaffolded only. "
        "See docs/11-Architecture_Frozen_v2.md §5 (Tool Executor)."
    )
