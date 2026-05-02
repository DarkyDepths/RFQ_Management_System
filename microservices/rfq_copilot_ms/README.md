# rfq_copilot_ms

Conversational copilot microservice for the RFQ Lifecycle Management platform. Reads from `rfq_manager_ms` (operational truth) and `rfq_intelligence_ms` (derived intelligence), bounded by the trust-boundary architecture frozen in [`docs/11-Architecture_Frozen_v2.md`](docs/11-Architecture_Frozen_v2.md).

## Status

This service ships **two parallel API lanes** during the migration:

| Lane | Prefix | Status | Purpose |
|---|---|---|---|
| **v1** | `/rfq-copilot/v1/...` | **working MVP** | Current demo/UI surface. Manager-grounded RFQ + portfolio replies via `rfq_grounded_reply` and `portfolio_grounded_reply`. Preserved for UI/demo continuity. |
| **v2** | `/rfq-copilot/v2/...` | **scaffolded** (returns `501`) | Frozen v4 trust-boundary architecture lane. Implementation lands across Slice 1 batches. |

**No v4 behavior ships in Batch 0.** The /v2 lane is reachable, returns a stable `501 Not Implemented` JSON body, and exists so the architecture's surface — routes, modules, type-contract files, anti-drift CI guards — is in place before any pipeline stage is wired.

## Architecture (v4 — canonical)

The frozen v4 pipeline is a deterministic state machine with the LLM constrained to three roles: Planner (classify), Compose (render), Judge (verify). Every other decision is owned by code, the registry, or an external system.

```
FastIntake (Stage 0, anchored regex)        \
                                              -- ExecutionPlanFactory -- (single TurnExecutionPlan constructor)
GPT-4o Planner -> PlannerValidator           /     reads Path Registry, applies rules F1-F8,
                                                   field-alias normalization, source-aware policy
   |
   v
Resolver -> Access -> Memory Load -> Tool Executor (deterministic) -> Evidence Check
   |
   v
Context Builder -> Compose -> Guardrails -> Judge -> Finalizer (template by reason_code) -> Persist
```

Cross-cutting:

- **Escalation Gate** — single intercept of every stage's failure trigger. Re-enters `ExecutionPlanFactory.build_from_escalation(...)` to construct the safe Path 8.x plan; never instantiates `TurnExecutionPlan` directly.
- **Path Registry** — single source of policy truth. Read at runtime **only** by `ExecutionPlanFactory` and `EscalationGate`. CI-enforced.
- **Three CI guards** (§11.5): only the factory may construct `TurnExecutionPlan`; only factory + gate may import the registry; FastIntake patterns must use anchored full-match.

Two intake sources, one plan factory, one escalation gate. The LLM produces language; code produces truth; policy enforces boundaries; the Judge verifies; templates render the safe answer when nothing else worked.

## Spec sources

The canonical specification is:

- **[`docs/11-Architecture_Frozen_v2.md`](docs/11-Architecture_Frozen_v2.md)** — frozen architecture, type contracts (§14), CI guards (§11.5), V1 release readiness (§12).
- **[`docs/rfq_copilot_architecture_v4.html`](docs/rfq_copilot_architecture_v4.html)** — visual rendering of that architecture (open in a browser).

Inherited and still in force per Architecture_Frozen_v2 Appendix A:

- [`1-COPILOT_PHILOSOPHY.md`](docs/1-COPILOT_PHILOSOPHY.md) — LLM/system division of responsibility.
- [`4-Capability__Evidence_Boundary_(what_the_system_is_allowed_to_do).md`](docs/4-Capability__Evidence_Boundary_(what_the_system_is_allowed_to_do).md) — capability boundaries.
- [`9-Path_Config_Table_v1.md`](docs/9-Path_Config_Table_v1.md) **§1 invariants** and **§4 per-path configs** only — the rest of that doc is partially superseded; see its banner.
- [`10-Stress_Test_Set_v1.md`](docs/10-Stress_Test_Set_v1.md) — 30-query test set; seeds the Slice 1 eval CSV (§11.2 / §12.5).

