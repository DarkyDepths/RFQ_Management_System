"""Path Registry **types** — v4 type contracts (§14.1, §14.2).

See ``docs/11-Architecture_Frozen_v2.md`` §14 (authoritative type
contracts) and §3.2 (registry reader allowlist).

================================================================
"Path Registry" = two complementary modules. This is the TYPES half.
================================================================

* **This module — ``src/models/path_registry.py``** (TYPES)
  Pure declarations: ``PathId``, ``IntakeSource``, ``IntentConfig``,
  ``PathConfig``, ``TargetPolicy``, ``MemoryPolicy``,
  ``PersistencePolicy``, etc. **Importable from anywhere.** Plan
  models, stage signatures, the factory protocol, and tests all need
  these — restricting them would break the type system. Importing a
  type carries no runtime policy data.

* **Sibling — ``src/config/path_registry.py``** (CONFIG; Slice 2)
  Will hold the runtime ``PATH_CONFIGS: PathRegistry`` data table.
  **Restricted to ``ExecutionPlanFactory`` and ``EscalationGate``
  only**, CI-enforced by
  ``tests/anti_drift/test_path_registry_reader_allowlist.py``
  (§11.5.2). Importing this module gives the importer the ability to
  enforce or bypass policy — that's the chokepoint we mechanically
  protect.

The split is the architectural commitment: types travel freely, policy
data does not.

================================================================
What lives here (Batch 1)
================================================================

* Closed-set identifier StrEnums: ``PathId``, ``IntakeSource``,
  ``ResolverStrategy``, ``AccessPolicyName``.
* Open-set identifier NewType aliases: ``ToolId``, ``GuardrailId``,
  ``JudgeTriggerName``, ``ReasonCode``, ``IntakePatternId``.
* Pydantic config types: ``TargetPolicy``, ``PresentationPolicy``,
  ``ComparableFieldGroups``, ``MemoryPolicy``, ``PersistencePolicy``,
  ``JudgePolicy``, ``ModelProfile``, ``IntentConfig``, ``PathConfig``,
  ``PlannerModelConfig``.
* Type alias: ``PathRegistry = dict[PathId, PathConfig]`` — the shape
  of the runtime config dict that Slice 2 will populate.

All Pydantic config models are ``frozen=True`` + ``extra="forbid"`` per
the freeze. ``frozen=True`` is shallow in Pydantic v2 (it blocks
attribute reassignment, not list-content mutation); deep immutability
is not the architectural defense — CI guard §11.5.1
(single-construction) is.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal, NewType, Optional, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Closed-set identifiers (StrEnum) ──────────────────────────────────────


class PathId(StrEnum):
    """Closed enum of path identifiers (§14.1).

    PATH_1..PATH_7 are the answer paths; PATH_8_1..PATH_8_5 are the
    safety/escalation sub-cases.
    """

    PATH_1 = "path_1"
    PATH_2 = "path_2"
    PATH_3 = "path_3"
    PATH_4 = "path_4"
    PATH_5 = "path_5"
    PATH_6 = "path_6"
    PATH_7 = "path_7"
    PATH_8_1 = "path_8_1"
    PATH_8_2 = "path_8_2"
    PATH_8_3 = "path_8_3"
    PATH_8_4 = "path_8_4"
    PATH_8_5 = "path_8_5"


class IntakeSource(StrEnum):
    """Which classification source produced the input that the
    ExecutionPlanFactory built from. Forensic field on
    ``TurnExecutionPlan.source``; checked against
    ``IntentConfig.allowed_intake_sources`` by factory rule F2.
    """

    FAST_INTAKE = "fast_intake"
    PLANNER = "planner"
    ESCALATION = "escalation"


class ResolverStrategy(StrEnum):
    """Resolution strategy the Resolver applies. Copied into the plan
    by the factory; the Resolver reads only ``plan.resolver_strategy``
    (never the registry directly).
    """

    NONE = "none"
    PAGE_DEFAULT = "page_default"
    SEARCH_BY_CODE = "search_by_code"
    SEARCH_BY_DESCRIPTOR = "search_by_descriptor"
    SEARCH_PORTFOLIO_BY_CODE_OR_PAGE_DEFAULT = (
        "search_portfolio_by_code_or_page_default"
    )
    SESSION_STATE_PICK = "session_state_pick"


class AccessPolicyName(StrEnum):
    """Per-path access enforcement strategy."""

    NONE = "none"
    MANAGER_MEDIATED = "manager_mediated"


# ── Open-set identifiers (NewType — grow as paths ship) ───────────────────

ToolId = NewType("ToolId", str)
"""Tool identifier (e.g. ``"get_rfq_profile"``, ``"search_portfolio"``,
``"query_rag"``). Open-set — declared in the Path Registry config and
mapped by the Tool Executor."""

GuardrailId = NewType("GuardrailId", str)
"""Guardrail identifier (e.g. ``"evidence"``, ``"scope"``, ``"shape"``,
``"target_isolation"``). Open-set."""

JudgeTriggerName = NewType("JudgeTriggerName", str)
"""Judge trigger identifier (e.g. ``"answer_makes_factual_claim"``).
Open-set."""

ReasonCode = NewType("ReasonCode", str)
"""Sub-classification of an escalation. Drives Finalizer template
selection. See freeze §6 for the catalog."""

IntakePatternId = NewType("IntakePatternId", str)
"""FastIntake pattern identifier (e.g. ``"greeting_v1"``,
``"empty_v1"``, ``"nonsense_punct_v1"``). Open-set."""


# ── Frozen Pydantic config types (§14.2) ──────────────────────────────────


_FROZEN = ConfigDict(extra="forbid", frozen=True, protected_namespaces=())
"""Standard model_config for every Path Registry config type:
forbid unknown fields, freeze attribute reassignment, allow ``model_*``
field names (we use ``model_profile`` — Pydantic v2 reserves ``model_``
by default but we deliberately want this name to match the freeze §14
contract). List/dict contents are NOT deep-frozen — that's a
documented Pydantic v2 limitation. The real architectural defense is
single-construction at the factory plus read-only stage access
(§11.5.1)."""


class TargetPolicy(BaseModel):
    """Per-path / per-intent target arity policy (§14.2).

    ``on_too_few`` / ``on_too_many`` are Optional so paths that don't
    use targets at all (Path 1, Path 2, the minimal Path 8.x plans
    built by the Escalation Gate) can declare
    ``TargetPolicy.none()`` without inventing fake reason codes.
    """

    model_config = _FROZEN

    min_targets: int
    max_targets: int
    on_too_few: Optional[ReasonCode] = None
    on_too_many: Optional[ReasonCode] = None

    @classmethod
    def none(cls) -> "TargetPolicy":
        """Convenience for paths that don't use targets at all."""
        return cls(min_targets=0, max_targets=0, on_too_few=None, on_too_many=None)


