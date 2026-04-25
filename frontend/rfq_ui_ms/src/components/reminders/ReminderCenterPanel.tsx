"use client";

import { useMemo, useState } from "react";
import { BellRing, RefreshCw } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import { ReminderDetailDialog } from "@/components/reminders/ReminderDetailDialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  processReminders,
  resolveReminder,
  sendReminderTestEmail,
  updateReminderRule,
} from "@/connectors/manager/reminders";
import type { RolePermissions } from "@/config/role-permissions";
import { useToast } from "@/context/toast-context";
import { useReminderCenter } from "@/hooks/use-reminder-center";
import type { ReminderModel } from "@/models/manager/rfq";
import {
  getReminderScopeLabel,
  getReminderTypeLabel,
  sortRemindersForDisplay,
} from "@/utils/reminder";

const reminderStatusTone: Record<string, "steel" | "gold" | "rose" | "emerald"> = {
  open: "steel",
  overdue: "rose",
  resolved: "emerald",
};

export function ReminderCenterPanel({
  permissions,
}: {
  permissions: RolePermissions;
}) {
  const reminders = useReminderCenter();
  const { pushToast } = useToast();
  const [selectedReminder, setSelectedReminder] = useState<ReminderModel | null>(null);
  const [showAllReminders, setShowAllReminders] = useState(false);

  const sortedReminders = useMemo(
    () => sortRemindersForDisplay(reminders.reminders),
    [reminders.reminders],
  );
  const visibleReminders = showAllReminders
    ? sortedReminders
    : sortedReminders.slice(0, 8);
  const hiddenReminderCount = Math.max(
    sortedReminders.length - visibleReminders.length,
    0,
  );

  if (!permissions.canViewPortfolio || !permissions.canManageReminders) {
    return null;
  }

  async function runAction<T>(
    action: () => Promise<T>,
    successDescription: string,
  ) {
    const result = await action();
    reminders.refresh();
    pushToast({
      title: "Reminder Center updated",
      description: successDescription,
      tone: "success",
    });
    return result;
  }

  async function handleResolveReminder(reminderId: string) {
    await runAction(
      () => resolveReminder(reminderId),
      "Reminder resolved.",
    );
  }

  async function handleProcessReminders() {
    const message = await runAction(
      () => processReminders(),
      "Manual/admin reminder batch run completed.",
    );
    pushToast({
      title: "Reminder batch",
      description: message,
      tone: "info",
    });
  }

  async function handleReminderTest() {
    const message = await runAction(
      () => sendReminderTestEmail(),
      "Reminder test action completed.",
    );
    pushToast({
      title: "Reminder test",
      description: message,
      tone: "info",
    });
  }

  async function handleToggleReminderRule(ruleId: string, isActive: boolean) {
    await runAction(
      () => updateReminderRule(ruleId, isActive),
      `Reminder rule ${isActive ? "enabled" : "disabled"}.`,
    );
  }

  return (
    <>
      <section className="surface-panel p-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="section-kicker">
              <BellRing className="h-3.5 w-3.5" />
              Reminder Center
            </div>
            <h2 className="mt-3 text-lg font-semibold text-foreground">
              Service-wide reminder controls live here
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              RFQ pages stay focused on reminders attached to one pursuit. Stats, rule toggles,
              manual batch runs, and portfolio reminder visibility belong here instead of inside
              a single RFQ workspace.
            </p>
          </div>
          <Badge variant="gold">Manager-owned</Badge>
        </div>

        {reminders.loading ? (
          <div className="mt-5 grid gap-4 xl:grid-cols-2">
            <SkeletonCard className="h-[220px]" lines={6} />
            <SkeletonCard className="h-[220px]" lines={6} />
          </div>
        ) : reminders.error ? (
          <div className="mt-5">
            <EmptyState
              description={reminders.error}
              title="Reminder Center unavailable"
            />
          </div>
        ) : (
          <div className="mt-5 space-y-5">
            {reminders.stats ? (
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                <div className="stat-cell">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Open Reminders
                  </div>
                  <div className="mt-1 text-lg font-semibold text-foreground">
                    {reminders.stats.openTasks}
                  </div>
                </div>
                <div className="stat-cell">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Overdue Reminders
                  </div>
                  <div className="mt-1 text-lg font-semibold text-foreground">
                    {reminders.stats.overdueTasks}
                  </div>
                </div>
                <div className="stat-cell">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    Due This Week
                  </div>
                  <div className="mt-1 text-lg font-semibold text-foreground">
                    {reminders.stats.dueThisWeek}
                  </div>
                </div>
                <div className="stat-cell">
                  <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                    RFQs With Active Reminders
                  </div>
                  <div className="mt-1 text-lg font-semibold text-foreground">
                    {reminders.stats.withActiveReminders}
                  </div>
                </div>
              </div>
            ) : null}

            <div className="flex flex-wrap justify-end gap-2">
              <Button onClick={() => void handleReminderTest()} size="sm" variant="ghost">
                <BellRing className="h-3.5 w-3.5" />
                Test Email
              </Button>
              <Button onClick={() => void handleProcessReminders()} size="sm" variant="secondary">
                <RefreshCw className="h-3.5 w-3.5" />
                Run Batch Now
              </Button>
            </div>

            <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
              <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-foreground">Reminder Rules</div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Automatic reminders are batch-driven. Unsupported rule scopes stay inert until
                      the domain has a real generating condition.
                    </p>
                  </div>
                  <Badge variant="steel">{reminders.rules.length} rule(s)</Badge>
                </div>

                <div className="mt-4 space-y-3">
                  {reminders.rules.map((rule) => (
                    <div
                      key={rule.id}
                      className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3 first:border-t-0 first:pt-0"
                    >
                      <div>
                        <div className="text-sm font-medium text-foreground">{rule.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {rule.scope}
                          {rule.description ? ` · ${rule.description}` : ""}
                        </div>
                      </div>
                      <Button
                        onClick={() => void handleToggleReminderRule(rule.id, !rule.isActive)}
                        size="sm"
                        variant="secondary"
                      >
                        {rule.isActive ? "Disable" : "Enable"}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-sm font-semibold text-foreground">Service-wide Reminders</div>
                    <p className="mt-1 text-sm text-muted-foreground">
                      Managers can inspect and resolve portfolio reminders here without mixing those
                      controls into one RFQ page. Manual reminders can be resolved here; automatic
                      reminders close when their generating condition is no longer true. The stats
                      above track active workload; the list below keeps reminder records visible,
                      including resolved history.
                    </p>
                  </div>
                  <Badge variant="steel">{sortedReminders.length} records</Badge>
                </div>

                {sortedReminders.length > 0 ? (
                  <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-xs text-muted-foreground">
                    <span>
                      Showing {visibleReminders.length} of {sortedReminders.length} records, sorted
                      by overdue first.
                    </span>
                    {hiddenReminderCount > 0 ? (
                      <Button
                        onClick={() => setShowAllReminders(true)}
                        size="sm"
                        variant="ghost"
                      >
                        Show all records
                      </Button>
                    ) : showAllReminders && sortedReminders.length > 8 ? (
                      <Button
                        onClick={() => setShowAllReminders(false)}
                        size="sm"
                        variant="ghost"
                      >
                        Show fewer records
                      </Button>
                    ) : null}
                  </div>
                ) : null}

                <div className="mt-4 space-y-3">
                  {sortedReminders.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No reminder records are currently available across the portfolio.
                    </p>
                  ) : (
                    visibleReminders.map((reminder) => (
                      <div key={reminder.id} className="stat-cell">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {reminder.message}
                            </div>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                              <Badge variant={reminderStatusTone[reminder.status] ?? "steel"}>
                                {reminder.status}
                              </Badge>
                              <Badge variant="outline">{getReminderScopeLabel(reminder)}</Badge>
                              <Badge variant="outline">{reminder.source}</Badge>
                              <Badge variant="outline">{getReminderTypeLabel(reminder.type)}</Badge>
                              <span>due {reminder.dueLabel}</span>
                              {reminder.rfqCode ? <span>· {reminder.rfqCode}</span> : null}
                              {reminder.rfqStageName ? <span>· {reminder.rfqStageName}</span> : null}
                              {reminder.assignedTo ? <span>· {reminder.assignedTo}</span> : null}
                              {reminder.delayDays > 0 ? (
                                <span>· {reminder.delayDays} day(s) late</span>
                              ) : null}
                              {reminder.sendCount > 0 ? (
                                <span>· sent {reminder.sendCount} time(s)</span>
                              ) : null}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              onClick={() => setSelectedReminder(reminder)}
                              size="sm"
                              variant="ghost"
                            >
                              View details
                            </Button>
                            {reminder.status !== "resolved" && reminder.source === "manual" ? (
                              <Button
                                onClick={() => void handleResolveReminder(reminder.id)}
                                size="sm"
                                variant="ghost"
                              >
                                Resolve
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      <ReminderDetailDialog
        onClose={() => setSelectedReminder(null)}
        reminder={selectedReminder}
      />
    </>
  );
}
