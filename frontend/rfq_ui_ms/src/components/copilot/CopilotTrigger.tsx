"use client";

import { Sparkles } from "lucide-react";

import { useAppShell } from "@/context/app-shell-context";
import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

export function CopilotTrigger() {
  const { sidebarCollapsed } = useAppShell();
  const { openCopilot } = useCopilot();

  return (
    <button
      type="button"
      onClick={() => openCopilot({ kind: "general" })}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
        "bg-primary/8 text-primary hover:bg-primary/12 dark:bg-primary/10",
        sidebarCollapsed && "lg:justify-center lg:px-0",
      )}
    >
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/15 text-primary">
        <Sparkles className="h-4 w-4" />
      </div>
      {!sidebarCollapsed ? <span className="truncate">RFQ Copilot</span> : null}
    </button>
  );
}
