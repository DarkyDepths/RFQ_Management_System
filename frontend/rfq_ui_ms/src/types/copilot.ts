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
