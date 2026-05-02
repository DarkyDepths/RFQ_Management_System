"""CI guards #4 + #5 — no active source/README references to v3 docs or
v3 vocabulary.

Per Batch 0 acceptance criteria:

* No active source/stub/README references to ``rfq_copilot_architecture_v3.html``.
* No active source/stub/README references to the prior planner-with-
  deterministic-fallback framing or the prior LLM tool-calling stage
  naming.

Scope: ``src/**/*.py`` and ``README.md``.
**Excluded** (legitimate superseded references): ``docs/`` (the freeze
itself in Architecture_Frozen_v2 Appendix A and the superseded-banner
docs both reference these tokens contextually); ``tests/`` (the test
file itself names the forbidden tokens to detect them).
"""

from __future__ import annotations

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
README = REPO_ROOT / "README.md"


# Plain substring matches — case-sensitive where sensible.
FORBIDDEN_LITERALS = (
    "rfq_copilot_architecture_v3.html",
    "tiny LLM fallback",
    "tiny-LLM fallback",
)

# Regex patterns — match v3 vocabulary forms while allowing safe contexts.
# These specifically target class definitions, file references, and
# heading/header forms, NOT every occurrence of the word.
FORBIDDEN_PATTERNS = (
    re.compile(r"\bclass\s+Agent\b"),                  # `class Agent:` — v3 stage class
    re.compile(r"\bAgent\s+stage\b"),                  # docstring like "Agent stage —"
    re.compile(r"\bAgent\s+—\s+LLM"),                  # the old v3 docstring header
    re.compile(r"agent\.py"),                          # the deleted v3 file
    re.compile(r"\bdeterministic\s+classifier\s*\(.*tiny"),  # the v3 phrasing
)


def _scan_files() -> list[Path]:
    files: list[Path] = []
    if README.exists():
        files.append(README)
    for p in SRC.rglob("*.py"):
        if p.is_file():
            files.append(p)
    return files


def test_no_v3_html_references():
    offenders: list[tuple[str, str]] = []
    for path in _scan_files():
        content = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_LITERALS:
            if token in content:
                offenders.append((str(path.relative_to(REPO_ROOT)), token))

    assert not offenders, (
        f"Active source/README must not reference superseded v3 tokens. "
        f"Offenders: {offenders}. "
        f"See Batch 0 acceptance criteria #4 + #5."
    )


def test_no_v3_vocabulary_patterns():
    offenders: list[tuple[str, str]] = []
    for path in _scan_files():
        content = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            for match in pattern.finditer(content):
                offenders.append(
                    (str(path.relative_to(REPO_ROOT)), match.group(0))
                )

    assert not offenders, (
        f"Active source/README must not use prior v3 vocabulary forms. "
        f"Offenders: {offenders}. "
        f"See Batch 0 acceptance criteria #5."
    )
