"""Anti-drift tests for docs/SLICE_1_APP_TESTING.md (Batch 9).

The Slice 1 app-testing document is the contract between the copilot
and the humans testing it in the app. These tests pin the parts that
must remain present so future edits don't accidentally drop a section
that testers / frontend devs rely on.

The tests check structural anchors (headings, sections, tokens) — they
do NOT lint prose. Updating wording is fine; removing the anchored
sections is what fails.
"""

from __future__ import annotations

from pathlib import Path

import pytest


_DOC_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "docs" / "SLICE_1_APP_TESTING.md"
)


@pytest.fixture(scope="module")
def doc_text() -> str:
    return _DOC_PATH.read_text(encoding="utf-8")


# ── 1. Doc exists ───────────────────────────────────────────────────────


def test_slice1_app_testing_doc_exists():
    assert _DOC_PATH.is_file(), (
        f"Slice 1 testing doc must exist at {_DOC_PATH}. "
        f"It is the contract for app-side QA."
    )


# ── 2. Lists supported Slice 1 questions (FastIntake + Path 4) ──────────


@pytest.mark.parametrize("supported_question", [
    "hello",
    "thanks",
    "bye",
    "What is the deadline for IF-0001?",
    "Who owns IF-0001?",
    "What is the status of IF-0001?",
    "What is the current stage of IF-0001?",
    "What is the priority of IF-0001?",
    "Is IF-0001 blocked?",
    "Show stages for IF-0001.",
    "Give me a summary of IF-0001.",
])
def test_doc_lists_supported_questions(doc_text: str, supported_question: str):
    assert supported_question in doc_text, (
        f"Doc must list supported Slice 1 question: {supported_question!r}"
    )


# ── 3. Lists intentionally unsupported capabilities ─────────────────────


@pytest.mark.parametrize("unsupported_token", [
    "Path 2",
    "Path 3",
    "Path 5",
    "Path 6",
    "Path 7",
    "win probability",
    "bid strategy",
    "margin",
    "intentionally does NOT support",
])
def test_doc_lists_intentionally_unsupported(
    doc_text: str, unsupported_token: str,
):
    assert unsupported_token in doc_text, (
        f"Doc must call out unsupported Slice 1 capability: "
        f"{unsupported_token!r}"
    )


# ── 4. Documents required env vars ──────────────────────────────────────


@pytest.mark.parametrize("env_var", [
    "MANAGER_BASE_URL",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
    "AZURE_OPENAI_CHAT_DEPLOYMENT",
    "DATABASE_URL",
])
def test_doc_documents_env_vars(doc_text: str, env_var: str):
    assert env_var in doc_text, (
        f"Doc must mention required env var {env_var!r}"
    )


def test_doc_documents_manager_base_url_as_service_root_only(doc_text: str):
    """The connector appends ``/rfq-manager/v1`` to ``MANAGER_BASE_URL``
    (see ``manager_ms_connector._url``). The env var must therefore be
    the *service root* only — never include the API path or the
    connector will produce ``/rfq-manager/v1/rfq-manager/v1/...`` 404s.

    This pin guards two things:
    1. No example shows the doubled form ``MANAGER_BASE_URL=...rfq-manager/v1``.
    2. The doc mentions that the connector appends the path internally,
       so a tester knows why the env var is "just the host".
    """
    import re
    # 1. No assignment-style example with /rfq-manager/v1 baked in.
    bad_assignment = re.compile(
        r"MANAGER_BASE_URL\s*=\s*\S*/rfq-manager/v1"
    )
    assert not bad_assignment.search(doc_text), (
        "Doc must not show MANAGER_BASE_URL set with /rfq-manager/v1 "
        "appended — the connector adds that itself."
    )
    # 2. The path should still be mentioned as the appended-internally
    #    convention so the curl troubleshooting test is valid.
    assert "/rfq-manager/v1" in doc_text
    assert "appends" in doc_text.lower()


# ── 5. Documents request body shape (message + current_rfq_code) ────────


def test_doc_documents_request_body_fields(doc_text: str):
    assert "message" in doc_text
    assert "current_rfq_code" in doc_text


def test_doc_documents_v2_endpoint(doc_text: str):
    # The exact route the frontend posts to.
    assert "/rfq-copilot/v2/threads/" in doc_text
    assert "/turn" in doc_text


# ── 6. Documents execution_record_id semantics ──────────────────────────


def test_doc_documents_execution_record_id(doc_text: str):
    assert "execution_record_id" in doc_text
    # Must explain the null-on-failure semantics.
    assert "null" in doc_text.lower()


# ── 7. Warns Path 3/5/6/7 are not implemented yet ───────────────────────


def test_doc_warns_path_3_5_6_7_not_implemented(doc_text: str):
    """The reader must not be misled into expecting these in Slice 1."""
    for token in ("Path 3", "Path 5", "Path 6", "Path 7"):
        assert token in doc_text


# ── 8. Documents readiness endpoint (Batch 9 addition) ──────────────────


def test_doc_documents_readiness_endpoint(doc_text: str):
    assert "/health/readiness" in doc_text
    # Reader must understand it's passive (no live call).
    assert "passive" in doc_text.lower()


# ── 9. No leaked secrets in the doc ─────────────────────────────────────


def test_doc_does_not_contain_real_secrets(doc_text: str):
    """Defensive scan — the doc must use placeholder syntax for any
    secrets, never a real-looking key. Detects common leak patterns."""
    lower = doc_text.lower()
    # Detect "AKIA"-style AWS keys, "sk-..." OpenAI-style keys, etc.
    assert "akia" not in lower, "Possible AWS key in doc"
    assert "sk-live-" not in lower
    assert "bearer " not in lower
    # Azure key would look like a 32+ char hex blob; don't try to
    # pattern-match (false positives), but ensure documented examples
    # use angle-bracket placeholders.
    assert "<your-key>" in doc_text
    assert "<your-resource>" in doc_text
