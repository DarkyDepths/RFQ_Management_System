"""Contract tests — Path Registry runtime CONFIG (Slice 1 scope).

Verifies the runtime ``PATH_CONFIGS`` dict in
``src/config/path_registry.py`` matches the freeze and the Batch 2 spec:

* All Slice 1 required paths are present.
* Path 1 is template-only / no fetch / no access.
* Path 4 is Planner-only / manager-mediated / no intelligence fields.
* Path 8.x is template-only with reason_code-keyed templates.
* Every IntentConfig declares an intake source.
* The Path Registry split holds: tests + factory + gate may import the
  config; nothing else inside ``src/pipeline/`` may.

Tests in this file freely import the config — the CI allowlist guard
(§11.5.2) scopes its check to ``src/pipeline/`` only, NOT to
``tests/``. Tests need to validate the config, so this is correct.
"""

from __future__ import annotations

import inspect
from typing import get_args, get_origin

from src.config.path_registry import (
    PATH_CONFIGS,
    PLANNER_MODEL_CONFIG,
    REGISTRY_VERSION,
)
from src.models.path_registry import (
    AccessPolicyName,
    IntakeSource,
    IntentConfig,
    PathConfig,
    PathId,
    PathRegistry,
    PlannerModelConfig,
    ResolverStrategy,
)


# ── 1. PATH_CONFIGS imports + validates ───────────────────────────────────


def test_path_configs_imports_and_validates():
    """Importing PATH_CONFIGS triggers Pydantic validation on every entry.
    If any IntentConfig / PathConfig fails validation, the import would
    have raised — a successful import is the validation."""
    assert PATH_CONFIGS is not None
    assert len(PATH_CONFIGS) > 0


def test_registry_version_is_set():
    """REGISTRY_VERSION is required so future-us can diagnose
    "did the config change between v0.1 and v0.2" from forensics."""
    assert isinstance(REGISTRY_VERSION, str)
    assert REGISTRY_VERSION  # non-empty


def test_planner_model_config_is_a_planner_model_config():
    assert isinstance(PLANNER_MODEL_CONFIG, PlannerModelConfig)
    assert PLANNER_MODEL_CONFIG.model == "gpt-4o"


# ── 2. PATH_CONFIGS is typed as PathRegistry ──────────────────────────────


def test_path_configs_is_dict_path_id_to_path_config():
    assert isinstance(PATH_CONFIGS, dict)
    for path_id, cfg in PATH_CONFIGS.items():
        assert isinstance(path_id, PathId), (
            f"Key {path_id!r} is not a PathId enum member"
        )
        assert isinstance(cfg, PathConfig), (
            f"Value for {path_id} is not a PathConfig"
        )


def test_path_configs_matches_path_registry_alias():
    """The runtime config dict's shape matches the type alias declared
    in src/models/path_registry.py — that's the contract Slice 2 was
    asked to satisfy."""
    assert get_origin(PathRegistry) is dict
    key_type, value_type = get_args(PathRegistry)
    assert key_type is PathId
    assert value_type is PathConfig


# ── 3. Slice 1 required paths are present ─────────────────────────────────


_SLICE_1_REQUIRED_PATHS = {
    PathId.PATH_1,
    PathId.PATH_4,
    PathId.PATH_8_1,
    PathId.PATH_8_2,
    PathId.PATH_8_3,
    PathId.PATH_8_4,
    PathId.PATH_8_5,
}


def test_slice_1_required_paths_present():
    missing = _SLICE_1_REQUIRED_PATHS - set(PATH_CONFIGS.keys())
    assert not missing, f"Slice 1 missing path configs: {missing}"


def test_slice_1_does_not_pre_configure_deferred_paths():
    """Paths 2, 3, 5, 6, 7 are intentionally absent in Slice 1. Batch 3
    factory rule F1 will route any planner emission targeting them to
    8.1 ``unsupported_intent_topic``. If a future PR pre-configures
    them here, Batch 4 / 5 expectations must be revisited."""
    deferred = {
        PathId.PATH_2,
        PathId.PATH_3,
        PathId.PATH_5,
        PathId.PATH_6,
        PathId.PATH_7,
    }
    accidentally_present = deferred & set(PATH_CONFIGS.keys())
    assert not accidentally_present, (
        f"Paths {accidentally_present} are deferred in Slice 1 but appear "
        f"in PATH_CONFIGS. If this is intentional, update the Slice plan "
        f"and the Batch 3 factory rule F1 expectations."
    )


