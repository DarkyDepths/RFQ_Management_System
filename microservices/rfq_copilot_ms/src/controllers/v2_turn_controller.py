"""V2TurnController — orchestrates the v4 pipeline for /v2 turns.

Slice 1 / Batch 5 wiring:

  FastIntake.try_match
    on hit  -> factory.build_from_intake -> finalizer.finalize -> response
    on miss -> Planner.classify
                -> PlannerValidator.validate
                -> factory.build_from_planner
                -> Resolver.resolve_path_4_target
                -> Access.check_path_4_access
                -> ToolExecutor.execute_path_4
                -> EvidenceCheck.check_path_4
                -> ContextBuilder.build_path_4
                -> Path4Renderer.render_path_4 (writes state.final_text)
                -> Finalizer.finalize (passes through Path 4, renders Path 8.x)

  Any StageError raised at any point is caught and routed via the
  EscalationGate, which re-enters the factory to construct the safe
  Path 8.x plan. The Finalizer then renders the safe template.

This module sits between the FastAPI route (which is now thin: just
parse + call + serialize) and the pipeline stages (which are pure
deterministic functions or LLM-injected services).
"""

from __future__ import annotations

import logging
import time
import uuid

from sqlalchemy.orm import Session

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.execution_plan import FactoryRejection
from src.models.execution_record import ExecutionRecordStatus
from src.models.execution_state import ExecutionState
from src.models.path_registry import PathId, ReasonCode
from src.models.planner_proposal import (
    ValidatedPlannerProposal,
    ValidationRejection,
)
from src.models.v2_turn import V2TurnRequest, V2TurnResponse
from src.pipeline import (
    access as access_stage,
    compose as compose_stage,
    context_builder as context_stage,
    evidence_check as evidence_stage,
    execution_state as exec_state_helpers,
    fast_intake,
    finalizer as finalizer_stage,
    guardrails as guardrails_stage,
    judge as judge_stage,
    path4_renderer,
    persist as persist_stage,
    resolver as resolver_stage,
    tool_executor as tool_executor_stage,
)
from src.pipeline.errors import StageError
from src.pipeline.escalation_gate import EscalationGate
from src.pipeline.execution_plan_factory import ExecutionPlanFactory
from src.pipeline.planner import Planner
from src.pipeline.planner_validator import PlannerValidator
from src.utils.errors import LlmUnreachable


logger = logging.getLogger(__name__)


# Path 4 intents whose answers are produced by the LLM Compose stage
# (with Judge verification) instead of the deterministic path4_renderer.
# Synthesis intents — multi-field, fluent prose, deterministic renderers
# can't naturally produce them at quality.
#
# TODO: Move this to PATH_CONFIGS as a per-intent render policy in a
# future batch (e.g. ``IntentConfig.compose_eligible: bool``). Slice 1
# keeps it module-local so the registry stays free of behavior knobs.
COMPOSE_ELIGIBLE_PATH4_INTENTS: frozenset[str] = frozenset({"summary", "blockers"})


