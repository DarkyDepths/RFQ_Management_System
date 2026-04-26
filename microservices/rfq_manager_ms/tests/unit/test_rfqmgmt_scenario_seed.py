from __future__ import annotations

import re
from collections import Counter
from datetime import date, timedelta

from scripts.seed_rfqmgmt_scenarios import (
    DASHBOARD_SEED_MARKER_PREFIX,
    GOLDEN_SCENARIO_KEY,
    SCENARIO_TAG_PREFIX,
    seeded_scenarios_for_batch,
    seed_manager_scenarios,
)
from src.models.reminder import Reminder
from src.models.rfq import RFQ
from src.models.rfq_file import RFQFile
from src.models.rfq_stage import RFQStage


def _rfq_by_scenario(db_session, scenario_key: str) -> RFQ:
    rfq = (
        db_session.query(RFQ)
        .filter(RFQ.description.like(f"{SCENARIO_TAG_PREFIX}{scenario_key}]%"))
        .first()
    )
    assert rfq is not None
    return rfq


def _stage_by_name(db_session, rfq_id, stage_name: str) -> RFQStage:
    stage = (
        db_session.query(RFQStage)
        .filter(RFQStage.rfq_id == rfq_id, RFQStage.name == stage_name)
        .first()
    )
    assert stage is not None
    return stage


def _files_for_rfq(db_session, rfq_id) -> list[RFQFile]:
    return (
        db_session.query(RFQFile)
        .join(RFQStage, RFQStage.id == RFQFile.rfq_stage_id)
        .filter(RFQStage.rfq_id == rfq_id, RFQFile.deleted_at.is_(None))
        .all()
    )


def test_must_have_batch_seeds_expected_scenarios_and_keeps_golden_manual(db_session):
    result = seed_manager_scenarios(db_session, batch="must-have")

    seeded_keys = {item["scenario_key"] for item in result["manifest"]["scenarios"]}
    assert {
        "RFQ-01",
        "RFQ-02",
        "RFQ-03",
        "RFQ-04",
        "RFQ-14",
        "RFQ-20",
        "RFQ-24",
        "RFQ-30",
        "RFQ-09",
        "RFQ-10",
        "RFQ-11",
    }.issubset(seeded_keys)
    assert len(seeded_keys) == 24
    assert GOLDEN_SCENARIO_KEY not in seeded_keys
    assert len(result["created_scenarios"]) == 24
    assert result["manifest"]["golden_reserved_scenario"] == GOLDEN_SCENARIO_KEY
    assert result["manifest"]["manual_reserved"] == [
        {
            "scenario_key": "RFQ-06",
            "name": "SWCC Pretreatment Dosing Package",
            "workflow_code": "GHI-LONG",
            "priority": "critical",
            "status": "In preparation",
            "summary": "Reserved manual-only golden journey. Never pre-seeded.",
            "manual_only": True,
        }
    ]
    verification_targets = result["manifest"]["verification_targets"]
    assert verification_targets["intelligence_snapshot_anchor"]["scenario_key"] == "RFQ-02"
    assert verification_targets["stale_snapshot_anchor"]["scenario_key"] == "RFQ-04"
    assert verification_targets["decision_wait_anchor"] == {
        "scenario_key": "RFQ-09",
        "rfq_id": verification_targets["decision_wait_anchor"]["rfq_id"],
        "status": "In preparation",
        "current_stage_name": "Award / Lost",
        "expected_status": "In preparation",
        "expected_current_stage_name": "Award / Lost",
    }
    assert verification_targets["workbook_artifact_anchor"]["scenario_key"] == "RFQ-09"
    assert "failed_workbook_anchor" not in verification_targets
    manifest_entry = next(item for item in result["manifest"]["scenarios"] if item["scenario_key"] == "RFQ-20")
    assert manifest_entry["family"] == "stale_execution"
    assert manifest_entry["file_count"] >= 1
    assert manifest_entry["subtask_count"] >= 1


