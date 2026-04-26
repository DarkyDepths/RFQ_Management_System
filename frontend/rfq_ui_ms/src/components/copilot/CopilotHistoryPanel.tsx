"use client";

import { AlertCircle, ArrowLeft, Loader2, MessageSquare } from "lucide-react";

import { Button } from "@/components/ui/button";
import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";
import type { CopilotThreadSummary } from "@/types/copilot";

function relativeDate(iso: string): string {
  const d = new Date(iso);
  const diffMs = Date.now() - d.getTime();
  const diffDays = Math.floor(diffMs / 86_400_000);
  if (diffDays === 0)
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString([], { month: "short", day: "numeric" });
}

function ThreadRow({
  thread,
  active,
  onClick,
}: {
  thread: CopilotThreadSummary;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onClick}
        className={cn(
          "flex w-full flex-col gap-0.5 px-4 py-3 text-left transition-colors",
          "hover:bg-accent/10 active:bg-accent/20",
          active && "bg-primary/8",
        )}
      >
        <span
          className={cn(
            "line-clamp-2 text-sm leading-snug",
            active ? "font-medium text-primary" : "text-foreground",
          )}
        >
          {thread.preview || "New conversation"}
        </span>
        <span className="text-[11px] text-muted-foreground">
          {relativeDate(thread.lastActivityAt)}
        </span>
      </button>
    </li>
  );
}

export function CopilotHistoryPanel() {
  const { threads, threadsStatus, threadId, switchToThread, closeHistory } =
    useCopilot();

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      {/* Sub-header */}
      <div className="flex items-center gap-1 border-b border-border/40 px-2 py-2">
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          onClick={closeHistory}
          aria-label="Back to chat"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <span className="text-sm font-semibold text-foreground">Conversation history</span>
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {threadsStatus === "loading" && threads.length === 0 ? (
          <div className="flex h-32 items-center justify-center">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
          </div>
        ) : threadsStatus === "error" && threads.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center gap-2 text-center">
            <AlertCircle className="h-5 w-5 text-muted-foreground/60" />
            <p className="text-xs text-muted-foreground">Failed to load history</p>
          </div>
        ) : threads.length === 0 ? (
          <div className="flex h-32 flex-col items-center justify-center gap-2 px-6 text-center">
            <MessageSquare className="h-5 w-5 text-muted-foreground/60" />
            <p className="text-xs text-muted-foreground">
              No previous conversations for this RFQ
            </p>
          </div>
        ) : (
          <ul className="divide-y divide-border/30" aria-label="Past conversations">
            {threads.map((t) => (
              <ThreadRow
                key={t.id}
                thread={t}
                active={t.id === threadId}
                onClick={() => switchToThread(t.id)}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
