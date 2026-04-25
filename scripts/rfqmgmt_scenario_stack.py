from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from pathlib import PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
MANAGER_DIR = ROOT / "microservices" / "rfq_manager_ms"
INTELLIGENCE_DIR = ROOT / "microservices" / "rfq_intelligence_ms"
MANAGER_COMPOSE = MANAGER_DIR / "docker-compose.scenario.yml"
INTELLIGENCE_COMPOSE = INTELLIGENCE_DIR / "docker-compose.scenario.yml"
SEED_OUTPUT_DIR = ROOT / "seed_outputs"
MANAGER_MANIFEST = SEED_OUTPUT_DIR / "rfqmgmt_manager_manifest.json"
INTELLIGENCE_MANIFEST = SEED_OUTPUT_DIR / "rfqmgmt_intelligence_manifest.json"
CONTAINER_SEED_OUTPUT_DIR = PurePosixPath("/app/seed_outputs")
CONTAINER_MANAGER_MANIFEST = CONTAINER_SEED_OUTPUT_DIR / "rfqmgmt_manager_manifest.json"
CONTAINER_INTELLIGENCE_MANIFEST = CONTAINER_SEED_OUTPUT_DIR / "rfqmgmt_intelligence_manifest.json"

MANAGER_DB_URL = "postgresql+psycopg2://rfq_user:changeme@localhost:15432/rfq_manager_scenario_db"
INTELLIGENCE_DB_URL = (
    "postgresql+psycopg2://intelligence_user:intelligence_pass@localhost:15433/rfq_intelligence_scenario_db"
)
MANAGER_BASE_URL = "http://localhost:18000"
INTELLIGENCE_BASE_URL = "http://localhost:18001"
MANAGER_PROJECT = "rfq-manager-scenario"
INTELLIGENCE_PROJECT = "rfq-intelligence-scenario"


def _run(cmd: list[str], *, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    print(f"[run] {' '.join(cmd)}")
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=merged_env, check=True)


def _read_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _wait_for_health(url: str, *, timeout_seconds: int = 240) -> None:
    deadline = time.time() + timeout_seconds
    last_error = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200:
                    print(f"[health] {url} is healthy")
                    return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(3)
    raise RuntimeError(f"Timed out waiting for health at {url}. Last error: {last_error}")


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _require_verification_target(manager_manifest: dict, role: str) -> dict:
    target = manager_manifest.get("verification_targets", {}).get(role)
    if target is None:
        raise RuntimeError(f"Manager manifest is missing verification target '{role}'.")
    return target


def _manager_compose(*args: str) -> None:
    _run(
        ["docker", "compose", "-p", MANAGER_PROJECT, "-f", str(MANAGER_COMPOSE), *args],
        cwd=MANAGER_DIR,
    )


def _intelligence_compose(*args: str) -> None:
    _run(
        ["docker", "compose", "-p", INTELLIGENCE_PROJECT, "-f", str(INTELLIGENCE_COMPOSE), *args],
        cwd=INTELLIGENCE_DIR,
    )


def _manager_exec(*args: str) -> None:
    _run(
        ["docker", "compose", "-p", MANAGER_PROJECT, "-f", str(MANAGER_COMPOSE), "exec", "-T", "api", *args],
        cwd=MANAGER_DIR,
    )


def _intelligence_exec(*args: str) -> None:
    _run(
        [
            "docker",
            "compose",
            "-p",
            INTELLIGENCE_PROJECT,
            "-f",
            str(INTELLIGENCE_COMPOSE),
            "exec",
            "-T",
            "intelligence_api",
            *args,
        ],
        cwd=INTELLIGENCE_DIR,
    )


def up_stack() -> None:
    _manager_compose("up", "-d", "--build")
    _intelligence_compose("up", "-d", "--build")
    _wait_for_health(f"{MANAGER_BASE_URL}/health")
    _wait_for_health(f"{INTELLIGENCE_BASE_URL}/health")


def down_stack(*, remove_volumes: bool) -> None:
    manager_args = ["down"]
    intelligence_args = ["down"]
    if remove_volumes:
        manager_args.append("-v")
        intelligence_args.append("-v")
    _intelligence_compose(*intelligence_args)
    _manager_compose(*manager_args)


