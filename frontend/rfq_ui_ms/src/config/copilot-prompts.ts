import type { CopilotMode } from "@/types/copilot";

export interface CopilotSuggestedPrompt {
  id: string;
  label: string;
  prompt: string;
}

const generalPrompts: CopilotSuggestedPrompt[] = [
  { id: "g-overdue", label: "What's overdue this week?", prompt: "What's overdue this week?" },
  { id: "g-at-risk", label: "Show me RFQs at risk", prompt: "Show me RFQs at risk." },
  { id: "g-due-soon", label: "Which RFQs are due soon?", prompt: "Which RFQs are due soon?" },
  { id: "g-summary", label: "Summarize my portfolio activity", prompt: "Summarize my portfolio activity." },
];

const rfqBoundPrompts: CopilotSuggestedPrompt[] = [
  { id: "r-deadline", label: "What's the deadline?", prompt: "What's the deadline?" },
  { id: "r-stage", label: "What's the current stage?", prompt: "What's the current stage?" },
  { id: "r-owner", label: "Who owns this RFQ?", prompt: "Who owns this RFQ?" },
  { id: "r-blockers", label: "Any blockers I should know about?", prompt: "Any blockers I should know about?" },
];

export function getSuggestedPrompts(mode: CopilotMode): CopilotSuggestedPrompt[] {
  return mode.kind === "general" ? generalPrompts : rfqBoundPrompts;
}
