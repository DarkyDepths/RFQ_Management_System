"use client";

import type { ReminderModel } from "@/models/manager/rfq";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  getReminderScopeLabel,
  getReminderTypeLabel,
} from "@/utils/reminder";

const reminderStatusTone: Record<string, "emerald" | "rose" | "steel"> = {
  open: "steel",
  overdue: "rose",
  resolved: "emerald",
};

export function ReminderDetailDialog({
  onClose,
  reminder,
}: {
  onClose: () => void;
  reminder: ReminderModel | null;
}) {
  if (!reminder) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6">
      <div className="max-h-[90vh] w-full max-w-3xl overflow-hidden rounded-[2rem] border border-white/10 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.98))] shadow-[0_30px_120px_rgba(15,23,42,0.28)] backdrop-blur">
        <div className="flex items-start justify-between gap-4 border-b border-border/70 px-6 py-5">
          <div>
            <div className="section-kicker">Reminder Detail</div>
            <h3 className="mt-3 text-xl font-semibold text-foreground">
              {reminder.message}
            </h3>
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
              Review the reminder context, timing, ownership, and execution trace without leaving
              the current screen.
            </p>
          </div>
          <Button onClick={onClose} size="sm" variant="ghost">
            Close
          </Button>
        </div>

        <div className="max-h-[calc(90vh-96px)] overflow-y-auto px-6 py-5">
          <div className="flex flex-wrap gap-2">
            <Badge variant={reminderStatusTone[reminder.status] ?? "steel"}>
              {reminder.status}
            </Badge>
            <Badge variant="outline">{getReminderScopeLabel(reminder)}</Badge>
            <Badge variant="outline">{reminder.source}</Badge>
            <Badge variant="outline">{getReminderTypeLabel(reminder.type)}</Badge>
          </div>

          <div className="mt-5 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                RFQ
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.rfqCode
                  ? `${reminder.rfqCode} · ${reminder.rfqName ?? "RFQ"}`
                  : reminder.rfqName ?? "RFQ context not available"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Stage
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.rfqStageName ?? "RFQ-level reminder"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Due Date
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">{reminder.dueLabel}</div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Assigned Owner
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.assignedTo ?? "Not assigned"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Created By
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.createdBy ?? "System"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Created At
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.createdLabel}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Last Sent
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.lastSentLabel ?? "Not sent yet"}
              </div>
            </div>
            <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Send Count
              </div>
              <div className="mt-1 text-sm font-medium text-foreground">
                {reminder.sendCount}
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-2xl border border-border bg-card/80 p-4">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Reminder Message
            </div>
            <div className="mt-3 whitespace-pre-wrap text-sm leading-relaxed text-foreground">
              {reminder.message}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
