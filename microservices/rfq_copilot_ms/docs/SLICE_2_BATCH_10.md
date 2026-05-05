# Slice 2 — Batch 10: /v2 threads + history reconstruction + working_memory capture

> First batch of **Slice 2 — Conversation-Aware Portfolio Copilot**.
> Backend only. Frontend cutover is **PR-D** (separate, follows this).

---

## What this batch does

Builds the mechanical conversation primitive for `/v2`. Before this
batch, `/v2` shipped the turn endpoint only — thread lifecycle and
history loading went through `/v1`. After this batch:

- New table `v2_threads` (metadata only — no turn content).
- Five `/v2/threads/*` endpoints (`new`, `open`, `list`, `GET /{id}`,
  and the existing `POST /{id}/turn` now requires a registered id).
- History reconstructed from `execution_records` (no `v2_turns` table).
- Working memory CAPTURED into `state.working_memory` after the plan
  is built, capped by `MemoryPolicy.working_pairs`.
- Deterministic title from the first user message (no LLM).
- Actor ownership enforced (404 ThreadNotFoundError for missing OR
  not-owned — same code prevents enumeration).
- Freshness rules computed at read time (`general` 3 days,
  `rfq_bound` 7 days). No background job. No `status` column.

---

## What this batch deliberately does NOT do

**Capture, don't inject.** Batch 10 puts working memory on
`state.working_memory` and stops. Planner / Compose / Judge prompts
are byte-identical to Slice 1. The anti-drift test
`tests/anti_drift/test_batch10_no_history_injection.py` verifies this
on a multi-turn smoke.

Out of scope (deferred to later batches):

- ❌ History injection into Planner / Compose / Judge prompts → **Batch 12**
- ❌ Semantic follow-up resolution ("the first one", "what about its owner?") → **Batch 12**
- ❌ Path 3 portfolio retrieval → **Batch 11a** (basic filters), **11b** (semantic descriptors)
- ❌ Episodic memory → post-Slice-2
- ❌ `/v1` changes (the legacy lane is untouched)
- ❌ Frontend cutover from `/v1` to `/v2` thread management → **PR-D**
- ❌ Alembic migrations (uses `Base.metadata.create_all` like every other table)
- ❌ Title editing / pin / archive / soft-delete → UI/product features

---

## ⚠️ Release coupling — Batch 10 + PR-D MUST ship together

The merged PR-C frontend hybrid sends `/v1` thread ids to `/v2/turn`.
Batch 10 enforces strict registration on `/v2/turn`: a `/v1` id will
return `404 ThreadNotFoundError`. **The hybrid flow breaks the moment
Batch 10 is exposed to users.**

**Deploy ordering:**

1. Batch 10 → dev / staging only.
2. Backend smoke (`curl` commands below) — do **not** test in browser.
3. Ship Batch 10 + PR-D to production together.

**PR-D scope (NOT in Batch 10):**

- Frontend `connectors/copilot/threads.ts` — switch `openThread`,
  `createNewThread`, `listThreads`, `loadThread` from
  `/rfq-copilot/v1/threads/*` to `/rfq-copilot/v2/threads/*`.
- Adapt wire types for the new fields (`is_stale`, `created_new`,
  `title`, `preview`, `mode.rfq_code`).
- Browser smoke.

---

## Endpoints

All under `/rfq-copilot/v2/threads/`.

| Endpoint | Body | Response |
|---|---|---|
| `POST /new` | `{ mode }` | `{ thread_id }` (title NULL until first turn) |
| `POST /open` | `{ mode }` | `{ thread_id, mode, messages, is_stale, created_new }` |
| `POST /list` | `{ mode }` | `{ threads: [{ thread_id, title, rfq_code, rfq_label, last_activity_at, is_stale, preview }] }` |
| `GET /{id}` | — | `{ thread_id, mode, messages, is_stale }` (404 if not owned) |
| `POST /{id}/turn` | `{ message, current_rfq_code?, current_rfq_id? }` | existing `V2TurnResponse` (404 if thread not owned/missing) |

### Mode shape

```json
{ "kind": "general" }
{ "kind": "rfq_bound", "rfq_id": "<uuid>", "rfq_code": "IF-0058", "rfq_label": "IF-0058 — Refinery..." }
```

`/v2`'s `rfq_bound` mode adds an optional `rfq_code` field that `/v1`
didn't carry; the rest mirrors `/v1`.

### Freshness

```python
STALENESS_THRESHOLDS = {
    "general":   timedelta(days=3),
    "rfq_bound": timedelta(days=7),
}
```

Computed at read time — no persisted flag, no background job.
`/open` against a stale thread creates a fresh one (it does NOT delete
the stale one — the user can still find it via `/list`, where it
surfaces with `is_stale=true`).

---

## Architecture decisions

### D1. Thread storage = C+metadata (no `v2_turns` table)

`execution_records` is the source of truth for turn content. It already
has `thread_id`, `turn_id`, `user_message`, `final_answer`,
`created_at`, `path`, `intent_topic`, `target_rfq_code`,
`reason_code`. A separate `v2_turns` table would duplicate every one
of those fields and need transactional joins to stay consistent. The
new `v2_threads` table holds metadata only (owner, mode, title,
last_activity_at).

History reconstruction is one query against `execution_records`
ordered by `created_at`.

### D2. `/turn` requires a registered thread (option b)

Unknown `thread_id` → `404 ThreadNotFoundError`. No invisible
auto-create. This is a deliberate trade-off:

- ✅ Catches drift between thread management and turn endpoint.
- ✅ Prevents pollution of `execution_records` with attacker-chosen
  thread ids.
