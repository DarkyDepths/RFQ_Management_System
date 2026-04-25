"use client";

import { useState, type ReactNode } from "react";
import { ArrowRight, FilePlus2, RefreshCw, RotateCw, WandSparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { RolePermissions } from "@/config/role-permissions";
import {
  getRfqStatusLabel,
  getTerminalRfqOutcome,
} from "@/lib/rfq-status-display";
import type { ReprocessKind } from "@/models/intelligence/artifacts";
import type { IntelligenceLifecycleTriggerResult } from "@/models/intelligence/triggers";
import type { ManagerRfqStatus } from "@/models/manager/rfq";

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function formatTriggerMessage(result: IntelligenceLifecycleTriggerResult) {
  if (result.eventType === "rfq.created") {
    if (result.status === "duplicate") {
      return "Package intelligence is already up to date for this RFQ.";
    }

    if (result.status === "processed") {
      return "Package intelligence is ready. You can now review the initial summary of the client RFQ package.";
    }
  }

  if (result.eventType === "workbook.uploaded") {
    if (result.status === "duplicate") {
      return "Workbook enrichment is already up to date for this RFQ.";
    }

    if (result.status === "processed_with_failures") {
      return "Workbook enrichment finished with follow-up items. Review the workbook findings before relying on them.";
    }

    if (result.status === "processed") {
      return "Workbook enrichment is ready. You can now review how the estimator workbook compares with the RFQ package.";
    }
  }

  if (result.eventType === "outcome.recorded") {
    if (result.status === "duplicate") {
      return "Outcome-based enrichment is already current for this RFQ.";
    }

    if (result.status === "processed") {
      return "Outcome enrichment refreshed for this RFQ.";
    }
  }

  return result.status.replaceAll("_", " ");
}

function PhaseCard({
  action,
  badge,
  description,
  title,
}: {
  action?: ReactNode;
  badge: ReactNode;
  description: string;
  title: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-foreground">{title}</div>
          <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {description}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {badge}
          {action}
        </div>
      </div>
    </div>
  );
}

export function IntelligenceActionsPanel({
  onRefresh,
  onReprocess,
  onTriggerIntake,
  onTriggerOutcome,
  onTriggerWorkbook,
  permissions,
  rfqOutcomeReason,
  rfqStatus,
  sourcePackageAvailable,
  sourcePackageUpdatedLabel,
  workbookAvailable,
  workbookUpdatedLabel,
}: {
  onRefresh: () => void;
  onReprocess: (kind: ReprocessKind) => Promise<{ message: string }>;
  onTriggerIntake: () => Promise<IntelligenceLifecycleTriggerResult>;
  onTriggerOutcome: (input: {
    outcome: "awarded" | "lost" | "cancelled";
    outcomeReason?: string;
  }) => Promise<IntelligenceLifecycleTriggerResult>;
  onTriggerWorkbook: () => Promise<IntelligenceLifecycleTriggerResult>;
  permissions: RolePermissions;
  rfqOutcomeReason?: string;
  rfqStatus: ManagerRfqStatus;
  sourcePackageAvailable: boolean;
  sourcePackageUpdatedLabel?: string;
  workbookAvailable: boolean;
  workbookUpdatedLabel?: string;
}) {
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const terminalOutcome = getTerminalRfqOutcome(rfqStatus);
  const canTrigger = permissions.canTriggerIntelligence;

  async function runAction<T>(
    key: string,
    task: () => Promise<T>,
    formatMessage: (result: T) => string,
  ) {
    setBusyAction(key);
    setError("");
    setMessage("");

    try {
      const result = await task();
      setMessage(formatMessage(result));
      return result;
    } catch (actionError) {
      setError(
        getErrorMessage(
          actionError,
          "The intelligence action could not be completed.",
        ),
      );
      return null;
    } finally {
      setBusyAction(null);
    }
  }

  return (
    <div className="space-y-5">
      {message ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/8 p-4 text-sm text-emerald-700 dark:text-emerald-300">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-700 dark:text-rose-300">
          {error}
        </div>
      ) : null}

      {canTrigger ? (
        <div className="surface-panel p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">
                Intelligence Phases
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                Package intelligence begins once the RFQ package is available. Workbook enrichment remains a later-phase step after the estimator workbook exists.
              </p>
            </div>
            <Button onClick={onRefresh} size="sm" variant="ghost">
              <RefreshCw className="h-3.5 w-3.5" />
              Refresh
            </Button>
          </div>

          <div className="mt-5 space-y-3">
            <PhaseCard
              title="Package Intelligence"
              description={
                sourcePackageAvailable
                  ? `RFQ package is available${sourcePackageUpdatedLabel ? ` and was last updated ${sourcePackageUpdatedLabel}` : ""}. Generate the first package summary when you are ready to review the incoming request.`
                  : "Waiting for RFQ package upload. Package intelligence starts as soon as the incoming client RFQ package is attached."
              }
              badge={
                <Badge variant={sourcePackageAvailable ? "emerald" : "pending"}>
                  {sourcePackageAvailable ? "Package Ready" : "Waiting on Package"}
                </Badge>
              }
              action={
                sourcePackageAvailable ? (
                  <Button
                    disabled={busyAction === "trigger-intake"}
                    onClick={() =>
                      void runAction("trigger-intake", onTriggerIntake, formatTriggerMessage)
                    }
                    size="sm"
                    variant="secondary"
                  >
                    <WandSparkles className="h-3.5 w-3.5" />
                    Run Package Intelligence
                  </Button>
                ) : undefined
              }
            />

            <PhaseCard
              title="Workbook Enrichment"
              description={
                workbookAvailable
                  ? `Late-lifecycle estimator workbook is available${workbookUpdatedLabel ? ` and was last updated ${workbookUpdatedLabel}` : ""}. Run workbook enrichment when you want to compare the estimator output with the original RFQ package.`
                  : "Waiting for workbook upload. Workbook enrichment starts only after the estimator workbook exists."
              }
              badge={
                <Badge variant={workbookAvailable ? "emerald" : "pending"}>
                  {workbookAvailable ? "Workbook Ready" : "Waiting on Workbook"}
                </Badge>
              }
              action={
                workbookAvailable ? (
                  <Button
                    disabled={busyAction === "trigger-workbook"}
                    onClick={() =>
                      void runAction("trigger-workbook", onTriggerWorkbook, formatTriggerMessage)
                    }
                    size="sm"
                    variant="secondary"
                  >
                    <FilePlus2 className="h-3.5 w-3.5" />
                    Run Workbook Enrichment
                  </Button>
                ) : undefined
              }
            />

            <PhaseCard
              title="Historical Insights"
              description="Historical insights unlock only after enough completed RFQs and retained workbooks exist. For now, the platform is still building that learning base."
              badge={<Badge variant="steel">Maturity Gated</Badge>}
            />
          </div>
        </div>
      ) : null}

      {permissions.canReprocessArtifacts ? (
        <div className="surface-panel p-5">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h3 className="text-sm font-semibold text-foreground">
                Support Actions
              </h3>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                These manual support actions remain available as secondary controls while lifecycle automation is still being completed.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <Button
                disabled={!terminalOutcome || busyAction === "trigger-outcome"}
                onClick={() =>
                  terminalOutcome
                    ? void runAction(
                        "trigger-outcome",
                        () =>
                          onTriggerOutcome({
                            outcome: terminalOutcome,
                            outcomeReason: rfqOutcomeReason,
                          }),
                        formatTriggerMessage,
                      )
                    : undefined
                }
                size="sm"
                variant="secondary"
              >
                <ArrowRight className="h-3.5 w-3.5" />
                Refresh Outcome Enrichment
              </Button>
              <Button
                disabled={busyAction === "reprocess:intake"}
                onClick={() =>
                  void runAction("reprocess:intake", () => onReprocess("intake"), (result) => result.message)
                }
                size="sm"
                variant="secondary"
              >
                <RotateCw className="h-3.5 w-3.5" />
                Reprocess Package
              </Button>
              <Button
                disabled={busyAction === "reprocess:workbook"}
                onClick={() =>
                  void runAction("reprocess:workbook", () => onReprocess("workbook"), (result) => result.message)
                }
                size="sm"
                variant="secondary"
              >
                <RotateCw className="h-3.5 w-3.5" />
                Reprocess Workbook
              </Button>
              <Badge variant="steel">Status: {getRfqStatusLabel(rfqStatus)}</Badge>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