class V2TurnController:
    """Single orchestration entry point for /v2 turns.

    Constructor takes all collaborators so tests can inject fakes
    (FakeLlmConnector, FakeManagerConnector) without touching DI wiring.
    """

    def __init__(
        self,
        *,
        factory: ExecutionPlanFactory,
        validator: PlannerValidator,
        gate: EscalationGate,
        planner: Planner | None = None,
        manager: ManagerConnector | None = None,
        llm_connector: LlmConnector | None = None,
        session: Session | None = None,
        registry_version: str | None = None,
    ):
        self._factory = factory
        self._validator = validator
        self._gate = gate
        # Planner + manager are lazy / optional — Slice 1 FastIntake
        # path doesn't need them. Tests for Path 8.5 llm_unavailable
        # may inject None for planner explicitly to assert the route
        # surfaces a clean 200 (Path 8.5 template).
        self._planner = planner
        self._manager = manager
        # LLM connector is used by Compose + Judge for Path 4 synthesis
        # intents (summary, blockers). When None, those intents fall
        # back to the deterministic path4_renderer — single-field intents
        # already use it. Tests that don't care about Compose/Judge can
        # leave this None.
        self._llm_connector = llm_connector
        # Session is optional — when None (e.g. tests that don't care
        # about persistence), Persist is skipped. In production DI
        # always provides a Session.
        self._session = session
        self._registry_version = registry_version

    # ── Public entry ──────────────────────────────────────────────────────

    def handle_turn(
        self,
        *,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
    ) -> V2TurnResponse:
        """Run the pipeline; persist the execution_record; return the
        v2 response.

        On any failure that the pipeline can recover from (StageError,
        LlmUnreachable, FactoryRejection, ValidationRejection), the
        Escalation Gate routes to a Path 8.x plan, the Finalizer
        renders the safe template, and we persist with status=
        ``escalated``. On truly-unexpected exceptions (gate failure,
        finalizer crash) we recover to a generic Path 8.5 fallback and
        persist with status=``failed`` + error_payload.

        Persistence is fire-and-forget in production: a DB blip never
        breaks the user-facing answer (Persist runs with strict=False).
        ``execution_record_id`` is None in the response when
        persistence was unavailable or failed.
        """
        started_at = time.monotonic()
        error_payload: dict | None = None
        state: ExecutionState

        try:
            # Stage 0 — FastIntake.
            decision = fast_intake.try_match(request.message)
            if decision is not None:
                state = self._handle_fast_intake_hit(
                    thread_id, request, actor, decision
                )
            else:
                state = self._handle_planner_path(thread_id, request, actor)
        except Exception as exc:
            # Unexpected — gate / finalizer / something downstream
            # crashed. Recover to a Path 8.5 placeholder so the user
            # gets a safe reply, and persist as "failed" with the
            # error payload for forensics.
            logger.exception("V2 pipeline unrecovered failure")
            error_payload = {
                "type": exc.__class__.__name__,
                "message": str(exc),
            }
            state = self._recover_unexpected_failure(thread_id, request, actor)

        duration_ms = int((time.monotonic() - started_at) * 1000)
        status = self._derive_status(state, had_error=error_payload is not None)
        record_id = self._persist(
            thread_id=thread_id,
            state=state,
            user_message=request.message,
            status=status,
            duration_ms=duration_ms,
            error_payload=error_payload,
        )
        return self._build_response(thread_id, state, execution_record_id=record_id)

    # ── FastIntake hit branch ─────────────────────────────────────────────

    def _handle_fast_intake_hit(
        self,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
        decision,
    ) -> ExecutionState:
        plan_or_rejection = self._factory.build_from_intake(
            decision=decision, actor=actor
        )
        if isinstance(plan_or_rejection, FactoryRejection):
            # Should not happen for declared FastIntake patterns.
            logger.error(
                "FastIntake -> factory rejection for %s/%s: %s",
                decision.path.value, decision.intent_topic, plan_or_rejection.trigger,
            )
            state = self._init_state_from_failed_intake(
                thread_id, request, actor, decision
            )
            self._gate.route(
                state,
                trigger=plan_or_rejection.trigger,
                reason_code=plan_or_rejection.reason_code,
                source_stage="factory",
                details={"factory_rule": plan_or_rejection.factory_rule},
            )
            finalizer_stage.finalize(state)
            return state

        plan = plan_or_rejection
        state = exec_state_helpers.init_state_from_intake(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            user_message=request.message,
            plan=plan,
            decision=decision,
        )
        state.registry_version = self._registry_version
        finalizer_stage.finalize(state)
        return state

    # ── Planner branch ────────────────────────────────────────────────────

    def _handle_planner_path(
        self,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
    ) -> ExecutionState:
        # Planner availability check — Slice 1 may run with planner=None
        # for the FastIntake-only deployment. Until LLM is configured,
        # we route any non-FastIntake message to Path 8.5 llm_unavailable.
        if self._planner is None:
            state = self._init_state_for_failure(thread_id, request, actor)
            self._gate.route(
                state,
                trigger="llm_unavailable",
                reason_code=ReasonCode("llm_unavailable"),
                source_stage="planner",
                details={"reason": "no Planner injected"},
            )
            finalizer_stage.finalize(state)
            return state

        # ── Planner.classify (LLM call) ──
        try:
            proposal = self._planner.classify(
                user_message=request.message,
                current_rfq_code=request.current_rfq_code,
            )
        except LlmUnreachable as exc:
            logger.warning("Planner LLM unreachable: %s", exc)
            state = self._init_state_for_failure(thread_id, request, actor)
            self._gate.route(
                state,
                trigger="llm_unavailable",
                reason_code=ReasonCode("llm_unavailable"),
                source_stage="planner",
                details={"cause": str(exc)},
            )
            finalizer_stage.finalize(state)
            return state

        # ── PlannerValidator.validate ──
        validated_or_rejection = self._validator.validate(proposal)
        if isinstance(validated_or_rejection, ValidationRejection):
            state = self._init_state_for_failure(thread_id, request, actor)
            state.planner_proposal = proposal
            self._gate.route(
                state,
                trigger=validated_or_rejection.trigger,
                reason_code=validated_or_rejection.reason_code,
                source_stage="validator",
                details={"rule_number": validated_or_rejection.rule_number},
            )
            finalizer_stage.finalize(state)
            return state
        validated: ValidatedPlannerProposal = validated_or_rejection

        # ── ExecutionPlanFactory.build_from_planner ──
        plan_or_rejection = self._factory.build_from_planner(validated, actor=actor)
        if isinstance(plan_or_rejection, FactoryRejection):
            state = self._init_state_for_failure(thread_id, request, actor)
            state.planner_proposal = proposal
            state.validated_planner_proposal = validated
            self._gate.route(
                state,
                trigger=plan_or_rejection.trigger,
                reason_code=plan_or_rejection.reason_code,
                source_stage="factory",
                details={"factory_rule": plan_or_rejection.factory_rule},
            )
            finalizer_stage.finalize(state)
            return state
        plan = plan_or_rejection

        # ── Build the state for downstream stages ──
        state = ExecutionState(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            plan=plan,
            user_message=request.message,
            intake_path="planner",
            planner_proposal=validated.proposal,
            validated_planner_proposal=validated,
            registry_version=self._registry_version,
        )

        # ── Path-specific downstream (Path 4 only in Slice 1) ──
        # Path 8.x direct emissions land here too — nothing to do
        # downstream; finalizer renders the template.
        if plan.path is PathId.PATH_4:
            try:
                self._run_path_4_pipeline(state, request, actor)
            except StageError as err:
                self._gate.route(
                    state,
                    trigger=err.trigger,
                    reason_code=err.reason_code,
                    source_stage=err.source_stage,  # type: ignore[arg-type]
                    details=err.details,
                )

        finalizer_stage.finalize(state)
        return state

    # ── Path 4 deterministic stage chain ─────────────────────────────────

    def _run_path_4_pipeline(
        self,
        state: ExecutionState,
        request: V2TurnRequest,
        actor: Actor,
    ) -> None:
        """Run Resolver -> Access -> ToolExecutor -> EvidenceCheck ->
        ContextBuilder -> Path4Renderer. Any stage may raise
        ``StageError``; the caller catches and routes via the Gate."""
        if self._manager is None:
            raise StageError(
                trigger="manager_unreachable",
                reason_code=ReasonCode("source_unavailable"),
                source_stage="access",
                details={"reason": "no manager connector injected"},
            )

        # Resolver — find the target.
        target = resolver_stage.resolve_path_4_target(
            target_candidates=state.plan.target_candidates,
            current_rfq_code=request.current_rfq_code,
        )
        state.resolved_targets.append(target)

        # Access — verify with manager + cache the detail for Tool Executor.
        decision, cached_detail = access_stage.check_path_4_access(
            target=target, actor=actor, manager=self._manager,
        )
        state.access_decisions.append(decision)

        # Tool Executor — invoke plan-approved manager tools.
        tool_executor_stage.execute_path_4(
            state=state,
            actor=actor,
            manager=self._manager,
            cached_rfq_detail=cached_detail,
        )

        # Evidence Check — gate.
        evidence_stage.check_path_4(state)

        # Context Builder — defensive whitelist filter.
        context_stage.build_path_4(state)

        intent = state.plan.intent_topic
        use_compose = (
            intent in COMPOSE_ELIGIBLE_PATH4_INTENTS
            and self._llm_connector is not None
        )

        if use_compose:
            # ── Path 4 LLM Compose + Judge branch (Batch 8) ──
            # Compose drafts; we promote draft to final_text so the
            # deterministic guardrails (the safety floor) inspect the
            # actual user-facing answer; then Judge verifies grounding.
            # Single guardrail run — Judge runs after, on the same text.
            compose_stage.compose_path_4(state, self._llm_connector)
            state.final_text = state.draft_text
            guardrails_stage.run_path_4_guardrails(state)
            judge_stage.judge_path_4(state, self._llm_connector)
            return

        # ── Deterministic Path 4 renderer branch (default) ──
        rendered = path4_renderer.render_path_4(state)
        if rendered is None:
            # Shouldn't happen — Evidence Check passed but renderer
            # found nothing. Defensive: route to no_evidence.
            raise StageError(
                trigger="no_evidence",
                reason_code=ReasonCode("no_evidence"),
                source_stage="context_builder",
                details={"reason": "renderer returned None despite evidence check"},
            )
        state.final_text = rendered

        # Guardrails (Batch 7) — deterministic safety floor between
        # render and finalize. Any failure raises StageError; the
        # outer try/except in _handle_planner_path catches and routes
        # via the gate to a safe Path 8.5 template.
        guardrails_stage.run_path_4_guardrails(state)

    # ── Helpers ───────────────────────────────────────────────────────────

    def _init_state_for_failure(
        self,
        thread_id: str,  # noqa: ARG002 — reserved for future thread-aware forensics
        request: V2TurnRequest,
        actor: Actor,
    ) -> ExecutionState:
        """Build a placeholder ExecutionState for the gate to operate on
        when no plan was successfully built (e.g. LLM unavailable).

        We need a ``plan`` to satisfy the model; use a minimal Path 8.1
        placeholder that the gate immediately swaps out for the real
        Path 8.x plan via ``factory.build_from_escalation``.
        """
        # Use the gate's factory to build a minimal Path 8.1 placeholder.
        # This isn't elegant, but EscalationGate.route swaps state.plan
        # immediately, so the placeholder is only briefly attached.
        from src.models.execution_plan import EscalationRequest

        placeholder_plan = self._factory.build_from_escalation(
            EscalationRequest(
                target_path=PathId.PATH_8_1,
                reason_code=ReasonCode("unsupported_intent"),
                source_stage="orchestrator",
                trigger="placeholder_pre_routing",
            ),
            actor=actor,
        )
        return ExecutionState(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            plan=placeholder_plan,
            user_message=request.message,
            intake_path="planner",
        )

    def _init_state_from_failed_intake(
        self, thread_id: str, request: V2TurnRequest, actor: Actor, decision
    ) -> ExecutionState:
        """Build an ExecutionState for FastIntake-source failure cases
        (factory rejected the FastIntake decision — should be rare)."""
        from src.models.execution_plan import EscalationRequest

        placeholder_plan = self._factory.build_from_escalation(
            EscalationRequest(
                target_path=PathId.PATH_8_1,
                reason_code=ReasonCode("unsupported_intent"),
                source_stage="orchestrator",
                trigger="placeholder_pre_routing",
            ),
            actor=actor,
        )
        return ExecutionState(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            plan=placeholder_plan,
            user_message=request.message,
            intake_path="fast_intake",
            intake_decision=decision,
        )

    def _build_response(
        self,
        thread_id: str,
        state: ExecutionState,
        *,
        execution_record_id: str | None = None,
    ) -> V2TurnResponse:
        """Serialize the final state into the v2 response shape."""
        return V2TurnResponse(
            lane="v2",
            status="answered",
            thread_id=thread_id,
            answer=state.final_text or "",
            path=state.final_path.value if state.final_path else None,
            intent_topic=state.plan.intent_topic,
            reason_code=(
                str(state.plan.finalizer_reason_code)
                if state.plan.finalizer_reason_code is not None
                else None
            ),
            execution_record_id=execution_record_id,
        )

    # ── Unexpected-failure recovery + status derivation + persist ────────

    def _recover_unexpected_failure(
        self,
        thread_id: str,  # noqa: ARG002
        request: V2TurnRequest,
        actor: Actor,
    ) -> ExecutionState:
        """Build a Path 8.5 placeholder state for unexpected exceptions.

        Mirrors ``_init_state_for_failure`` but reaches a guaranteed
        Path 8.5 ``llm_unavailable`` plan via the factory's
        ``build_from_escalation`` (the most generic safe template).
        Used by ``handle_turn``'s outer try/except.
        """
        from src.models.execution_plan import EscalationRequest

        plan = self._factory.build_from_escalation(
            EscalationRequest(
                target_path=PathId.PATH_8_5,
                reason_code=ReasonCode("llm_unavailable"),
                source_stage="orchestrator",
                trigger="unexpected_pipeline_failure",
            ),
            actor=actor,
        )
        state = ExecutionState(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            plan=plan,
            user_message=request.message,
            intake_path="planner",
            registry_version=self._registry_version,
        )
        finalizer_stage.finalize(state)
        return state

    @staticmethod
    def _derive_status(
        state: ExecutionState, *, had_error: bool
    ) -> ExecutionRecordStatus:
        """Derive the persistence status from the final state shape.

        * unhandled exception caught by handle_turn -> ``failed``
        * any escalation fired -> ``escalated``
        * normal completion -> ``answered``
        """
        if had_error:
            return ExecutionRecordStatus.FAILED
        if state.escalations:
            return ExecutionRecordStatus.ESCALATED
        return ExecutionRecordStatus.ANSWERED

    def _persist(
        self,
        *,
        thread_id: str,
        state: ExecutionState,
        user_message: str,
        status: ExecutionRecordStatus,
        duration_ms: int,
        error_payload: dict | None,
    ) -> str | None:
        """Write the execution record. Returns the row id on success,
        ``None`` if persistence is unavailable (no session) or fails
        (production strict=False)."""
        if self._session is None:
            return None
        record = persist_stage.persist_execution_record(
            session=self._session,
            state=state,
            thread_id=thread_id,
            user_message=user_message,
            final_answer=state.final_text,
            status=status,
            duration_ms=duration_ms,
            error_payload=error_payload,
            strict=False,  # production: never break the user answer
        )
        return record.id if record is not None else None
