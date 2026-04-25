"use client";

import { useCopilotContext } from "@/context/copilot-context";

export function useCopilot() {
  const ctx = useCopilotContext();
  if (!ctx) {
    throw new Error("useCopilot must be used inside CopilotProvider");
  }
  return ctx;
}
