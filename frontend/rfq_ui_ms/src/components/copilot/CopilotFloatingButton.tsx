"use client";

import { Sparkles } from "lucide-react";

import { useCopilot } from "@/hooks/useCopilot";

interface CopilotFloatingButtonProps {
  rfqId: string;
  rfqLabel: string;
}

export function CopilotFloatingButton({ rfqId, rfqLabel }: CopilotFloatingButtonProps) {
  const { openCopilot } = useCopilot();

  return (
    <button
      type="button"
      onClick={() => openCopilot({ kind: "rfq_bound", rfqId, rfqLabel })}
      aria-label="Open RFQ Copilot"
      className="fixed bottom-6 right-6 z-20 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-glow transition-transform hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2"
    >
      <Sparkles className="h-5 w-5" />
    </button>
  );
}