def seed_stack(*, seed_set: str) -> None:
    SEED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _manager_exec(
        "python",
        "scripts/seed_rfqmgmt_scenarios.py",
        "--batch",
        "must-have",
        "--manifest-out",
        str(CONTAINER_MANAGER_MANIFEST),
    )

    if seed_set in {"full", "full-plus-optional"}:
        _manager_exec(
            "python",
            "scripts/seed_rfqmgmt_scenarios.py",
            "--batch",
            "later",
            "--manifest-out",
            str(CONTAINER_MANAGER_MANIFEST),
        )

    if seed_set == "full-plus-optional":
        _manager_exec(
            "python",
            "scripts/seed_rfqmgmt_scenarios.py",
            "--batch",
            "optional",
            "--manifest-out",
            str(CONTAINER_MANAGER_MANIFEST),
        )

    _intelligence_exec(
        "python",
        "scripts/seed_rfqmgmt_intelligence.py",
        "--manager-manifest",
        str(CONTAINER_MANAGER_MANIFEST),
        "--output-json",
        str(CONTAINER_INTELLIGENCE_MANIFEST),
    )


def verify_stack(*, seed_set: str) -> dict:
    manager_manifest = _load_json(MANAGER_MANIFEST)
    intelligence_manifest = _load_json(INTELLIGENCE_MANIFEST)
    scenario_map = {item["scenario_key"]: item for item in manager_manifest["scenarios"]}

    manager_health = _read_json(f"{MANAGER_BASE_URL}/health")
    intelligence_health = _read_json(f"{INTELLIGENCE_BASE_URL}/health")
    manager_stats = _read_json(f"{MANAGER_BASE_URL}/rfq-manager/v1/rfqs/stats")
    manager_list = _read_json(f"{MANAGER_BASE_URL}/rfq-manager/v1/rfqs?page=1&size=20")

    expected_total = 7 if seed_set == "must-have" else 10 if seed_set == "full" else 12
    if manager_stats["total_rfqs_12m"] < expected_total:
        raise RuntimeError(
            f"Scenario stack verification failed: expected at least {expected_total} RFQs, "
            f"got {manager_stats['total_rfqs_12m']}."
        )

    snapshot_anchor = _require_verification_target(manager_manifest, "intelligence_snapshot_anchor")
    stale_snapshot_anchor = _require_verification_target(manager_manifest, "stale_snapshot_anchor")
    decision_wait_anchor = _require_verification_target(manager_manifest, "decision_wait_anchor")
    workbook_anchor = _require_verification_target(manager_manifest, "workbook_artifact_anchor")

    rfq09_detail = _read_json(f"{MANAGER_BASE_URL}/rfq-manager/v1/rfqs/{decision_wait_anchor['rfq_id']}")
    rfq02_snapshot = _read_json(f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{snapshot_anchor['rfq_id']}/snapshot")
    rfq04_snapshot = _read_json(
        f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{stale_snapshot_anchor['rfq_id']}/snapshot"
    )
    rfq09_profile = _read_json(
        f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{workbook_anchor['rfq_id']}/workbook-profile"
    )
    rfq09_review = _read_json(
        f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{workbook_anchor['rfq_id']}/workbook-review"
    )
    rfq09_artifacts = _read_json(
        f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{workbook_anchor['rfq_id']}/artifacts"
    )

    rfq04_snapshot_updated = rfq04_snapshot.get("updated_at")
    rfq04_manager_updated = stale_snapshot_anchor.get("updated_at") or scenario_map.get(
        stale_snapshot_anchor["scenario_key"], {}
    ).get("updated_at")
    stale_ok = bool(rfq04_snapshot_updated and rfq04_manager_updated and rfq04_snapshot_updated < rfq04_manager_updated)

    workbook_failure_status = None
    workbook_failure_review_status = None
    failed_workbook_anchor = manager_manifest.get("verification_targets", {}).get("failed_workbook_anchor")
    if seed_set in {"full", "full-plus-optional"} and failed_workbook_anchor:
        rfq07_snapshot = _read_json(
            f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{failed_workbook_anchor['rfq_id']}/snapshot"
        )
        workbook_failure_status = rfq07_snapshot["content"]["workbook_panel"]["parser_status"]
        try:
            urllib.request.urlopen(
                f"{INTELLIGENCE_BASE_URL}/intelligence/v1/rfqs/{failed_workbook_anchor['rfq_id']}/workbook-review",
                timeout=10,
            )
            workbook_failure_review_status = "unexpected_200"
        except urllib.error.HTTPError as exc:
            workbook_failure_review_status = exc.code

    if rfq09_detail["status"] != decision_wait_anchor.get("expected_status"):
        raise RuntimeError(
            f"Expected {decision_wait_anchor['scenario_key']} to remain {decision_wait_anchor.get('expected_status')} "
            f"while awaiting decision, got {rfq09_detail['status']}"
        )
    if rfq09_detail.get("current_stage_name") != decision_wait_anchor.get("expected_current_stage_name"):
        raise RuntimeError(
            f"Expected {decision_wait_anchor['scenario_key']} to sit in the final "
            f"{decision_wait_anchor.get('expected_current_stage_name')} stage while awaiting outcome."
        )
    if rfq02_snapshot["artifact_type"] != snapshot_anchor.get("expected_snapshot_artifact_type"):
        raise RuntimeError(
            f"{snapshot_anchor['scenario_key']} snapshot endpoint did not return "
            f"{snapshot_anchor.get('expected_snapshot_artifact_type')}."
        )
    if stale_snapshot_anchor.get("expected_snapshot_stale_relative_to_manager") and not stale_ok:
        raise RuntimeError(
            f"Expected {stale_snapshot_anchor['scenario_key']} intelligence snapshot to remain older than manager truth."
        )
    if rfq09_profile["artifact_type"] != workbook_anchor.get("expected_profile_artifact_type"):
        raise RuntimeError(
            f"{workbook_anchor['scenario_key']} workbook profile endpoint did not return "
            f"{workbook_anchor.get('expected_profile_artifact_type')}."
        )
    if rfq09_review["artifact_type"] != workbook_anchor.get("expected_review_artifact_type"):
        raise RuntimeError(
            f"{workbook_anchor['scenario_key']} workbook review endpoint did not return "
            f"{workbook_anchor.get('expected_review_artifact_type')}."
        )
    if workbook_anchor.get("requires_artifacts") and not rfq09_artifacts.get("artifacts"):
        raise RuntimeError(f"{workbook_anchor['scenario_key']} artifacts endpoint returned no artifacts.")
    if (
        failed_workbook_anchor
        and workbook_failure_review_status is not None
        and workbook_failure_review_status != failed_workbook_anchor.get("expected_workbook_review_http_status")
    ):
        raise RuntimeError(
            f"Expected {failed_workbook_anchor['scenario_key']} workbook review endpoint to return "
            f"{failed_workbook_anchor.get('expected_workbook_review_http_status')}, "
            f"got {workbook_failure_review_status}."
        )

    summary = {
        "manager_health": manager_health,
        "intelligence_health": intelligence_health,
        "manager_stats": manager_stats,
        "listed_rfq_count_page_1": len(manager_list.get("data", [])),
        "seeded_scenarios": [item["scenario_key"] for item in intelligence_manifest["seeded"]],
        "verification_targets": sorted(manager_manifest.get("verification_targets", {}).keys()),
        "rfq04_stale_snapshot_ok": stale_ok,
        "rfq07_parser_status": workbook_failure_status,
        "rfq07_workbook_review_status": workbook_failure_review_status,
        "ui_env": {
            "NEXT_PUBLIC_USE_MOCK_DATA": "false",
            "NEXT_PUBLIC_MANAGER_API_URL": MANAGER_BASE_URL,
            "NEXT_PUBLIC_INTELLIGENCE_API_URL": INTELLIGENCE_BASE_URL,
        },
    }
    print(json.dumps(summary, indent=2))
    return summary


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Manage the parallel RFQMGMT scenario stack without touching the current containers.",
    )
    parser.add_argument(
        "command",
        choices=["up", "seed", "verify", "all", "down"],
        help="Lifecycle command to run against the scenario stack.",
    )
    parser.add_argument(
        "--seed-set",
        choices=["must-have", "full", "full-plus-optional"],
        default="full",
        help="Which scenario set to seed. 'full' = must-have + later, without optional edge-only scenarios.",
    )
    parser.add_argument(
        "--remove-volumes",
        action="store_true",
        help="When used with 'down', also remove the scenario stack volumes.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "up":
        up_stack()
    elif args.command == "seed":
        seed_stack(seed_set=args.seed_set)
    elif args.command == "verify":
        verify_stack(seed_set=args.seed_set)
    elif args.command == "all":
        up_stack()
        seed_stack(seed_set=args.seed_set)
        verify_stack(seed_set=args.seed_set)
    elif args.command == "down":
        down_stack(remove_volumes=args.remove_volumes)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
