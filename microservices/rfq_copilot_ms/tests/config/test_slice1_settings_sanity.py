"""Slice 1 settings + boot sanity (Batch 9).

These tests pin the contract that:

* The required env vars exist on the Settings model with expected types.
* The app boots when Azure config is absent (FastIntake-only mode).
* The DI surface returns ``None`` for the planner when Azure is absent
  rather than raising.
* No real secrets are hardcoded in source files we control.

They DO NOT test runtime behavior — that's covered by the smoke suite.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


# ── 1. Settings model exposes the required env vars ─────────────────────


def test_settings_exposes_manager_base_url():
    from src.config.settings import Settings
    assert "MANAGER_BASE_URL" in Settings.model_fields


def test_settings_exposes_azure_openai_fields():
    from src.config.settings import Settings
    fields = Settings.model_fields
    for required in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_VERSION",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        "AZURE_OPENAI_TIMEOUT_SECONDS",
    ):
        assert required in fields, f"Settings must declare {required}"


def test_settings_exposes_database_url():
    from src.config.settings import Settings
    assert "DATABASE_URL" in Settings.model_fields


# ── 2. Declared defaults are safe — empty-by-default for credentials ────


def test_credential_fields_declared_defaults_are_empty():
    """The model's *declared* defaults for credentials must be empty
    strings — production deployments must opt in by setting env vars,
    not opt out by overriding bakes-in. We assert against
    ``model_fields[...].default`` so the test is independent of any
    ``.env`` file the local dev environment happens to have."""
    from src.config.settings import Settings
    fields = Settings.model_fields
    for name in (
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_CHAT_DEPLOYMENT",
        # MANAGER_BASE_URL has no safe default — must be explicitly set.
        "MANAGER_BASE_URL",
    ):
        assert fields[name].default == "", (
            f"{name} declared default must be the empty string "
            f"(got {fields[name].default!r}). Production must opt in "
            f"explicitly via env var, never inherit a baked-in value."
        )


# ── 3. App boots without Azure configured ───────────────────────────────


def _force_azure_unconfigured(monkeypatch) -> None:
    """Simulate "Azure not configured" by zeroing the *runtime* settings
    attributes that the connectors actually read, plus resetting the
    DI singletons so providers re-evaluate.

    Patching env vars alone isn't enough — the module-level ``settings``
    object is constructed at import time and may already carry values
    from a developer's local .env. The connectors read attributes on
    that singleton, so we patch the singleton directly.
    """
    from src.config import settings as settings_module
    from src import app_context

    monkeypatch.setattr(settings_module.settings, "AZURE_OPENAI_API_KEY", "")
    monkeypatch.setattr(settings_module.settings, "AZURE_OPENAI_ENDPOINT", "")
    monkeypatch.setattr(
        settings_module.settings, "AZURE_OPENAI_CHAT_DEPLOYMENT", ""
    )
    monkeypatch.setattr(app_context, "_planner", None)
    monkeypatch.setattr(app_context, "_planner_init_attempted", False)
    monkeypatch.setattr(app_context, "_llm_connector", None)


def test_app_boots_without_azure(monkeypatch):
    """Importing the app and creating a TestClient must not raise even
    when Azure env vars are unset. This is the FastIntake-only mode
    Slice 1 supports."""
    _force_azure_unconfigured(monkeypatch)

    # Importing must succeed.
    from src.app import app  # noqa: F401

    # Hitting health doesn't depend on Azure.
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200


# ── 4. get_planner returns None when Azure is absent ────────────────────


def test_get_planner_returns_none_when_azure_unconfigured(monkeypatch):
    """The DI provider must NOT raise when Azure isn't configured —
    it returns None and the V2TurnController routes appropriately
    to Path 8.5 llm_unavailable for non-FastIntake messages."""
    _force_azure_unconfigured(monkeypatch)
    from src import app_context
    assert app_context.get_planner() is None


def test_get_llm_connector_optional_returns_none_without_azure(monkeypatch):
    """Mirror of get_planner — the optional LLM provider used by the
    Compose+Judge wiring must also return None gracefully."""
    _force_azure_unconfigured(monkeypatch)
    from src import app_context
    assert app_context.get_llm_connector_optional() is None


# ── 5. FastIntake works without Azure (end-to-end) ──────────────────────


def test_fastintake_works_without_azure(monkeypatch):
    """End-to-end: with Azure unset, FastIntake messages must still
    answer with their templates (no Planner consulted)."""
    _force_azure_unconfigured(monkeypatch)
    from src.app import app

    client = TestClient(app)
    r = client.post(
        "/rfq-copilot/v2/threads/t1/turn",
        json={"message": "hello"},
    )
    # FastIntake hits before any Azure-dependent stage.
    assert r.status_code == 200
    assert r.json()["path"] == "path_1"


# ── 6. No hardcoded secrets in source we control ────────────────────────


_REPO_ROOT = Path(__file__).resolve().parents[2]
"""Points at microservices/rfq_copilot_ms/."""


def _scan_files(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    out = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix not in suffixes:
            continue
        # Skip caches / venvs.
        parts = set(p.parts)
        if "__pycache__" in parts or ".venv" in parts or "node_modules" in parts:
            continue
        out.append(p)
    return out


_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    # AWS access key.
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    # OpenAI live key.
    re.compile(r"\bsk-live-[A-Za-z0-9]{20,}"),
    # Bearer-token literals.
    re.compile(r"Bearer\s+[A-Za-z0-9_\-\.]{30,}"),
    # Azure-style 32-char hex blob immediately following an ='/=" — only
    # flagged when literally assigned in code/config.
    re.compile(r'(?:api_key|API_KEY|api-key)["\']?\s*[:=]\s*["\'][0-9a-f]{32,}["\']'),
)


@pytest.mark.parametrize("scan_dir", [
    "src",
    "docs",
])
def test_no_hardcoded_secrets_in_repo(scan_dir: str):
    target = _REPO_ROOT / scan_dir
    assert target.is_dir(), f"Expected dir not found: {target}"
    files = _scan_files(target, suffixes=(".py", ".md", ".env", ".cfg", ".ini"))
    offenders: list[tuple[Path, str]] = []
    for fp in files:
        try:
            text = fp.read_text(encoding="utf-8")
        except Exception:
            continue
        for pat in _SECRET_PATTERNS:
            m = pat.search(text)
            if m:
                offenders.append((fp.relative_to(_REPO_ROOT), m.group(0)))
    assert not offenders, (
        f"Possible hardcoded secrets detected in {scan_dir}: {offenders}"
    )