# ── 4. Path 1 is template-only / no fetch / no access ─────────────────────


def test_path_1_is_template_only():
    p1 = PATH_CONFIGS[PathId.PATH_1]
    assert p1.access_policy == AccessPolicyName.NONE, (
        "Path 1 must not require manager access"
    )
    assert p1.resolver_strategy == ResolverStrategy.NONE, (
        "Path 1 must not invoke the Resolver"
    )
    assert p1.allowed_resolver_tools == [], (
        "Path 1 must not declare resolver tools"
    )
    assert p1.judge_policy is None, (
        "Path 1 must not run the Judge"
    )
    assert p1.model_profile is None, (
        "Path 1 must not run Compose (template-only)"
    )
    for intent_topic, ic in p1.intent_topics.items():
        assert ic.evidence_tools == [], (
            f"Path 1 intent {intent_topic!r} must not declare evidence_tools"
        )


def test_path_1_intents_present():
    """Path 1 must have greeting, thanks, farewell intents."""
    p1 = PATH_CONFIGS[PathId.PATH_1]
    expected = {"greeting", "thanks", "farewell"}
    assert expected.issubset(p1.intent_topics.keys()), (
        f"Path 1 missing required intents: {expected - p1.intent_topics.keys()}"
    )


def test_path_1_template_keys_per_intent():
    """Per Call 1(a): Path 1 uses finalizer_template_keys keyed by
    intent_topic (one template per intent: greeting/thanks/farewell)."""
    p1 = PATH_CONFIGS[PathId.PATH_1]
    for intent in ("greeting", "thanks", "farewell"):
        assert intent in p1.finalizer_template_keys, (
            f"Path 1 intent {intent!r} has no template key"
        )
        assert p1.finalizer_template_keys[intent].startswith("path_1."), (
            f"Path 1 template for {intent!r} should start with 'path_1.'"
        )


# ── 5. Path 4 does not allow FastIntake as an intake source ───────────────


def test_path_4_intents_never_allow_fast_intake():
    """Operational paths must not be reachable via FastIntake. The
    architectural defense is twofold: (1) the registry declares no
    Path 4 intent with FAST_INTAKE in allowed_intake_sources, and
    (2) the factory rule F2 enforces this at plan-build time."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    for intent_topic, ic in p4.intent_topics.items():
        assert IntakeSource.FAST_INTAKE not in ic.allowed_intake_sources, (
            f"Path 4 intent {intent_topic!r} must NOT allow FastIntake. "
            f"Got: {ic.allowed_intake_sources}"
        )
        assert IntakeSource.PLANNER in ic.allowed_intake_sources, (
            f"Path 4 intent {intent_topic!r} must allow Planner intake. "
            f"Got: {ic.allowed_intake_sources}"
        )


# ── 6. Path 4 uses manager-grounded tool ids only ─────────────────────────


_ALLOWED_PATH_4_TOOLS = {
    "get_rfq_profile",
    "get_rfq_stages",
}


def test_path_4_uses_only_manager_grounded_tools():
    """Path 4 evidence_tools must be drawn from the manager-backed tool
    set. No intelligence_ms tools (Path 5 territory), no RAG tools
    (Path 2), no portfolio search tools (Path 3)."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    for intent_topic, ic in p4.intent_topics.items():
        for tool in ic.evidence_tools:
            assert tool in _ALLOWED_PATH_4_TOOLS, (
                f"Path 4 intent {intent_topic!r} uses non-manager tool "
                f"{tool!r}. Allowed in Slice 1: {_ALLOWED_PATH_4_TOOLS}"
            )


def test_path_4_access_is_manager_mediated():
    p4 = PATH_CONFIGS[PathId.PATH_4]
    assert p4.access_policy == AccessPolicyName.MANAGER_MEDIATED


