"use client";

import { MessageSquarePlus, Sparkles, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCopilot } from "@/hooks/useCopilot";

export function CopilotHeader() {
  const { mode, closeCopilot, newChat } = useCopilot();

  const subtitle = mode.kind === "general" ? "General" : mode.rfqLabel;

  return (
    <div className="flex items-center justify-between gap-2 border-b border-border px-4 py-3">
      <div className="flex min-w-0 items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Sparkles className="h-4 w-4" />
        </div>
        <div className="min-w-0">
          <div className="truncate text-sm font-semibold leading-none text-foreground">
            RFQ Copilot
          </div>
          <div className="mt-1 truncate text-xs text-muted-foreground">{subtitle}</div>
        </div>
      </div>
      <div className="flex items-center gap-1">
        <Button
          variant="ghost"
          size="icon"
          aria-label="New chat"
          onClick={newChat}
          className="h-8 w-8"
        >
          <MessageSquarePlus className="h-4 w-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          aria-label="Close copilot"
          onClick={closeCopilot}
          className="h-8 w-8"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>
    </div>
  );
}
