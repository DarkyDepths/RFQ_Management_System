import type { CopilotMessage, CopilotMode } from "@/types/copilot";

export const MOCK_REPLY_DELAY_MS = 800;

const GENERAL_REPLY =
  "I'm running in MVP demo mode. I can show the copilot conversation experience now; real portfolio grounding will be connected in the next batches.";

function rfqBoundReply(rfqLabel: string): string {
  return `I'm running in MVP demo mode for ${rfqLabel}. I can show the RFQ Copilot experience now; real RFQ details such as deadline, stage, owner, and blockers will be grounded through rfq_manager_ms in the next batches.`;
}

export function generateMockReply(mode: CopilotMode): CopilotMessage {
  const content = mode.kind === "general" ? GENERAL_REPLY : rfqBoundReply(mode.rfqLabel);

  return {
    id: crypto.randomUUID(),
    role: "assistant",
    content,
    createdAt: new Date().toISOString(),
  };
}
