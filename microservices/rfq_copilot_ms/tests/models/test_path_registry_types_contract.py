"""Contract tests — Path Registry types (§14.1, §14.2).

Verifies the type system half of the architecture before any runtime
config or factory logic ships. These tests are pure declarations checks
— no behavior is exercised.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.path_registry import (
    AccessPolicyName,
    ComparableFieldGroups,
    GuardrailId,
    IntakeSource,
    IntentConfig,
    JudgePolicy,
    JudgeTriggerName,
    MemoryPolicy,
    ModelProfile,
    PathConfig,
    PathId,
    PathRegistry,
    PersistencePolicy,
    PlannerModelConfig,
    PresentationPolicy,
    ReasonCode,
    ResolverStrategy,
    TargetPolicy,
    ToolId,
)


# ── Enum membership ───────────────────────────────────────────────────────


def test_path_id_includes_all_freeze_values():
    """PathId must include all 12 freeze §14.1 values: PATH_1..PATH_7
    and PATH_8_1..PATH_8_5."""
    expected = {
        "path_1", "path_2", "path_3", "path_4",
        "path_5", "path_6", "path_7",
        "path_8_1", "path_8_2", "path_8_3", "path_8_4", "path_8_5",
    }
    actual = {member.value for member in PathId}
    assert actual == expected, f"PathId mismatch: {actual ^ expected}"


def test_intake_source_has_exactly_three_members():
    """IntakeSource must be exactly {fast_intake, planner, escalation}.
    No more, no fewer."""
    expected = {"fast_intake", "planner", "escalation"}
    actual = {member.value for member in IntakeSource}
    assert actual == expected, (
        f"IntakeSource must be exactly {expected}, got {actual}. "
        f"Adding a fourth source would change the factory contract."
    )


def test_resolver_strategy_includes_freeze_values():
    """ResolverStrategy must cover all §14.1 entries."""
    expected = {
        "none",
        "page_default",
        "search_by_code",
        "search_by_descriptor",
        "search_portfolio_by_code_or_page_default",
        "session_state_pick",
    }
    actual = {member.value for member in ResolverStrategy}
    assert actual == expected, f"ResolverStrategy mismatch: {actual ^ expected}"


def test_access_policy_name_membership():
    """AccessPolicyName must be exactly {none, manager_mediated}."""
    expected = {"none", "manager_mediated"}
    actual = {member.value for member in AccessPolicyName}
    assert actual == expected


# ── New-type aliases are str-compatible ────────────────────────────────────


def test_open_set_newtypes_are_str_compatible():
    """ToolId / GuardrailId / ReasonCode / JudgeTriggerName are NewType
    aliases over str. At runtime they are plain strings — declared so
    that mypy / type-checkers can distinguish them statically."""
    tool: ToolId = ToolId("get_rfq_profile")
    guardrail: GuardrailId = GuardrailId("evidence")  # noqa: F841
    reason: ReasonCode = ReasonCode("no_evidence")  # noqa: F841
    trigger: JudgeTriggerName = JudgeTriggerName("answer_makes_factual_claim")  # noqa: F841
    assert isinstance(tool, str)
    assert tool == "get_rfq_profile"


# ── extra="forbid" enforcement ─────────────────────────────────────────────


def test_target_policy_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="extra"):
        TargetPolicy(min_targets=1, max_targets=1, surprise="value")  # type: ignore[call-arg]


def test_intent_config_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="extra"):
        IntentConfig(allowed_intake_sources=[IntakeSource.PLANNER], rogue=True)  # type: ignore[call-arg]


def test_path_config_rejects_unknown_fields():
    with pytest.raises(ValidationError, match="extra"):
        PathConfig(
            persistence_policy=PersistencePolicy(),
            finalizer_template_key_default="x.y",
            mystery_field=1,  # type: ignore[call-arg]
        )


# ── frozen=True attribute reassignment ─────────────────────────────────────


def test_frozen_models_reject_attribute_reassignment():
    """Pydantic ``frozen=True`` blocks attribute reassignment. This is
    the documented immutability guarantee we rely on for plan/policy
    types — NOT deep immutability of list contents (Pydantic v2 does
    not deep-freeze).

    The architectural defense against accidental mutation of plan data
    is single-construction at the factory + read-only stage access (CI
    guards §11.5.1, §11.5.2), not field immutability.
    """
    policy = TargetPolicy(min_targets=1, max_targets=1)
    with pytest.raises(ValidationError):
        policy.min_targets = 99  # type: ignore[misc]


def test_frozen_does_not_deep_freeze_list_contents():
    """Documented behavior: ``frozen=True`` is shallow. Mutating the
    contents of a list field on a frozen model is NOT prevented by
    Pydantic. This test exists to make the limitation visible — if a
    future Pydantic update changes this behavior, the assertion below
    flips and we update the docs.
    """
    cfg = PersistencePolicy()
    # session_state_writes is a list field on a frozen model.
    initial_len = len(cfg.session_state_writes)
    cfg.session_state_writes.append("rogue_key")  # not blocked by frozen
    assert len(cfg.session_state_writes) == initial_len + 1


# ── TargetPolicy.none() convenience ───────────────────────────────────────


def test_target_policy_none_classmethod():
    """``TargetPolicy.none()`` is the canonical constructor for paths
    that don't use targets at all (Path 1, Path 2, all Path 8.x)."""
    policy = TargetPolicy.none()
    assert policy.min_targets == 0
    assert policy.max_targets == 0
    assert policy.on_too_few is None
    assert policy.on_too_many is None


