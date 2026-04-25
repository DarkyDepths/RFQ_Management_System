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

// Wire DTOs — frozen now to mirror the eventual backend (snake_case = Python defaults).
// A translator layer will map these to/from the camelCase domain types above when
// Batch 3 wires real fetch calls.

export interface OpenThreadRequest {
  mode: CopilotMode;
}

export interface OpenThreadResponse {
  thread_id: string;
  messages: CopilotMessage[];
}

export interface NewThreadRequest {
  mode: CopilotMode;
}

export interface NewThreadResponse {
  thread_id: string;
}

export interface TurnRequest {
  user_message: string;
}

export interface TurnResponse {
  message_id: string;
  assistant_message: CopilotMessage;
}

export type CopilotStatus = "idle" | "loading" | "error";