Superseded (do not use as implementation guidance — see Architecture_Frozen_v2 Appendix A for the full list of supersessions):

- The prior `v3` architecture HTML diagram — invalidated by the freeze; the file in `docs/` carries a banner.
- The prior planner-with-deterministic-fallback framing in `9-Path_Config_Table_v1.md` §2.1 — replaced by FastIntake + Planner + PlannerValidator + ExecutionPlanFactory.
- The prior tool-calling stage naming — replaced by `Tool Executor` (deterministic).

## Layout

```
src/
  app.py                           FastAPI app factory; registers /v1 and /v2 routers
  app_context.py                   DI wiring
  database.py                      SQLAlchemy engine + Base
  config/
    settings.py                    Pydantic settings
  connectors/
    manager_ms_connector.py        rfq_manager_ms HTTP (operational truth)
    llm_connector.py               Azure OpenAI
  controllers/
    thread_controller.py           Thread lifecycle (v1)
    turn_controller.py             Single-turn pipeline (v1)
  datasources/                     Conversation DB: turns, threads, audit_log, ...
  models/
    db.py / actor.py / thread.py / turn.py / manager_dto.py    (v1)
    intake_decision.py             (Slice 1 -- §2.6)
    planner_proposal.py            (Slice 1 -- §2.1, §2.4)
    execution_plan.py              (Slice 1 -- §2.2, §2.7)
    execution_state.py             (Slice 1 -- §2.5)
    path_registry.py               (Slice 1 -- type contracts §14.1, §14.2)
  pipeline/                        v4 stages (stubs in Batch 0 -- bodies in Slice 1)
    fast_intake.py                 Stage 0 -- anchored regex (§5.0)
    fast_intake_patterns.py        Slice 1 pattern table
    planner.py                     Stage 1 -- GPT-4o structured Planner (§2.1)
    planner_validator.py           Stage 2 -- LLM-failure structural checks (§2.3)
    execution_plan_factory.py      Stage 2.5 -- single TurnExecutionPlan constructor (§2.7)
    execution_state.py             Runtime state helpers
    tool_executor.py               Stage 6 -- deterministic tool invocation
    escalation_gate.py             Cross-cutting -- re-enters factory (§5.2)
    finalizer.py                   Stage 12 -- template render by reason_code
  routes/
    health_routes.py               GET /health
    entry_routes.py                v1 thread lifecycle
    turn_routes.py                 v1 turn endpoint
    thread_routes.py               v1 thread inspection (stub)
    v2/turn_routes.py              v2 placeholder -- returns 501
  services/
    rfq_grounded_reply.py          v1 manager-grounded RFQ replies
    portfolio_grounded_reply.py    v1 portfolio replies
  translators/
    manager_translator.py          rfq_manager_ms <-> evidence
  utils/                           auth_context, errors, helpers
tests/
  anti_drift/                      CI guards (§11.3, §11.5)
  smoke/                           /v1 and /v2 reachability smoke
docs/                              Specs (see above)
```

## Run

```
uvicorn src.app:app --reload --port 8003
```

Dev dependencies (testing): `pip install -r requirements-dev.txt`.

## Implementation roadmap

Slice 1 batches (after Batch 0):

1. Type contracts (`src/models/*` Pydantic bodies)
2. Path Registry config (`src/config/path_registry.py` PATH_CONFIGS)
3. FastIntake stage + pattern table
4. PlannerValidator (rules 1, 2, 2b, 2c, 2d, 3, 4, 5)
5. ExecutionPlanFactory (rules F1..F8 + alias normalization)
6. Escalation Gate (matrix + factory re-entry)
7. Planner connector (Azure OpenAI structured output)
8. Resolver + Access (Path 4 only)
9. Tool Executor + Evidence Check + Context Builder (with §12.1 untrusted-data delimiters)
10. Compose + Guardrails + Judge
11. Finalizer (template-first §12.6) + Persist + ExecutionRecord schema
12. Orchestrator (stage skipping, `turn_budget_exceeded`, one-turn-per-thread §12.4)
13. Slice 1 eval CSV (§12.5 minimum bar)

Each batch is one PR, tests included, CI guards stay green.