class PresentationPolicy(BaseModel):
    """Path 3 only — how to present large result sets without
    auto-escalating to 8.3 (§14.2).
    """

    model_config = _FROZEN

    default_sort: str
    default_limit: int
    on_too_many_strategy: Literal["paginate", "summarize", "clarify"]
    too_many_threshold: int = 50


class ComparableFieldGroups(BaseModel):
    """Path 7 only — A=operational fields, B=intelligence fields,
    C=FORBIDDEN judgment fields (§14.2).

    ``ExecutionPlanFactory`` rule F7 rejects any
    ``canonical_requested_fields ∩ C`` to 8.1
    ``group_C_field_requested``. The post-compose
    ``comparable_field_policy`` guardrail is backup only.
    """

    model_config = _FROZEN

    A: list[str]
    B: list[str]
    C: list[str]


class MemoryPolicy(BaseModel):
    """Per-path memory policy."""

    model_config = _FROZEN

    working_pairs: int
    episodic_scope: Literal["per_target", "per_thread", "none"]


class PersistencePolicy(BaseModel):
    """Per-path persistence policy. ``session_state_writes`` lists which
    ``session_state`` keys this path may write to (e.g. Path 8.3 writes
    ``pending_clarification``).
    """

    model_config = _FROZEN

    store_user_msg: bool = True
    store_assistant_msg: bool = True
    store_tool_calls: bool = True
    store_source_refs: bool = True
    store_judge_verdict: bool = True
    episodic_contribution: bool = True
    update_last_activity: bool = True
    session_state_writes: list[str] = Field(default_factory=list)


class JudgePolicy(BaseModel):
    """Per-path Judge policy. Empty ``triggers`` skips the Judge stage
    (per §5.1 stage-skip convention).
    """

    model_config = _FROZEN

    triggers: list[JudgeTriggerName]
    model_profile: str = "gpt-4o"
    timeout_seconds: float = 10.0


