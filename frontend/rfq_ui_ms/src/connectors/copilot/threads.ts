import { apiConfig } from "@/config/api";
import { requestJson } from "@/lib/http-client";
import type {
  CopilotMessage,
  CopilotMode,
  CopilotThreadSummary,
  WireListThreadsResponse,
  WireMessage,
  WireMode,
  WireNewThreadResponse,
  WireOpenThreadResponse,
  WireThreadDetail,
  WireThreadSummary,
  WireV2TurnResponse,
} from "@/types/copilot";

// ── wire <-> domain mappers (the only place snake_case touches the codebase) ──

function toDomainMode(wire: WireMode): CopilotMode {
  if (wire.kind === "general") return { kind: "general" };
  return { kind: "rfq_bound", rfqId: wire.rfq_id, rfqLabel: wire.rfq_label };
}

function toDomainThreadSummary(wire: WireThreadSummary): CopilotThreadSummary {
  return {
    id: wire.thread_id,
    mode: toDomainMode(wire.mode),
    lastActivityAt: wire.last_activity_at,
    preview: wire.preview,
  };
}

function toWireMode(mode: CopilotMode): WireMode {
  if (mode.kind === "general") {
    return { kind: "general" };
  }
  return { kind: "rfq_bound", rfq_id: mode.rfqId, rfq_label: mode.rfqLabel };
}

function toDomainMessage(wire: WireMessage): CopilotMessage {
  return {
    id: wire.id,
    role: wire.role,
    content: wire.content,
    createdAt: wire.created_at,
  };
}

function buildUrl(path: string) {
  return `${apiConfig.copilotBaseUrl}${apiConfig.copilotApiPath}${path}`;
}

function buildV2Url(path: string) {
  return `${apiConfig.copilotBaseUrl}${apiConfig.copilotV2ApiPath}${path}`;
}

/** Pull the page-context identifier the planner / resolver needs from
 * a CopilotMode. RFQ-bound threads carry the manager UUID in
 * ``rfqId``; the copilot's access stage handles UUID-or-code dispatch
 * (Batch 9.1), so passing the UUID is correct.
 */
function currentRfqCodeFromMode(mode: CopilotMode): string | null {
  if (mode.kind === "rfq_bound") return mode.rfqId;
  return null;
}

// ── public API — domain types only ────────────────────────────────────────────

export interface OpenThreadResult {
  threadId: string;
  messages: CopilotMessage[];
}

export async function openThread(mode: CopilotMode): Promise<OpenThreadResult> {
  const response = await requestJson<WireOpenThreadResponse>(
    buildUrl("/threads/open"),
    {
      method: "POST",
      body: JSON.stringify({ mode: toWireMode(mode) }),
    },
  );
  return {
    threadId: response.thread_id,
    messages: response.messages.map(toDomainMessage),
  };
}

export interface NewThreadResult {
  threadId: string;
}

export async function createNewThread(mode: CopilotMode): Promise<NewThreadResult> {
  const response = await requestJson<WireNewThreadResponse>(
    buildUrl("/threads/new"),
    {
      method: "POST",
      body: JSON.stringify({ mode: toWireMode(mode) }),
    },
  );
  return { threadId: response.thread_id };
}

export interface TurnResult {
  userMessageId: string;
  assistantMessage: CopilotMessage;
  /** Path the copilot routed through (e.g. ``"path_4"``,
   * ``"path_8_5"``). Optional metadata for UI hints (different style
   * for safety-fallback answers); null when the backend didn't return it. */
  path: string | null;
  /** Reason code for Path 8.x answers (e.g. ``"no_evidence"``,
   * ``"manager_auth_failed"``). null on normal Path 1 / Path 4 answers. */
  reasonCode: string | null;
  /** Resolved RFQ code (Path 4 only). null otherwise. */
  targetRfqCode: string | null;
}

/**
 * Send one turn through the v4 trust-boundary /v2 lane.
 *
 * Why /v2 (Slice 1): every turn now goes through FastIntake or the
 * GPT-4o Planner, then through the trust-boundary pipeline. Out-of-
 * scope, forbidden-field, and unsupported asks route to safe Path 8
 * templates instead of being LLM-composed answers (which /v1 would
 * happily fabricate, e.g. "data does not include win probability").
 *
 * Page context: RFQ-bound mode carries the RFQ identifier in
 * ``mode.rfqId`` (a UUID). We pass it as ``current_rfq_code`` so the
 * planner's page-default emission resolves to the right RFQ. The
 * backend's access stage handles UUID-or-code dispatch.
 *
 * Response mapping: /v2 returns a ``V2TurnResponse`` with the answer
 * text + routing metadata. We synthesize ``CopilotMessage`` ids on
 * the client because /v2 doesn't return them in the legacy /v1
 * shape (turns are persisted to the ``execution_records`` forensics
 * table; ids there serve a different purpose and aren't message ids).
 */
export async function sendTurn(
  threadId: string,
  userMessage: string,
  mode: CopilotMode,
): Promise<TurnResult> {
  const response = await requestJson<WireV2TurnResponse>(
    buildV2Url(`/threads/${encodeURIComponent(threadId)}/turn`),
    {
      method: "POST",
      body: JSON.stringify({
        message: userMessage,
        current_rfq_code: currentRfqCodeFromMode(mode),
      }),
    },
  );
  const assistantMessage: CopilotMessage = {
    // /v2 doesn't return per-message ids -- mint client-side so the UI
    // can key off them. Use turn_id when present so the assistant id
    // is at least correlated to the persisted execution_record.
    id: response.turn_id ?? crypto.randomUUID(),
    role: "assistant",
    content: response.answer,
    createdAt: new Date().toISOString(),
  };
  return {
    // /v2 has no concept of a separate ``user_message_id``; the user
    // message is recorded as part of the execution_record. The caller
    // already minted a client-side id when dispatching the user
    // message, so we return the same scheme here.
    userMessageId: crypto.randomUUID(),
    assistantMessage,
    path: response.path,
    reasonCode: response.reason_code,
    targetRfqCode: response.target_rfq_code,
  };
}

export async function listThreads(mode: CopilotMode): Promise<CopilotThreadSummary[]> {
  const response = await requestJson<WireListThreadsResponse>(
    buildUrl("/threads/list"),
    {
      method: "POST",
      body: JSON.stringify({ mode: toWireMode(mode) }),
    },
  );
  return response.threads.map(toDomainThreadSummary);
}

export async function loadThread(threadId: string): Promise<OpenThreadResult> {
  const response = await requestJson<WireThreadDetail>(
    buildUrl(`/threads/${encodeURIComponent(threadId)}`),
    { method: "GET" },
  );
  return {
    threadId: response.thread_id,
    messages: response.messages.map(toDomainMessage),
  };
}
