// ── Domain types (camelCase) — what components and context see ──────────────

export type CopilotMode =
  | { kind: "general" }
  | { kind: "rfq_bound"; rfqId: string; rfqLabel: string };

export type CopilotMessageRole = "user" | "assistant";

export interface CopilotMessage {
  id: string;
  role: CopilotMessageRole;
  content: string;
  createdAt: string;
}

export interface CopilotThread {
  id: string;
  mode: CopilotMode;
  lastActivityAt: string;
  messages: CopilotMessage[];
}

export type CopilotStatus = "idle" | "loading" | "error";

export interface CopilotThreadSummary {
  id: string;
  mode: CopilotMode;
  lastActivityAt: string;
  preview: string;
}

// ── Wire types (snake_case) — exact match to backend Pydantic output ────────
//
// The connector layer (src/connectors/copilot/threads.ts) owns all wire <-> domain
// mapping. Components and context never see snake_case fields.

export type WireMode =
  | { kind: "general" }
  | { kind: "rfq_bound"; rfq_id: string; rfq_label: string };

export interface WireMessage {
  id: string;
  role: CopilotMessageRole;
  content: string;
  created_at: string;
}

export interface WireOpenThreadResponse {
  thread_id: string;
  messages: WireMessage[];
}

export interface WireNewThreadResponse {
  thread_id: string;
}

export interface WireTurnResponse {
  message_id: string;
  assistant_message: WireMessage;
}

export interface WireThreadSummary {
  thread_id: string;
  mode: WireMode;
  last_activity_at: string;
  preview: string;
}

export interface WireListThreadsResponse {
  threads: WireThreadSummary[];
}

export interface WireThreadDetail {
  thread_id: string;
  messages: WireMessage[];
}

// ── /v2 lane wire types (Slice 1 — turn endpoint only) ───────────────────

/**
 * Body for ``POST /rfq-copilot/v2/threads/{thread_id}/turn``. Differs
 * from /v1's ``user_message`` field on purpose: /v2 frames the turn as
 * "the user said X while looking at RFQ Y", which is the primitive the
 * Planner classifies against.
 *
 * ``current_rfq_code`` may be either a human-readable code ("IF-0001")
 * or a UUID; the copilot's access stage dispatches to the correct
 * manager endpoint by inspecting the shape. Frontend RFQ-bound mode
 * carries the manager UUID in ``rfqId``, so we pass that directly.
 */
export interface WireV2TurnRequest {
  message: string;
  current_rfq_code?: string | null;
  current_rfq_id?: string | null;
}

/**
 * /v2 turn response. The user-facing answer lives in ``answer``;
 * everything else is metadata for analytics and UI hints (Path 8.x
 * answers may render with a distinct style; ``target_rfq_code`` lets
 * the UI cross-link the answer to a card without re-parsing prose).
 *
 * Per Batch 9 stable contract: this key set is locked by a CI guard
 * in tests/smoke/test_v2_slice1_app_readiness.py -- additive changes
 * only.
 */
export interface WireV2TurnResponse {
  lane: "v2";
  status: "answered";
  thread_id: string;
  turn_id: string | null;
  answer: string;
  path: string | null;
  intent_topic: string | null;
  reason_code: string | null;
  target_rfq_code: string | null;
  execution_record_id: string | null;
}