def test_path_4_has_default_template_key():
    """Path 4 declares finalizer_template_key_default (one template for
    the path, intent-aware rendering inside the Finalizer)."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    assert p4.finalizer_template_key_default is not None
    assert p4.finalizer_template_key_default.startswith("path_4.")


# ── 7. Path 4 allowed_fields excludes intelligence-only fields ────────────


_INTELLIGENCE_ONLY_FIELDS = {
    "briefing",
    "readiness",
    "workbook_review",
    "cost_prediction",
    "win_probability",
    "ranking",
    "winner",
    "estimation_quality",
    "margin",
    "bid_amount",
    "internal_cost",
    "similarity",
}


def test_path_4_allowed_fields_excludes_intelligence_and_judgment():
    """Path 4 is operational/manager-grounded ONLY. Intelligence-only or
    judgment fields must NEVER appear in any intent's allowed_fields.
    They may legitimately appear in forbidden_fields — that's the
    factory rule F5 enforcement."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    for intent_topic, ic in p4.intent_topics.items():
        leaked = set(ic.allowed_fields) & _INTELLIGENCE_ONLY_FIELDS
        assert not leaked, (
            f"Path 4 intent {intent_topic!r} has intelligence/judgment "
            f"fields in allowed_fields: {leaked}. These belong on Path 5 "
            f"(intelligence) or are FORBIDDEN by §14.2 Group C."
        )


