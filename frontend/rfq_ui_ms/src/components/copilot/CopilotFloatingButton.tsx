"use client";

import { Sparkles } from "lucide-react";

import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

interface CopilotFloatingButtonProps {
  rfqId: string;
  rfqLabel: string;
}

const FAB_GUTTER_PX = 24; // matches bottom-6 / right-6

export function CopilotFloatingButton({ rfqId, rfqLabel }: CopilotFloatingButtonProps) {
  const { open, drawerWidth, isResizing, openCopilot } = useCopilot();

  const right = open ? drawerWidth + FAB_GUTTER_PX : FAB_GUTTER_PX;

  return (
    <button
      type="button"
      onClick={() => openCopilot({ kind: "rfq_bound", rfqId, rfqLabel })}
      aria-label="Open RFQ Copilot"
      style={{
        right,
        transition: isResizing ? "none" : "right 250ms ease-out",
      }}
      className={cn(
        "fixed bottom-6 z-20 flex h-14 w-14 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-glow",
        "hover:scale-105 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2",
        // transition-transform handles the hover scale; the right-position transition is inline above so we can disable it during drag.
        "transition-transform",
      )}
    >
      <Sparkles className="h-5 w-5" />
    </button>
  );
}
