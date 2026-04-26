"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Clock,
  Loader2,
  MessageSquarePlus,
  PanelLeftClose,
  PanelLeftOpen,
  Sparkles,
} from "lucide-react";

import { CopilotComposer } from "@/components/copilot/CopilotComposer";
import { CopilotEmptyState } from "@/components/copilot/CopilotEmptyState";
import { CopilotHistorySidebar } from "@/components/copilot/CopilotHistorySidebar";
import { CopilotMessages } from "@/components/copilot/CopilotMessages";
import { Button } from "@/components/ui/button";
import { useCopilot } from "@/hooks/useCopilot";
import { cn } from "@/lib/utils";

export function CopilotPage() {
  const { mode, messages, status, openCopilot, newChat } = useCopilot();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Ensure conversation context is in general mode whenever the page mounts.
  // This handles the case where the user opened an RFQ-bound drawer earlier
  // and now wants to switch to the workspace-wide assistant.
  useEffect(() => {
    if (mode.kind !== "general") {
      openCopilot({ kind: "general" });
    } else if (status === "idle" && messages.length === 0) {
      openCopilot({ kind: "general" });
    }
    // Intentionally only run on mount — subsequent mode switches are user-driven.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-[calc(100dvh-9rem)] flex-col gap-6">
      {/* ─── Header ─── */}
      <section className="surface-panel relative overflow-hidden p-6 lg:p-8">
        <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-primary/[0.08] to-transparent" />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/15 to-primary/[0.03] text-primary ring-1 ring-primary/20">
              <Sparkles className="h-7 w-7" strokeWidth={1.5} />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-primary animate-breathe" />
            </div>
            <div>
              <div className="section-kicker">Workspace Copilot</div>
              <h1 className="mt-2 text-display text-3xl font-semibold tracking-tight text-foreground lg:text-4xl">
                RFQ Copilot
              </h1>
              <p className="mt-2 max-w-xl text-sm leading-relaxed text-muted-foreground">
                Ask anything about your portfolio — lifecycle posture, scoring
                rules, blocker patterns, or how to advance a specific RFQ.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen((v) => !v)}
              aria-label={sidebarOpen ? "Hide history" : "Show history"}
              aria-pressed={sidebarOpen}
            >
              {sidebarOpen ? (
                <PanelLeftClose className="h-4 w-4" strokeWidth={1.75} />
              ) : (
                <PanelLeftOpen className="h-4 w-4" strokeWidth={1.75} />
              )}
              <span className="hidden sm:inline">History</span>
            </Button>
            <Button variant="secondary" size="sm" onClick={newChat}>
              <MessageSquarePlus className="h-4 w-4" strokeWidth={1.75} />
              New chat
            </Button>
          </div>
        </div>
      </section>

      {/* ─── Conversation surface ─── */}
      <section className="surface-panel relative flex flex-1 overflow-hidden">
        {/* History sidebar */}
        <div
          className={cn(
            "overflow-hidden transition-all duration-200 ease-in-out",
            sidebarOpen ? "w-56 opacity-100" : "w-0 opacity-0",
          )}
        >
          {sidebarOpen && <CopilotHistorySidebar />}
        </div>

        {/* Chat area */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto">
            {status === "loading" && messages.length === 0 ? (
              <div
                role="status"
                aria-label="Loading conversation"
                className="flex h-full min-h-[320px] items-center justify-center"
              >
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : status === "error" && messages.length === 0 ? (
              <div
                role="alert"
                className="flex h-full min-h-[320px] flex-col items-center justify-center gap-3 px-6 text-center"
              >
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-destructive/25 bg-destructive/10 text-destructive">
                  <AlertCircle className="h-5 w-5" strokeWidth={1.75} />
                </div>
                <p className="max-w-sm text-sm text-muted-foreground">
                  Couldn&apos;t reach the copilot service. Refresh the page or try
                  again in a moment.
                </p>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full min-h-[420px] items-center justify-center">
                <div className="w-full max-w-xl">
                  <CopilotEmptyState />
                </div>
              </div>
            ) : (
              <div className="mx-auto w-full max-w-3xl">
                <CopilotMessages />
              </div>
            )}
          </div>

          <div className="mx-auto w-full max-w-3xl">
            <CopilotComposer />
          </div>
        </div>
      </section>
    </div>
  );
}