def test_path_4_forbidden_fields_includes_judgment_set():
    """Path 4 forbidden_fields must cover the §14.2 Group C judgment
    fields (margin, win_probability, ranking, winner, estimation_quality)
    so the future factory rule F5 has a non-empty set to enforce."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    judgment_fields = {
        "margin",
        "win_probability",
        "ranking",
        "winner",
        "estimation_quality",
    }
    missing = judgment_fields - set(p4.forbidden_fields)
    assert not missing, (
        f"Path 4 forbidden_fields missing Group C judgment fields: "
        f"{missing}"
    )


# ── 8. Path 8.x is template-only ──────────────────────────────────────────


_PATH_8_IDS = [
    PathId.PATH_8_1,
    PathId.PATH_8_2,
    PathId.PATH_8_3,
    PathId.PATH_8_4,
    PathId.PATH_8_5,
]


def test_all_path_8_configs_are_template_only():
    for path_id in _PATH_8_IDS:
        cfg = PATH_CONFIGS[path_id]
        assert cfg.access_policy == AccessPolicyName.NONE, (
            f"{path_id} must not require manager access (template-only)"
        )
        assert cfg.resolver_strategy == ResolverStrategy.NONE, (
            f"{path_id} must not invoke the Resolver"
        )
        assert cfg.allowed_resolver_tools == [], (
            f"{path_id} must not declare resolver tools"
        )
        assert cfg.judge_policy is None, (
            f"{path_id} must not run the Judge (template-only)"
        )
        assert cfg.model_profile is None, (
            f"{path_id} must not run Compose (template-only)"
        )
        # Path 8.x configs declare zero intent_topics — they're entered
        # via direct Planner emission OR Escalation Gate routing, not via
        # an intent classification.
        # (Could be relaxed later if needed; documenting current shape.)
        assert cfg.intent_topics == {}, (
            f"{path_id} must not declare intent_topics — entered via "
            f"direct Planner emission or Escalation Gate routing"
        )


def test_all_path_8_configs_have_finalizer_template_keys():
    for path_id in _PATH_8_IDS:
        cfg = PATH_CONFIGS[path_id]
        assert cfg.finalizer_template_keys, (
            f"{path_id} must declare at least one finalizer_template_keys "
            f"entry — that's the only way the Finalizer can render this path"
        )
        # Every template value must be a non-empty string.
        for reason_code, template_key in cfg.finalizer_template_keys.items():
            assert isinstance(template_key, str) and template_key, (
                f"{path_id} reason {reason_code!r} has empty template key"
            )


def test_path_8_3_writes_pending_clarification_to_session_state():
    """Per freeze §3.1 Path 8.3 example — clarification turns write to
    session_state so the next turn can re-classify in context."""
    p8_3 = PATH_CONFIGS[PathId.PATH_8_3]
    assert "pending_clarification" in p8_3.persistence_policy.session_state_writes


# ── 9. Every IntentConfig has at least one allowed_intake_source ──────────


def test_every_intent_has_at_least_one_allowed_intake_source():
    """An IntentConfig with no allowed sources is unreachable — both
    factory rule F2 (intake source must be in the allowlist) would
    reject every plan attempt. Treat as a config bug."""
    for path_id, cfg in PATH_CONFIGS.items():
        for intent_topic, ic in cfg.intent_topics.items():
            assert len(ic.allowed_intake_sources) >= 1, (
                f"{path_id} intent {intent_topic!r} has no allowed "
                f"intake sources — unreachable"
            )


# ── 10. Every configured intent has a finalizer template path ─────────────


def test_every_configured_intent_has_a_finalizer_template_available():
    """For each (path, intent_topic) in PATH_CONFIGS, the path must
    declare either finalizer_template_keys[intent_topic] (per Call 1a
    convention for normal paths) or finalizer_template_key_default."""
    for path_id, cfg in PATH_CONFIGS.items():
        if not cfg.intent_topics:
            continue  # Path 8.x: no intents, templates keyed by reason_code
        for intent_topic in cfg.intent_topics:
            has_per_intent = intent_topic in cfg.finalizer_template_keys
            has_default = cfg.finalizer_template_key_default is not None
            assert has_per_intent or has_default, (
                f"{path_id} intent {intent_topic!r} has no template path "
                f"(neither finalizer_template_keys[{intent_topic!r}] nor "
                f"finalizer_template_key_default is set)"
            )


# ── 11. Reaffirm 5: no Path 4 intent allows FastIntake ────────────────────


def test_no_path_4_intent_allows_fast_intake_redundant():
    """Restated as a top-level guard so the assertion is visible at the
    test-name level too — operational paths are a hard FastIntake
    boundary."""
    p4 = PATH_CONFIGS[PathId.PATH_4]
    for intent_topic, ic in p4.intent_topics.items():
        assert IntakeSource.FAST_INTAKE not in ic.allowed_intake_sources


# ── 12. Path 8.4 / 8.5 don't allow Planner direct emission ────────────────


def test_path_8_4_and_8_5_have_no_intent_topics():
    """8.4 (inaccessible) and 8.5 (no-evidence/source-down/llm-down) can
    only be reached via the Escalation Gate routing a stage failure
    trigger — never via direct Planner emission. The cleanest way to
    encode this in Slice 1's type surface is to declare no intent
    topics: the Planner has no (path, intent_topic) pair to emit, and
    PlannerValidator rule 2d would reject any direct attempt anyway."""
    for path_id in (PathId.PATH_8_4, PathId.PATH_8_5):
        assert PATH_CONFIGS[path_id].intent_topics == {}, (
            f"{path_id} must declare no intent_topics — direct Planner "
            f"emission is forbidden by §2.3 rule 2d"
        )


# ── 13. CI guard scope unchanged: only factory + gate may import config ───


def test_registry_config_allowlist_still_only_factory_and_gate():
    """Defensive check: this batch added the import to factory + gate
    but must NOT have widened the allowlist. The CI guard test in
    tests/anti_drift/ continues to enforce this; here we assert the
    allowlist constants on that test module did not drift."""
    from tests.anti_drift import test_path_registry_reader_allowlist as guard

    assert guard.FORBIDDEN_MODULE == "src.config.path_registry"
    # ALLOWED set members (resolved as Paths) point only at the two files.
    allowed_names = {p.name for p in guard.ALLOWED}
    assert allowed_names == {"execution_plan_factory.py", "escalation_gate.py"}, (
        f"Registry-config allowlist drifted: {allowed_names}"
    )


# ── 14. src.models.path_registry remains freely importable ────────────────


def test_types_module_remains_importable():
    """Sanity restated at the config-test layer — Batch 2 must not have
    accidentally restricted the types module."""
    import src.models.path_registry as types_mod
    assert inspect.ismodule(types_mod)
    # And the types we depend on are still there.
    from src.models.path_registry import PathConfig, IntentConfig, PathId  # noqa: F401


# ── Batch 0 functional smoke / anti-drift remain green ────────────────────
# (These run as part of the full suite; see other test files. We don't
#  re-run them here — that would double-count and slow CI.)