def test_scenario_seed_rerun_is_idempotent_for_existing_batch(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    second = seed_manager_scenarios(db_session, batch="must-have")

    assert second["created_scenarios"] == []
    assert set(second["existing_scenarios"]) == {
        scenario.key for scenario in seeded_scenarios_for_batch("must-have")
    }
    assert len(second["manifest"]["scenarios"]) == 24


def test_later_and_optional_batches_only_seed_their_own_scenarios(db_session):
    later = seed_manager_scenarios(db_session, batch="later")
    later_keys = {item["scenario_key"] for item in later["manifest"]["scenarios"]}
    assert later_keys == {scenario.key for scenario in seeded_scenarios_for_batch("later")}
    assert len(later_keys) == 10
    assert later["manifest"]["verification_targets"]["failed_workbook_anchor"]["scenario_key"] == "RFQ-07"

    optional = seed_manager_scenarios(db_session, batch="optional")
    optional_keys = {item["scenario_key"] for item in optional["manifest"]["scenarios"]}
    assert optional_keys == {
        *(scenario.key for scenario in seeded_scenarios_for_batch("later")),
        *(scenario.key for scenario in seeded_scenarios_for_batch("optional")),
    }
    assert len(optional_keys) == 16


def test_all_batch_contains_full_portfolio_plus_manual_reservation(db_session):
    result = seed_manager_scenarios(db_session, batch="all")

    seeded_keys = {item["scenario_key"] for item in result["manifest"]["scenarios"]}
    workflow_codes = {item["workflow_code"] for item in result["manifest"]["scenarios"]}

    assert len(seeded_keys) == 40
    assert "RFQ-41" in seeded_keys
    assert GOLDEN_SCENARIO_KEY not in seeded_keys
    assert "GHI-CUSTOM" in workflow_codes


def test_dashboard_batch_seeds_120_rfqs_with_dashboard_extension_delta(db_session):
    result = seed_manager_scenarios(db_session, batch="dashboard")

    entries = result["manifest"]["scenarios"]
    seeded_keys = {item["scenario_key"] for item in entries}
    dashboard_entries = [
        item for item in entries if item["scenario_key"].startswith("DASH-D")
    ]

    assert len(entries) == 120
    assert len(dashboard_entries) == 86
    assert GOLDEN_SCENARIO_KEY not in seeded_keys
    assert {item["scenario_key"] for item in dashboard_entries} == {
        f"DASH-D{index:03d}" for index in range(1, 87)
    }

    assert Counter(item["status"] for item in entries) == {
        "In preparation": 75,
        "Awarded": 20,
        "Lost": 17,
        "Cancelled": 8,
    }
    assert Counter(item["priority"] for item in entries) == {
        "normal": 76,
        "critical": 44,
    }
    assert Counter(item["workflow_code"] for item in entries) == {
        "GHI-LONG": 72,
        "GHI-SHORT": 42,
        "GHI-CUSTOM": 6,
    }
    assert Counter(item["client"] for item in dashboard_entries) == {
        "Saudi Aramco": 16,
        "Saudi Electricity Company": 12,
        "SABIC": 11,
        "Maaden": 9,
        "NEOM": 8,
        "SWCC": 8,
        "Royal Commission Jubail": 6,
        "PetroRabigh": 6,
        "Yasref": 5,
        "Sadara": 5,
    }

    summary = result["seed_summary"]
    assert summary["total_rfqs"] == 120
    assert summary["blocked_active_rfqs"] >= 24
    assert summary["overdue_active_rfqs"] >= 26
    assert summary["awarded_count"] == 20
    assert summary["lost_count"] == 17
    assert summary["cancelled_count"] == 8
    assert summary["terminal_rfqs_with_current_stage_id_null_and_progress_100"] == 45

    repeated_clients = [
        client
        for client, count in Counter(item["client"] for item in dashboard_entries).items()
        if count > 1
    ]
    assert len(repeated_clients) == 10
    assert len(Counter(item["owner"] for item in entries)) >= 8


def test_dashboard_seed_is_idempotent_and_uses_markers_not_runtime_codes(db_session):
    first = seed_manager_scenarios(db_session, batch="dashboard")
    second = seed_manager_scenarios(db_session, batch="dashboard")

    assert len(first["created_scenarios"]) == 120
    assert second["created_scenarios"] == []
    assert set(second["existing_scenarios"]) == {
        scenario.key for scenario in seeded_scenarios_for_batch("dashboard")
    }
    assert db_session.query(RFQ).count() == 120

    dashboard_entries = [
        item
        for item in second["manifest"]["scenarios"]
        if item["scenario_key"].startswith("DASH-D")
    ]
    assert dashboard_entries
    assert all(
        item["seed_marker"] == f"{DASHBOARD_SEED_MARKER_PREFIX}{item['scenario_key']}]"
        for item in dashboard_entries
    )
    assert all(item["seed_marker"] in item["description"] for item in dashboard_entries)
    assert all(
        re.match(r"^(IF|IB)-\d{4}$", item["rfq_code"])
        for item in second["manifest"]["scenarios"]
    )


def test_dashboard_seed_keeps_terminal_rfqs_consistent_and_api_smoke(db_session, client):
    seed_manager_scenarios(db_session, batch="dashboard")

    terminal_rfqs = (
        db_session.query(RFQ)
        .filter(RFQ.status.in_(["Awarded", "Lost", "Cancelled"]))
        .all()
    )
    assert len(terminal_rfqs) == 45
    assert all(rfq.current_stage_id is None for rfq in terminal_rfqs)
    assert all(rfq.progress == 100 for rfq in terminal_rfqs)

    health = client.get("/health")
    stats = client.get("/rfq-manager/v1/rfqs/stats")
    analytics = client.get("/rfq-manager/v1/rfqs/analytics")
    listing = client.get("/rfq-manager/v1/rfqs?page=1&size=100")

    assert health.status_code == 200
    assert stats.status_code == 200
    assert analytics.status_code == 200
    assert listing.status_code == 200
    assert stats.json()["total_rfqs_12m"] == 120
    assert stats.json()["open_rfqs"] == 75
    assert analytics.json()["win_rate"] == 54.1
    assert listing.json()["total"] == 120
    assert len(listing.json()["data"]) == 100


def test_blocked_overdue_scenario_has_expected_operational_pressure(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    rfq = _rfq_by_scenario(db_session, "RFQ-03")
    stage = _stage_by_name(db_session, rfq.id, "Pre-bid clarifications")
    reminders = db_session.query(Reminder).filter(Reminder.rfq_id == rfq.id).all()

    assert rfq.status == "In preparation"
    assert rfq.priority == "critical"
    assert rfq.deadline < date.today()
    assert rfq.current_stage_id == stage.id

    assert stage.status == "In Progress"
    assert stage.blocker_status == "Blocked"
    assert stage.blocker_reason_code == "waiting_client_docs"

    assert len(reminders) == 3
    assert {reminder.status for reminder in reminders} == {"open", "overdue"}
    assert any(reminder.send_count == 1 for reminder in reminders)


def test_tight_future_scenario_keeps_its_intended_deadline_after_safe_seed_create(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    rfq = _rfq_by_scenario(db_session, "RFQ-04")

    assert rfq.deadline == date.today() + timedelta(days=14)


def test_seeded_active_rfq_progress_reflects_lifecycle_completion_not_stage_workload(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    rfq = _rfq_by_scenario(db_session, "RFQ-04")

    assert rfq.progress == 27


def test_early_intelligence_anchor_has_source_package_file(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    rfq = _rfq_by_scenario(db_session, "RFQ-02")
    files = _files_for_rfq(db_session, rfq.id)

    assert any(file.type == "Client RFQ" for file in files)
    assert any(file.filename == "client-rfq-source-package.zip" for file in files)


def test_decision_wait_anchor_has_package_and_workbook_files(db_session):
    seed_manager_scenarios(db_session, batch="must-have")

    rfq = _rfq_by_scenario(db_session, "RFQ-09")
    files = _files_for_rfq(db_session, rfq.id)
    file_types = {file.type for file in files}

    assert "Client RFQ" in file_types
    assert "Estimation Workbook" in file_types


def test_cost_estimation_in_progress_scenario_keeps_package_without_workbook(db_session):
    seed_manager_scenarios(db_session, batch="later")

    rfq = _rfq_by_scenario(db_session, "RFQ-05")
    files = _files_for_rfq(db_session, rfq.id)
    file_types = {file.type for file in files}

    assert "Client RFQ" in file_types
    assert "Estimation Workbook" not in file_types
