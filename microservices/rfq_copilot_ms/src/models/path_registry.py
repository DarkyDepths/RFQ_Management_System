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

* **Sibling — ``src/config/path_registry.py``** (CONFIG; Slice 1)
  Holds the runtime ``PATH_CONFIGS: dict[PathId, PathConfig]`` data
  table. **Restricted to ``ExecutionPlanFactory`` and ``EscalationGate``
  only**, CI-enforced by ``tests/anti_drift/test_path_registry_reader_allowlist.py``
  (§11.5.2). Importing this module gives the importer the ability to
  enforce or bypass policy — that's the chokepoint we mechanically
  protect.

The split is the architectural commitment: types travel freely, policy
data does not.

Types declared here (Slice 1 will populate Pydantic bodies):

* ``PathId`` — closed StrEnum: PATH_1..PATH_7, PATH_8_1..PATH_8_5.
* ``IntakeSource`` — closed StrEnum: FAST_INTAKE, PLANNER, ESCALATION.
* ``ResolverStrategy`` — closed StrEnum.
* ``AccessPolicyName`` — closed StrEnum: NONE, MANAGER_MEDIATED.
* ``ToolId``, ``GuardrailId``, ``JudgeTriggerName``, ``ReasonCode``,
  ``IntakePatternId`` — open NewType aliases (str-based).
* ``TargetPolicy``, ``PresentationPolicy``, ``ComparableFieldGroups``,
  ``MemoryPolicy``, ``PersistencePolicy``, ``JudgePolicy``,
  ``ModelProfile``, ``IntentConfig``, ``PathConfig``,
  ``PlannerModelConfig`` — Pydantic config types.

Batch 0 status: STUB ONLY. No types implemented yet.
"""

from __future__ import annotations

# Implementation deferred to Slice 1 batch.
# Future shape (illustrative — do not import yet):
#
#   from enum import StrEnum
#   from typing import NewType
#   from pydantic import BaseModel
#
#   class PathId(StrEnum):
#       PATH_1 = "path_1"
#       ...
#       PATH_8_5 = "path_8_5"
#
#   class IntakeSource(StrEnum):
#       FAST_INTAKE = "fast_intake"
#       PLANNER     = "planner"
#       ESCALATION  = "escalation"
#
#   ToolId           = NewType("ToolId", str)
#   GuardrailId      = NewType("GuardrailId", str)
#   JudgeTriggerName = NewType("JudgeTriggerName", str)
#   ReasonCode       = NewType("ReasonCode", str)
#   IntakePatternId  = NewType("IntakePatternId", str)
#
#   class IntentConfig(BaseModel):
#       allowed_intake_sources: list[IntakeSource]
#       evidence_tools: list[ToolId]
#       allowed_fields: list[str]
#       forbidden_fields: list[str]
#       field_aliases: dict[str, list[str]]
#       confidence_threshold: float
#       judge_triggers: list[JudgeTriggerName]
#       # ... see §14.2 for the full field set
#
#   class PathConfig(BaseModel):
#       intent_topics: dict[str, IntentConfig]
#       # ... see §14.2
