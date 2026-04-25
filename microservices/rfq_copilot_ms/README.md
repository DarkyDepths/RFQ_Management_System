# rfq_copilot_ms

Copilot microservice for the RFQ Lifecycle Management platform. Conversational layer that reads from rfq_manager_ms (operational truth) and rfq_intelligence_ms (derived intelligence), bounded by a frozen execution contract.

## Architecture

Layered architecture (consistent with rfq_manager_ms / rfq_intelligence_ms):

```
routes/        →  FastAPI endpoints (turn, threads, health)
controllers/   →  TurnController orchestrates the pipeline
pipeline/      →  12 stages: planner → resolver → access → memory → context → agent → evidence_check → compose → guardrails → judge → finalizer → escalation_gate → persist
datasources/   →  Conversation DB (turns, threads, session_state, audit_log, episodic)
connectors/    →  manager_ms, intelligence_ms, RAG, Anthropic, event_bus
translators/   →  Pure data shape transforms (API payloads ↔ EvidencePacket)
models/        →  Pydantic + SQLAlchemy contracts
config/        →  PATH_CONFIGS registry, invariants, temporal filters, forbidden inferences
utils/         →  Pure helpers (claim detector, RFQ code parser, etc.)
```

## Spec sources

See `docs/`:
- `1-COPILOT_PHILOSOPHY.md` ... `8-Challenges_(Known__Hidden).md` — frozen design
- `9-Path_Config_Table_v1.md` — execution contract (v1.1, paper-walkthrough validated)
- `10-Stress_Test_Set_v1.md` — 30-query test set (phase A done, phase B pending)
- `rfq_copilot_architecture_v3.html` — visual architecture

## Status

**Skeleton only — no implementation.** Awaiting code phase post phase-B stress test.
