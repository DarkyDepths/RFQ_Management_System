"use client";

import { AlertCircle, Loader2, MessageSquare } from "lucide-react";

import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";
import type { CopilotThreadSummary } from "@/types/copilot";

function groupByDate(threads: CopilotThreadSummary[]) {
  const DAY = 86_400_000;
  const todayStart = new Date();
  todayStart.setHours(0, 0, 0, 0);
  const yesterdayStart = new Date(todayStart.getTime() - DAY);
  const weekStart = new Date(todayStart.getTime() - 7 * DAY);

  const groups: { label: string; items: CopilotThreadSummary[] }[] = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Previous 7 days", items: [] },
    { label: "Older", items: [] },
  ];

  for (const t of threads) {
    const d = new Date(t.lastActivityAt);
    if (d >= todayStart) groups[0].items.push(t);
    else if (d >= yesterdayStart) groups[1].items.push(t);
    else if (d >= weekStart) groups[2].items.push(t);
    else groups[3].items.push(t);
  }

  return groups.filter((g) => g.items.length > 0);
}

export function CopilotHistorySidebar() {
  const { threads, threadsStatus, threadId, switchToThread } = useCopilot();

  const groups = groupByDate(threads);

  return (
    <aside className="flex w-56 shrink-0 flex-col overflow-hidden border-r border-border/60">
      <div className="flex items-center px-3 pb-2 pt-3">
        <span className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/60">
          Conversations
        </span>
      </div>

      <div className="flex-1 overflow-y-auto">
        {threadsStatus === "loading" && threads.length === 0 ? (
          <div className="flex h-20 items-center justify-center">
            <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
          </div>
        ) : threadsStatus === "error" && threads.length === 0 ? (
          <div className="flex h-20 flex-col items-center justify-center gap-1 px-4 text-center">
            <AlertCircle className="h-4 w-4 text-muted-foreground/60" />
            <p className="text-[11px] text-muted-foreground">Failed to load history</p>
          </div>
        ) : groups.length === 0 ? (
          <div className="flex h-20 flex-col items-center justify-center gap-1 px-4 text-center">
            <MessageSquare className="h-4 w-4 text-muted-foreground/60" />
            <p className="text-[11px] text-muted-foreground">No previous chats</p>
          </div>
        ) : (
          <nav aria-label="Conversation history">
            {groups.map((group) => (
              <div key={group.label}>
                <div className="px-3 pb-1 pt-3">
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/50">
                    {group.label}
                  </span>
                </div>
                {group.items.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    title={t.preview || "New conversation"}
                    onClick={() => switchToThread(t.id)}
                    className={cn(
                      "flex w-full items-start gap-1.5 rounded-none px-3 py-2 text-left text-xs transition-colors",
                      "hover:bg-accent/10 active:bg-accent/20",
                      t.id === threadId
                        ? "bg-primary/8 font-medium text-primary"
                        : "text-foreground/75",
                    )}
                  >
                    <span className="mt-px line-clamp-2 leading-snug">
                      {t.preview || "New conversation"}
                    </span>
                  </button>
                ))}
              </div>
            ))}
          </nav>
        )}
      </div>
    </aside>
  );
}
