"use client";

import Link from "next/link";
import { BellRing, ArrowRight } from "lucide-react";

import { SkeletonCard } from "@/components/common/SkeletonCard";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useReminderSummary } from "@/hooks/use-reminder-summary";

export function ReminderCenterSummaryCard() {
  const reminderSummary = useReminderSummary();

  return (
    <section className="surface-panel p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="section-kicker">
            <BellRing className="h-3.5 w-3.5" />
            Reminder Snapshot
          </div>
          <h2 className="mt-3 text-lg font-semibold text-foreground">
            Reminder health stays visible here
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
            Overview keeps a compact reminder snapshot for managers. Full rule controls,
            service-wide reminder records, and batch actions now live in the dedicated
            Reminder Center.
          </p>
        </div>
        <Badge variant="gold">Manager-only</Badge>
      </div>

      {reminderSummary.loading ? (
        <div className="mt-5">
          <SkeletonCard className="h-[180px]" lines={4} />
        </div>
      ) : reminderSummary.error ? (
        <div className="mt-5 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
          <div className="text-sm font-medium text-foreground">Reminder summary unavailable</div>
          <p className="mt-1 text-sm text-muted-foreground">{reminderSummary.error}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            <Button onClick={reminderSummary.refresh} size="sm" variant="secondary">
              Retry
            </Button>
          </div>
        </div>
      ) : reminderSummary.stats ? (
        <div className="mt-5 space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="stat-cell">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Open Reminders
              </div>
              <div className="mt-1 text-lg font-semibold text-foreground">
                {reminderSummary.stats.openTasks}
              </div>
            </div>
            <div className="stat-cell">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Overdue Reminders
              </div>
              <div className="mt-1 text-lg font-semibold text-foreground">
                {reminderSummary.stats.overdueTasks}
              </div>
            </div>
            <div className="stat-cell">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Due This Week
              </div>
              <div className="mt-1 text-lg font-semibold text-foreground">
                {reminderSummary.stats.dueThisWeek}
              </div>
            </div>
            <div className="stat-cell">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                RFQs With Active Reminders
              </div>
              <div className="mt-1 text-lg font-semibold text-foreground">
                {reminderSummary.stats.withActiveReminders}
              </div>
            </div>
          </div>

          <div className="flex justify-end">
            <Button asChild variant="secondary">
              <Link href="/reminders">
                Open Reminder Center
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      ) : null}
    </section>
  );
}
