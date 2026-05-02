# Slice 1 — App Testing Guide

This document is the **practical guide** for testing rfq_copilot_ms
end-to-end inside the real app. It covers what works in Slice 1, what
intentionally does not, the request/response contract, the env vars,
and a manual QA checklist.

For the architecture spec see
[`11-Architecture_Frozen_v2.md`](11-Architecture_Frozen_v2.md). This
document is **operational**, not architectural — it tells you what to
type, what to expect, and what to check.

---

## What Slice 1 supports

| Path | What it answers | Source |
|---|---|---|
| **Path 1** | Conversational trivial messages: greeting, thanks, farewell. | FastIntake template (no LLM, no manager). |
| **Path 4** | RFQ-specific operational questions about a single RFQ: deadline, owner, status, current stage, priority, blockers, stages, summary. | Planner classifies → Resolver → Access → Manager fetch → deterministic renderer (single-field) OR Compose+Judge (summary, blockers). |
| **Path 8.1 / 8.2 / 8.3 / 8.4 / 8.5** | Safe fallback templates when something is wrong (unsupported intent, out-of-scope, clarification needed, target inaccessible, source/LLM/judge failure). | Planner / Validator / Factory / Gate routing → Finalizer template. |

## What Slice 1 intentionally does NOT support

These produce safe Path 8.x responses, **never** invented data:

- **Path 2** — domain knowledge / RAG explanations ("what is PWHT?").
- **Path 3** — portfolio retrieval ("show urgent RFQs", "find Aramco projects").
- **Path 5** — intelligence retrieval ("what does the briefing say?", win probability, readiness, workbook review, cost prediction, bid strategy).
- **Path 6** — cross-RFQ reference ("for IF-0001 use the same approach as IF-0002").
- **Path 7** — multi-RFQ comparison ("compare IF-0001 with IF-0002").
- **Forbidden fields** — margin, internal_cost, ranking, winner, estimation_quality.
- **Multi-intent in one message**.

Asking any of these will route to a Path 8 safe template — it will not
produce a fabricated answer. **Do not** read a Path 8 reply as "the
copilot doesn't work"; that's the trust boundary doing its job.

---

## Required services

| Service | Default local port | Required for |
|---|---|---|
| `rfq_manager_ms` | `8000` | All Path 4 questions (manager-grounded answers). |
| `rfq_copilot_ms` | `8003` | The copilot lane under test. |
| Azure OpenAI | n/a | Planner (any non-FastIntake question) + Compose+Judge (summary, blockers). |

The copilot **boots and answers FastIntake messages even without
Azure** (greeting / thanks / farewell). Non-FastIntake messages
without Azure will route to Path 8.5 `llm_unavailable`. This is
intentional Slice 1 behavior, not a bug.

---

## Required environment variables

Create `.env` in `microservices/rfq_copilot_ms/` (or export in the shell)
with at least:

```
# DB — defaults to local SQLite, fine for dev
DATABASE_URL=sqlite:///./rfq_copilot.db

# Manager wiring — service ROOT only. The copilot's ManagerConnector
# appends the API path "/rfq-manager/v1" itself, so do NOT include
# it here or every URL gets doubled and 404s.
# Adjust the port to wherever you launched rfq_manager_ms (its
# default is :8000):
MANAGER_BASE_URL=http://localhost:8000

# Azure OpenAI — required for Planner + Compose + Judge
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_VERSION=2024-08-01-preview
AZURE_OPENAI_API_KEY=<your-key>
AZURE_OPENAI_CHAT_DEPLOYMENT=<your-gpt4o-deployment>
```

**Notes:**

- `MANAGER_BASE_URL` is empty by default; you must set it for Path 4.
  If unset, Path 4 questions safely route to Path 8.5
  `source_unavailable` rather than crashing.
- **Set the service root only** (e.g. `http://localhost:8000`). The
  `ManagerConnector` appends `/rfq-manager/v1` internally — including
  it in the env var causes `/rfq-manager/v1/rfq-manager/v1/...` 404s.
- Azure variables are empty by default. Missing Azure -> non-FastIntake
  messages route to Path 8.5 `llm_unavailable`. Boot will not fail.
- **Never commit `.env`.** Never paste keys into chat. The copilot logs
  do not echo secrets.

---

## Run the copilot locally

```
cd microservices/rfq_copilot_ms
uvicorn src.app:app --reload --port 8003
```

Then probe:

```
curl http://localhost:8003/health
# -> {"status":"ok","service":"rfq_copilot_ms"}

curl http://localhost:8003/health/readiness
# -> {"service":"rfq_copilot_ms",
#     "azure_planner_configured": true|false,
#     "manager_base_url_configured": true|false,
#     "manager_base_url": "...",
#     "persistence_configured": true|false}
```

