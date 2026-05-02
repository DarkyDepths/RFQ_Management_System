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
import uuid

from src.connectors.llm_connector import LlmConnector
from src.connectors.manager_ms_connector import ManagerConnector
from src.models.actor import Actor
from src.models.execution_plan import FactoryRejection
from src.models.execution_state import ExecutionState
from src.models.path_registry import PathId, ReasonCode
from src.models.planner_proposal import (
    ValidatedPlannerProposal,
    ValidationRejection,
)
from src.models.v2_turn import V2TurnRequest, V2TurnResponse
from src.pipeline import (
    access as access_stage,
    context_builder as context_stage,
    evidence_check as evidence_stage,
    execution_state as exec_state_helpers,
    fast_intake,
    finalizer as finalizer_stage,
    path4_renderer,
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

    # ── Public entry ──────────────────────────────────────────────────────

    def handle_turn(
        self,
        *,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
    ) -> V2TurnResponse:
        """Run the pipeline; return the v2 response on success.

        On any failure that the pipeline can recover from (StageError,
        LlmUnreachable, FactoryRejection, ValidationRejection), the
        Escalation Gate routes to a Path 8.x plan and we still return
        a 200 success with the safe template answer. True 500s only
        for the truly-unrecovered case (gate failed AND finalizer
        crashed).
        """
        # Stage 0 — FastIntake.
        decision = fast_intake.try_match(request.message)
        if decision is not None:
            return self._handle_fast_intake_hit(thread_id, request, actor, decision)

        # FastIntake miss — proceed to Planner-based pipeline.
        return self._handle_planner_path(thread_id, request, actor)

    # ── FastIntake hit branch ─────────────────────────────────────────────

    def _handle_fast_intake_hit(
        self,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
        decision,
    ) -> V2TurnResponse:
        plan_or_rejection = self._factory.build_from_intake(
            decision=decision, actor=actor
        )
        if isinstance(plan_or_rejection, FactoryRejection):
            # Should not happen for declared FastIntake patterns.
            logger.error(
                "FastIntake -> factory rejection for %s/%s: %s",
                decision.path.value, decision.intent_topic, plan_or_rejection.trigger,
            )
            # Build a minimal state with a stand-in Path 8.1 plan and
            # finalize a generic unsupported template.
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
            return self._build_response(thread_id, state)

        plan = plan_or_rejection
        state = exec_state_helpers.init_state_from_intake(
            turn_id=str(uuid.uuid4()),
            actor=actor,
            user_message=request.message,
            plan=plan,
            decision=decision,
        )
        finalizer_stage.finalize(state)
        return self._build_response(thread_id, state)

    # ── Planner branch ────────────────────────────────────────────────────

    def _handle_planner_path(
        self,
        thread_id: str,
        request: V2TurnRequest,
        actor: Actor,
    ) -> V2TurnResponse:
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
            return self._build_response(thread_id, state)

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
            return self._build_response(thread_id, state)

        # ── PlannerValidator.validate ──
        validated_or_rejection = self._validator.validate(proposal)
        if isinstance(validated_or_rejection, ValidationRejection):
            state = self._init_state_for_failure(thread_id, request, actor)
            self._gate.route(
                state,
                trigger=validated_or_rejection.trigger,
                reason_code=validated_or_rejection.reason_code,
                source_stage="validator",
                details={"rule_number": validated_or_rejection.rule_number},
            )
            finalizer_stage.finalize(state)
            return self._build_response(thread_id, state)
        validated: ValidatedPlannerProposal = validated_or_rejection

        # ── ExecutionPlanFactory.build_from_planner ──
        plan_or_rejection = self._factory.build_from_planner(validated, actor=actor)
        if isinstance(plan_or_rejection, FactoryRejection):
            state = self._init_state_for_failure(thread_id, request, actor)
            self._gate.route(
                state,
                trigger=plan_or_rejection.trigger,
                reason_code=plan_or_rejection.reason_code,
                source_stage="factory",
                details={"factory_rule": plan_or_rejection.factory_rule},
            )
            finalizer_stage.finalize(state)
            return self._build_response(thread_id, state)
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
        return self._build_response(thread_id, state)

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

        # Path 4 Renderer — deterministic grounded answer.
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
        self, thread_id: str, state: ExecutionState
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
        )
