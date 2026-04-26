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
  WireTurnResponse,
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
}

export async function sendTurn(
  threadId: string,
  userMessage: string,
): Promise<TurnResult> {
  const response = await requestJson<WireTurnResponse>(
    buildUrl(`/threads/${encodeURIComponent(threadId)}/turn`),
    {
      method: "POST",
      body: JSON.stringify({ user_message: userMessage }),
    },
  );
  return {
    userMessageId: response.message_id,
    assistantMessage: toDomainMessage(response.assistant_message),
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