**`/health/readiness` is passive** — it reports configuration presence
only. A `true` value does not guarantee the upstream is reachable; it
only means the env wiring is in place. Use it as the first sanity
check before debugging individual turns.

---

## How to test /v2 with curl

The endpoint is `POST /rfq-copilot/v2/threads/{thread_id}/turn`. The
`thread_id` is currently a free-form string — the v2 lane does not yet
require pre-creating a thread (Slice 1 keeps the contract minimal).

### Request body

```jsonc
{
  "message": "What is the deadline for IF-0001?",
  "current_rfq_code": null,    // optional — set when the user is on an RFQ page
  "current_rfq_id": null       // optional, reserved
}
```

### Response body

```jsonc
{
  "lane": "v2",
  "status": "answered",
  "thread_id": "t1",
  "turn_id": "<uuid>",                       // per-turn UUID
  "answer": "<user-facing string>",          // safe; never raw draft on Judge fail
  "path": "path_4" | "path_1" | "path_8_x",  // null only if Finalizer didn't run
  "intent_topic": "deadline" | "summary" | ...,
  "reason_code": null | "no_evidence" | "llm_unavailable" | ...,
  "target_rfq_code": "IF-0001" | null,       // resolved target (Path 4)
  "execution_record_id": "<uuid>" | null     // null if persistence failed
}
```

The frontend should treat `answer` as the only required user-facing
field; everything else is metadata for analytics, debugging, and UI
hints (e.g. show a different style for `path_8_x` answers).

### Example calls

```bash
# Path 1 — FastIntake (no Azure / no manager needed)
curl -s -X POST http://localhost:8003/rfq-copilot/v2/threads/t1/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'

# Path 4 — single-field deterministic
curl -s -X POST http://localhost:8003/rfq-copilot/v2/threads/t1/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the deadline for IF-0001?"}'

# Path 4 — page-context + summary (Compose+Judge)
curl -s -X POST http://localhost:8003/rfq-copilot/v2/threads/t1/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Give me a summary.", "current_rfq_code": "IF-0001"}'
```

---

## Supported Slice 1 questions

### FastIntake (no LLM, no manager)

- `hello`
- `thanks`
- `bye`
- empty message
- `???`
- `!!!`

### Path 4 — explicit RFQ code

- What is the deadline for IF-0001?
- Who owns IF-0001?
- What is the status of IF-0001?
- What is the current stage of IF-0001?
- What is the priority of IF-0001?
- Is IF-0001 blocked?
- Show stages for IF-0001.
- Give me a summary of IF-0001.

### Path 4 — RFQ-page context (`current_rfq_code` provided)

These work **only** when the request includes `current_rfq_code`. Without
it the copilot routes to Path 8.3 (clarification — "which RFQ?"):

- What is the deadline?
- Who owns this?
- What is the current stage?
- Is it blocked?
- Show stages.
- Give me a summary.

### Safe fallbacks (intentional)

| User input | Route | What happens |
|---|---|---|
| Page-default question without `current_rfq_code` | Path 8.3 | Asks the user to specify the RFQ. |
| Unknown RFQ code (e.g. IF-9999) | Path 8.4 | "I can't access that RFQ." |
| Manager service down | Path 8.5 | "The data source isn't reachable right now…" |
| Azure / Planner not configured | Path 8.5 | "The language model I rely on isn't available right now…" |
| Out-of-scope ("write me a recipe") | Path 8.2 | "I can only help with RFQ, estimation, and industrial project questions." |
| Forbidden field ("what's the margin on IF-0001?") | Path 8.1 / 8.5 | Refused without quoting the forbidden field. |

---

## Manual QA checklist

Run through this before claiming a deployment is healthy.

### Environment

- [ ] `rfq_manager_ms` running on the configured port.
- [ ] `rfq_copilot_ms` running on `:8003`.
- [ ] `MANAGER_BASE_URL` matches the manager port.
- [ ] Azure OpenAI env vars set (Planner / Compose / Judge).
- [ ] DB file (or configured DATABASE_URL) creates `execution_records`
  on first boot.
- [ ] Frontend points at `POST /rfq-copilot/v2/threads/{thread_id}/turn`.
- [ ] `GET /health` returns `{"status":"ok"}`.
- [ ] `GET /health/readiness` shows all three configured flags `true`.

### General copilot

- [ ] `hello` → short greeting (Path 1).
- [ ] `thanks` → short reply (Path 1).
- [ ] `???` → safe clarification or out-of-scope, never a fabricated reply.
- [ ] `What is the deadline for IF-0001?` → grounded answer with the date.
- [ ] `What is the deadline?` (no `current_rfq_code`) → asks for clarification.
- [ ] `write me a recipe` → out-of-scope reply (Path 8.2).
- [ ] `show urgent RFQs` → safe unsupported reply (Slice 1 has no Path 3);
  must NOT produce a fake list.

### RFQ-page context (set `current_rfq_code` on each request)