- ❌ Breaks the current PR-C hybrid frontend (the reason for the
  release-coupling warning above).

### D3. Capture working_memory; do NOT inject

`state.working_memory` is populated AFTER the factory builds the plan
(so `MemoryPolicy.working_pairs` from the registry caps the size).
Planner / Compose / Judge prompts are byte-identical to Slice 1.

**Why split capture and injection across batches:** injection changes
LLM input shape, which forces a Judge re-verification pass and a
prompt-engineering iteration. Doing capture first lets Batch 11 ship
Path 3 (which depends on conversation context being CAPTURED but not
yet semantically resolved) before Batch 12 takes on the LLM-shape work.

### D4. No `status` column

`stale` is computed from `last_activity_at`. `closed` has no UI surface
yet. Add the column when there's actual semantics for it.

### D5. WorkingMemoryEntry: complete pairs only

`assistant_answer: str` is **required** (not Optional). NULL
`final_answer` rows from mid-flight Persist failures are skipped from
working memory.

The asymmetry vs message reconstruction is deliberate:

- **Message reconstruction (UI display, lenient):** user-only rows
  surface so the UI can show "you sent X; assistant didn't answer."
- **Working memory (semantic resolution input, strict):** Batch 12's
  follow-up resolution against an empty assistant answer would be
  meaningless or worse.

### D6. Actor ownership enforced everywhere

Every read/write through `V2ThreadDatasource` is gated by
`(thread_id, actor_id)`. Owner mismatch → `ThreadNotFoundError` (404).
Same error class as missing thread to prevent ID enumeration via
status-code differentiation.

### D7. Deterministic title

On the first successful `/turn`, if `title is None`, set it to
`request.message.strip()[:60]` (+ `…` if truncated). No LLM call. No
"smart" rewriting. `set_title_if_unset` uses `WHERE title IS NULL` so
a future manual-edit endpoint won't be clobbered.

### D8. Anti-drift tests

Two new anti-drift tests guard the Batch 10 design:

- `test_memory_policy_load_bearing.py` — AST scan ensures at least one
  source file under `src/` reads `MemoryPolicy.working_pairs`.
  Pre-Batch-10 the field was declared but unused; this test prevents
  silent regression.
- `test_batch10_no_history_injection.py` — multi-turn smoke captures
  every Planner / Compose / Judge LLM call on turn 2. The recorded
  `messages` arrays must be `[system, user]` only — no prior
  assistant message, no echo of turn-1 content.

---

## Manual verification (curl, no UI)

> The UI will not work between Batch 10 and PR-D. Use these `curl`
> commands.

```bash
# 1. Create
curl -X POST -H "Content-Type: application/json" \
  -d '{"mode":{"kind":"general"}}' \
  http://localhost:8003/rfq-copilot/v2/threads/new
# -> {"thread_id": "abc123"}

# 2. Turn (sets title)
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"What is the deadline for IF-0001?"}' \
  http://localhost:8003/rfq-copilot/v2/threads/abc123/turn
# -> 200 with answer

# 3. Second turn (working_memory now populated; LLM prompt unchanged)
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"Who owns IF-0001?"}' \
  http://localhost:8003/rfq-copilot/v2/threads/abc123/turn

# 4. Reload (history reconstructed, title set)
curl http://localhost:8003/rfq-copilot/v2/threads/abc123

# 5. List
curl -X POST -H "Content-Type: application/json" \
  -d '{"mode":{"kind":"general"}}' \
  http://localhost:8003/rfq-copilot/v2/threads/list

# 6. Unknown thread → 404
curl -X POST -H "Content-Type: application/json" \
  -d '{"message":"hi"}' \
  http://localhost:8003/rfq-copilot/v2/threads/unknown-id/turn
# -> 404 {"error":"ThreadNotFoundError","message":"..."}
```

DB inspection:

```bash
sqlite3 microservices/rfq_copilot_ms/rfq_copilot.db \
  'SELECT id, owner_actor_id, mode_kind, title, last_activity_at FROM v2_threads;'
sqlite3 microservices/rfq_copilot_ms/rfq_copilot.db \
  'SELECT id, thread_id, user_message, final_answer FROM execution_records WHERE thread_id="abc123" ORDER BY created_at;'
```

---

## Roadmap context

| PR / Batch | Scope | Depends on |
|---|---|---|
| **Batch 10 (this)** | `/v2` threads + history reconstruction + working_memory capture | merged main |
| **PR-D** | Frontend cutover from `/v1` to `/v2/threads/*`. Required before Batch 10 reaches users. | Batch 10 |
| **Batch 11a** | Path 3 — basic portfolio filters (urgent / overdue / critical / by-owner / by-status) using existing manager `list_rfqs` | Batch 10 + PR-D in production |
| **Batch 11b** | Path 3 — semantic descriptor search ("Aramco projects") | 11a |
| **Batch 12** | Inject working_memory into Planner / Compose; add Judge re-verification; support "the first one" / "which is most delayed?" / "open the first one" | 11a (so Path 3 lists exist to follow up on) |

### Deferred design problem for Batch 12

`MemoryPolicy.working_pairs` lives on `state.plan.memory_policy`, but
the plan doesn't exist until AFTER Planner runs. Batch 12 (which wants
to inject working_memory into Planner's prompt) must solve this. Three
options to consider:

1. Load history with a default cap (max of all paths' `working_pairs`)
   before Planner; trim after the plan exists.
2. Restructure orchestration so a minimal plan exists pre-Planner.
3. Inject only into Compose / Judge (which run after the plan exists),
   not Planner.

Out of scope for Batch 10. Documented here so Batch 12's author has
the context.