# ── PathConfig finalizer-template-key validator ────────────────────────────


def test_path_config_requires_finalizer_template_key_or_default():
    """Per §14.2 model_validator: a PathConfig must declare either
    ``finalizer_template_keys`` (Path 8.x) or
    ``finalizer_template_key_default`` (normal paths). Neither set =
    error — the Finalizer would have nothing to render."""
    with pytest.raises(ValidationError, match="finalizer"):
        PathConfig(persistence_policy=PersistencePolicy())


def test_path_config_accepts_template_keys_only():
    """Path 8.x families set the keyed dict (one template per
    reason_code), no default needed."""
    cfg = PathConfig(
        persistence_policy=PersistencePolicy(),
        finalizer_template_keys={"no_evidence": "path_8_5.no_evidence"},
    )
    assert cfg.finalizer_template_keys["no_evidence"] == "path_8_5.no_evidence"
    assert cfg.finalizer_template_key_default is None


def test_path_config_accepts_template_key_default_only():
    """Normal paths set just the default template key."""
    cfg = PathConfig(
        persistence_policy=PersistencePolicy(),
        finalizer_template_key_default="path_4_default",
    )
    assert cfg.finalizer_template_key_default == "path_4_default"
    assert cfg.finalizer_template_keys == {}


# ── PathRegistry type alias ────────────────────────────────────────────────


def test_path_registry_is_a_dict_alias_not_a_class():
    """PathRegistry is a type alias for dict[PathId, PathConfig], not a
    wrapper class with behavior. Slice 2 will populate
    PATH_CONFIGS: PathRegistry = {...} inside src/config/path_registry.py.
    """
    from typing import get_origin

    # The alias resolves to dict at runtime.
    assert get_origin(PathRegistry) is dict
    # And we can construct a value of the alias's shape directly.
    registry: PathRegistry = {
        PathId.PATH_4: PathConfig(
            persistence_policy=PersistencePolicy(),
            finalizer_template_key_default="path_4_default",
        ),
    }
    assert PathId.PATH_4 in registry


# ── Auxiliary types compile and roundtrip ──────────────────────────────────


def test_presentation_policy_roundtrip():
    p = PresentationPolicy(
        default_sort="deadline_asc",
        default_limit=10,
        on_too_many_strategy="paginate",
    )
    assert p.too_many_threshold == 50  # default


def test_comparable_field_groups_roundtrip():
    g = ComparableFieldGroups(
        A=["deadline", "owner"],
        B=["briefing_summary"],
        C=["margin", "win_probability"],
    )
    assert "margin" in g.C


def test_memory_policy_literal_scope_enforcement():
    """``episodic_scope`` is a closed Literal — invalid values are
    rejected at validation."""
    MemoryPolicy(working_pairs=5, episodic_scope="per_target")
    with pytest.raises(ValidationError):
        MemoryPolicy(working_pairs=5, episodic_scope="invalid_scope")  # type: ignore[arg-type]


def test_judge_policy_default_model_profile():
    p = JudgePolicy(triggers=[JudgeTriggerName("answer_makes_factual_claim")])
    assert p.model_profile == "gpt-4o"


def test_model_profile_construction():
    m = ModelProfile(model="gpt-4o", temperature=0.3, max_tokens=500)
    assert m.timeout_seconds == 30.0  # default


def test_planner_model_config_defaults():
    """PlannerModelConfig is the top-level config used BEFORE the path
    is known (§3.5). Its defaults match the freeze."""
    cfg = PlannerModelConfig()
    assert cfg.model == "gpt-4o"
    assert cfg.temperature == 0.0
    assert cfg.json_schema_enforced is True
    assert cfg.retry_attempts == 1


def test_intent_config_default_allowed_intake_sources_is_planner_only():
    """Default IntentConfig allows PLANNER only — operational paths must
    not accidentally become FastIntake-eligible. Path 1 / 8.2 / 8.3
    explicitly add FAST_INTAKE in the registry."""
    cfg = IntentConfig()
    assert cfg.allowed_intake_sources == [IntakeSource.PLANNER]