- [ ] `What is the deadline?` → grounded answer for the current RFQ.
- [ ] `Who owns this?` → grounded answer.
- [ ] `What is the current stage?` → grounded answer.
- [ ] `Is it blocked?` → grounded answer.
- [ ] `Show stages.` → ordered list.
- [ ] `Give me a summary.` → grounded composed multi-field summary.

### Failure modes

- [ ] Unknown RFQ code → Path 8.4 reply, no leak of internal codes.
- [ ] Stop `rfq_manager_ms` → Path 8.5 `source_unavailable`, copilot
  itself stays up.
- [ ] Unset Azure env vars → non-FastIntake messages get Path 8.5
  `llm_unavailable`; FastIntake (`hello`, `thanks`, `bye`) still works.
- [ ] Persistence failure (e.g. DB file made read-only) → answer
  still returned, `execution_record_id` is `null` in the response.

### Record verification

For any successful turn, the response includes `execution_record_id`. Check:

- [ ] Row exists in `execution_records` with that id.
- [ ] `path`, `intent_topic`, `reason_code` populated.
- [ ] Path 4 rows have `tool_invocations_json` and `evidence_refs_json`.
- [ ] Path 8.x rows carry the escalation in `escalations_json` with
  `source_stage` set.
- [ ] `final_answer` matches what the user saw — and is **never** the
  raw rejected draft from a Judge failure.
- [ ] `state_json` does **not** contain `draft_text` (redacted by
  Persist in Batch 8).

---

## Operational diagnostics

Per-turn the controller emits one info log line:

```
v2.turn path=path_4 intent=deadline reason_code=None target=IF-0001
        duration_ms=412 execution_record_id=<uuid> status=answered
```

- No prompts, no LLM output, no draft text, no stack traces, no secrets.
- For Path 8 turns, `reason_code` shows why the user got a fallback.
- `duration_ms` is the wall-clock orchestration time.
- `execution_record_id=None` means persistence was unavailable or
  failed; the user still got an answer.

For deeper forensics inspect `execution_records` directly — the row
captures `planner_proposal_json`, `validated_proposal_json`, `plan_json`,
`tool_invocations_json`, `evidence_refs_json`, `escalations_json`, and
the redacted `state_json`.

---

## Known limitations

- **Single-target Path 4 only.** Multi-RFQ questions route to Path 8.3
  (clarification) or Path 8.1 (unsupported) — Path 7 ships in a later slice.
- **No portfolio queries.** Path 3 is unimplemented; "show urgent RFQs"
  routes to a safe fallback.
- **No intelligence/RAG/domain answers.** Paths 2 and 5 are unimplemented.
- **No streaming.** /v2 is request/response only.
- **Auth bypass is on by default in dev.** See `AUTH_BYPASS_ENABLED` in
  `src/config/settings.py`. Replace `src/utils/auth_context.py` with
  IAM-backed resolver before any production use.
- **DB schema bootstraps via `Base.metadata.create_all` on startup.**
  Migrate to Alembic before production.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Every non-FastIntake message returns Path 8.5 `llm_unavailable` | Azure env vars missing or wrong | Verify `AZURE_OPENAI_*` in `.env`; restart copilot. Check `/health/readiness`. |
| Every Path 4 query returns Path 8.5 `source_unavailable` | Manager not running, or `MANAGER_BASE_URL` set to the wrong value (e.g. duplicates the API path) | Start `rfq_manager_ms`. Verify the *service-root* form: `curl $MANAGER_BASE_URL/rfq-manager/v1/rfqs/<known-id>` should return 200 with JSON. If you instead see 404, you likely included `/rfq-manager/v1` in `MANAGER_BASE_URL` — strip it. |
| Real RFQ code returns Path 8.4 inaccessible | Manager doesn't have that RFQ, or the RFQ was deleted, or auth-bypass user lacks access | Check the manager DB. The copilot does not invent access. |
| Response missing `execution_record_id` | DB write failed (file permissions, locked SQLite, etc.) | Check copilot logs; persistence failures are logged but never break the user answer. |
| Frontend gets a 500 | An unexpected internal exception escaped the gate-recovery path | Inspect the copilot log line for the turn id; investigate the trace there. The user should still have received a Path 8.5 fallback in normal operation — a real 500 means a bug in the orchestrator. |
| `/health/readiness` shows `manager_base_url_configured: false` | `MANAGER_BASE_URL` is empty or unset in the running process | Re-export the var; restart. |

---

## What this document is not

- It is **not** the architecture spec. See `11-Architecture_Frozen_v2.md`.
- It is **not** a roadmap. Path 2/3/5/6/7 are out of scope for Slice 1
  by design — do not add tests assuming they exist.
- It is **not** a security review. Auth bypass + dev SQLite + the
  passive-only readiness probe are dev-mode shortcuts; production
  hardening is a separate workstream.