class ModelProfile(BaseModel):
    """LLM call profile used by the Compose stage. ``None`` on a path
    means template-only — Compose is skipped per §5.1.
    """

    model_config = _FROZEN

    model: str
    temperature: float
    max_tokens: int
    timeout_seconds: float = 30.0


class IntentConfig(BaseModel):
    """One ``(path, intent_topic)`` entry in the Path Registry (§14.2).

    Source-aware policy: ``allowed_intake_sources`` is checked by
    ``ExecutionPlanFactory`` rule F2 — FastIntake cannot emit operational
    intents, the Planner cannot short-circuit FastIntake-only intents.
    """

    model_config = _FROZEN

    allowed_intake_sources: list[IntakeSource] = Field(
        default_factory=lambda: [IntakeSource.PLANNER]
    )
    evidence_tools: list[ToolId] = Field(default_factory=list)
    rag_required: bool = True
    controlled_domain_prompt_key: Optional[str] = None
    required_query_slots: list[str] = Field(default_factory=list)
    presentation_policy: Optional[PresentationPolicy] = None
    comparable_field_groups: Optional[ComparableFieldGroups] = None
    min_accessible_targets_for_comparison: Optional[int] = None
    allowed_fields: list[str] = Field(default_factory=list)
    field_aliases: dict[str, list[str]] = Field(default_factory=dict)
    confidence_threshold: float = 0.7
    judge_triggers: list[JudgeTriggerName] = Field(default_factory=list)


class PathConfig(BaseModel):
    """One path in the Path Registry (§14.2).

    Either ``finalizer_template_keys`` (for Path 8.x families with one
    template per ``reason_code``) or ``finalizer_template_key_default``
    (for normal paths with a single template) MUST be set — enforced by
    the post-init validator below.
    """

    model_config = _FROZEN

    intent_topics: dict[str, IntentConfig] = Field(default_factory=dict)
    resolver_strategy: ResolverStrategy = ResolverStrategy.NONE
    allowed_resolver_tools: list[ToolId] = Field(default_factory=list)
    required_target_policy: Optional[TargetPolicy] = None
    access_policy: AccessPolicyName = AccessPolicyName.NONE
    forbidden_fields: list[str] = Field(default_factory=list)
    memory_policy: Optional[MemoryPolicy] = None
    persistence_policy: PersistencePolicy
    active_guardrails: list[GuardrailId] = Field(default_factory=list)
    judge_policy: Optional[JudgePolicy] = None
    finalizer_template_keys: dict[str, str] = Field(default_factory=dict)
    finalizer_template_key_default: Optional[str] = None
    model_profile: Optional[ModelProfile] = None

    @model_validator(mode="after")
    def _check_finalizer_config(self) -> "PathConfig":
        """At least one of ``finalizer_template_keys`` /
        ``finalizer_template_key_default`` must be set. Path 8.x families
        use the keyed dict (one template per ``reason_code``); normal
        paths use the default. Mixed mode is allowed — keys win when a
        ``reason_code`` matches, default is the fallback.
        """
        has_keys = bool(self.finalizer_template_keys)
        has_default = self.finalizer_template_key_default is not None
        if not (has_keys or has_default):
            raise ValueError(
                "PathConfig must declare finalizer_template_keys (Path 8.x) "
                "or finalizer_template_key_default (normal paths) — neither is set."
            )
        return self


class PlannerModelConfig(BaseModel):
    """Top-level Planner configuration. Used BEFORE the path is known
    (the Planner classifies the turn into a path), so it cannot be
    derived from any per-path ``PathConfig.model_profile``. See §3.5.
    """

    model_config = _FROZEN

    model: str = "gpt-4o"
    temperature: float = 0.0
    max_tokens: int = 800
    timeout_seconds: float = 15.0
    json_schema_enforced: bool = True
    retry_attempts: int = 1


# ── Type alias for the runtime registry shape ─────────────────────────────


PathRegistry: TypeAlias = dict[PathId, PathConfig]
"""Shape of the runtime config dict. Slice 2 will populate
``PATH_CONFIGS: PathRegistry = { … }`` inside
``src/config/path_registry.py``. This alias is the contract that file
must satisfy — and the type future stages (factory, gate) will use to
declare their dependency on the registry."""
