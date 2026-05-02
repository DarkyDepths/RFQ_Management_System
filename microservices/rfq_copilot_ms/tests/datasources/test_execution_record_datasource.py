"""Datasource tests for execution_records (Batch 6).

Pure DB writes/reads — no manager, no LLM, no pipeline. Uses the
shared ``db_session`` fixture from conftest (in-memory SQLite).
"""

from __future__ import annotations

import time

from src.datasources.execution_record_datasource import (
    ExecutionRecordDatasource,
)
from src.models.execution_record import (
    ExecutionRecordCreate,
    ExecutionRecordStatus,
)


def _payload(
    *,
    thread_id: str = "thread-1",
    turn_id: str = "turn-1",
    status: ExecutionRecordStatus = ExecutionRecordStatus.ANSWERED,
    user_message: str = "what is the deadline for IF-0001?",
    final_answer: str | None = "IF-0001 deadline is 2026-06-15.",
    path: str | None = "path_4",
    intent_topic: str | None = "deadline",
    intake_source: str | None = "planner",
    reason_code: str | None = None,
    target_rfq_code: str | None = "IF-0001",
    duration_ms: int | None = 42,
    tool_invocations_json: list | None = None,
    evidence_refs_json: list | None = None,
    escalations_json: list | None = None,
    error_json: dict | None = None,
) -> ExecutionRecordCreate:
    return ExecutionRecordCreate(
        thread_id=thread_id,
        turn_id=turn_id,
        status=status,
        user_message=user_message,
        final_answer=final_answer,
        path=path,
        intent_topic=intent_topic,
        intake_source=intake_source,
        reason_code=reason_code,
        target_rfq_code=target_rfq_code,
        duration_ms=duration_ms,
        tool_invocations_json=tool_invocations_json or [],
        evidence_refs_json=evidence_refs_json or [],
        escalations_json=escalations_json or [],
        error_json=error_json,
    )


# ── 1. create writes a row ───────────────────────────────────────────────


def test_create_writes_row(db_session):
    ds = ExecutionRecordDatasource(db_session)
    written = ds.create(_payload())
    assert written.id  # non-empty UUID
    assert written.thread_id == "thread-1"
    assert written.turn_id == "turn-1"
    assert written.status == ExecutionRecordStatus.ANSWERED
    assert written.path == "path_4"
    assert written.target_rfq_code == "IF-0001"
    assert written.duration_ms == 42
    assert written.created_at is not None


# ── 2. get_by_turn_id ─────────────────────────────────────────────────────


def test_get_by_turn_id_returns_row(db_session):
    ds = ExecutionRecordDatasource(db_session)
    written = ds.create(_payload(turn_id="turn-xyz"))
    fetched = ds.get_by_turn_id("turn-xyz")
    assert fetched is not None
    assert fetched.id == written.id
    assert fetched.path == "path_4"


def test_get_by_turn_id_returns_none_for_unknown(db_session):
    ds = ExecutionRecordDatasource(db_session)
    assert ds.get_by_turn_id("missing-turn") is None


def test_get_by_id_round_trip(db_session):
    ds = ExecutionRecordDatasource(db_session)
    written = ds.create(_payload())
    fetched = ds.get_by_id(written.id)
    assert fetched is not None
    assert fetched.turn_id == written.turn_id


# ── 3. list_by_thread_id ordering ─────────────────────────────────────────


def test_list_by_thread_id_returns_newest_first(db_session):
    ds = ExecutionRecordDatasource(db_session)
    ds.create(_payload(thread_id="t1", turn_id="turn-1"))
    time.sleep(0.01)  # ensure created_at differs
    ds.create(_payload(thread_id="t1", turn_id="turn-2"))
    time.sleep(0.01)
    ds.create(_payload(thread_id="t1", turn_id="turn-3"))
    rows = ds.list_by_thread_id("t1")
    assert [r.turn_id for r in rows] == ["turn-3", "turn-2", "turn-1"]


def test_list_by_thread_id_filters_by_thread(db_session):
    ds = ExecutionRecordDatasource(db_session)
    ds.create(_payload(thread_id="t1", turn_id="turn-1"))
    ds.create(_payload(thread_id="t2", turn_id="turn-2"))
    rows = ds.list_by_thread_id("t1")
    assert len(rows) == 1
    assert rows[0].turn_id == "turn-1"


def test_list_by_thread_id_respects_limit(db_session):
    ds = ExecutionRecordDatasource(db_session)
    for i in range(5):
        ds.create(_payload(thread_id="t1", turn_id=f"turn-{i}"))
    rows = ds.list_by_thread_id("t1", limit=3)
    assert len(rows) == 3


# ── 4. JSON round-trip ────────────────────────────────────────────────────


def test_json_fields_round_trip(db_session):
    ds = ExecutionRecordDatasource(db_session)
    payload = _payload(
        tool_invocations_json=[
            {"tool_name": "get_rfq_profile", "args": {"rfq_code": "IF-0001"},
             "latency_ms": 12, "status": "ok"},
        ],
        evidence_refs_json=[
            {"target_label": "IF-0001", "field_keys": ["deadline"],
             "source_refs": [{"source_type": "manager",
                              "source_id": "get_rfq_profile:IF-0001"}]},
        ],
        escalations_json=[
            {"trigger": "manager_unreachable", "reason_code": "source_unavailable",
             "source_stage": "tool_executor"},
        ],
    )
    written = ds.create(payload)
    fetched = ds.get_by_id(written.id)
    assert fetched is not None
    assert fetched.tool_invocations_json[0]["tool_name"] == "get_rfq_profile"
    assert fetched.evidence_refs_json[0]["target_label"] == "IF-0001"
    assert fetched.escalations_json[0]["trigger"] == "manager_unreachable"


# ── 5. Datasource has no manager / LLM dependencies ──────────────────────


def test_datasource_has_no_manager_llm_imports():
    """AST guard: src/datasources/execution_record_datasource.py must
    not import any manager / LLM module."""
    import ast
    import inspect
    from pathlib import Path

    from src.datasources import execution_record_datasource as ds_module

    src_path = Path(inspect.getfile(ds_module)).resolve()
    tree = ast.parse(src_path.read_text(encoding="utf-8"))
    forbidden = {
        "src.connectors.llm_connector",
        "src.connectors.manager_ms_connector",
        "openai", "anthropic", "httpx", "requests",
    }
    leaked = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            top_level = node.module.split(".")[0]
            if node.module in forbidden or top_level in forbidden:
                leaked.append(node.module)
    assert not leaked, (
        f"Datasource imports forbidden modules: {leaked}. "
        f"It must be a pure DB layer."
    )


# ── 6. Status persisted as string ─────────────────────────────────────────


def test_escalated_status_persists(db_session):
    ds = ExecutionRecordDatasource(db_session)
    written = ds.create(_payload(
        status=ExecutionRecordStatus.ESCALATED,
        path="path_8_5",
        reason_code="source_unavailable",
        final_answer="The data source I needed isn't reachable right now.",
    ))
    fetched = ds.get_by_id(written.id)
    assert fetched.status == ExecutionRecordStatus.ESCALATED
    assert fetched.reason_code == "source_unavailable"


def test_failed_status_with_error_json_persists(db_session):
    ds = ExecutionRecordDatasource(db_session)
    written = ds.create(_payload(
        status=ExecutionRecordStatus.FAILED,
        error_json={"type": "ValueError", "message": "unmapped trigger"},
    ))
    fetched = ds.get_by_id(written.id)
    assert fetched.status == ExecutionRecordStatus.FAILED
    assert fetched.error_json["type"] == "ValueError"
