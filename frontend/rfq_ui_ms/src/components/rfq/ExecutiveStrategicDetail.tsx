"use client";

import { motion } from "framer-motion";
import {
  AlertTriangle,
  Clock3,
  NotebookPen,
  Sparkles,
  Target,
  Workflow,
} from "lucide-react";

import { IntelligencePanel } from "@/components/intelligence/IntelligencePanel";
import { LifecycleProgressStageBox } from "@/components/rfq/LifecycleProgressStageBox";
import { LeadershipNotesPanel } from "@/components/rfq/LeadershipNotesPanel";
import { RFQStageTimeline } from "@/components/rfq/RFQStageTimeline";
import { RFQStatusChip } from "@/components/rfq/RFQStatusChip";
import { Badge } from "@/components/ui/badge";
import type { RolePermissions } from "@/config/role-permissions";
import type {
  IntelligenceResourceState,
  IntelligenceStaleNotice,
} from "@/hooks/use-rfq-intelligence";
import type { BriefingArtifactModel } from "@/models/intelligence/briefing";
import type { IntelligenceSnapshotModel } from "@/models/intelligence/snapshot";
import type {
  WorkbookProfileModel,
  WorkbookReviewModel,
} from "@/models/intelligence/workbook";
import type { RfqDetailModel } from "@/models/manager/rfq";
import {
  getRfqStatusLabel,
  getTerminalRfqOutcome,
} from "@/lib/rfq-status-display";
import { getBlockedStageHeadline, getRfqBlockedSignal } from "@/utils/blocker-signal";
import { intelligenceAvailabilityMeta } from "@/utils/status";

function buildDeliveryRisk(rfq: RfqDetailModel) {
  if (getTerminalRfqOutcome(rfq.status)) {
    return {
      detail: "Terminal RFQs no longer carry an active delivery risk.",
      label: "Closed",
      tone: "steel" as const,
    };
  }

  const dueAt = Date.parse(rfq.dueDateValue);
  if (Number.isNaN(dueAt)) {
    return {
      detail: "The due date is not available, so schedule posture is unclear.",
      label: "Schedule unknown",
      tone: "pending" as const,
    };
  }

  const diffDays = Math.ceil((dueAt - Date.now()) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) {
    return {
      detail: `${Math.abs(diffDays)} day(s) past due against ${rfq.dueLabel}.`,
      label: "Overdue",
      tone: "rose" as const,
    };
  }

  if (diffDays <= 5) {
    return {
      detail: `${diffDays} day(s) remaining to the current due date.`,
      label: "Due soon",
      tone: "gold" as const,
    };
  }

  return {
    detail: `${diffDays} day(s) remain before the current due date.`,
    label: "On track",
    tone: "emerald" as const,
  };
}

function resolveBlockerSignal(rfq: RfqDetailModel) {
  const blockedSignal = getRfqBlockedSignal(rfq);
  if (blockedSignal.reasonLabel) {
    return blockedSignal.reasonLabel;
  }

  if (blockedSignal.isBlocked) {
    return getBlockedStageHeadline(rfq) ?? `Blocked in ${rfq.stageLabel}`;
  }

  return rfq.summaryLine ?? "No blocker flagged.";
}

function resolveEscalationSignal(
  rfq: RfqDetailModel,
  intelligenceIsStale: boolean,
) {
  if (intelligenceIsStale) {
    return {
      detail: "Operational data changed after the latest intelligence artifact update.",
      label: "Refresh intelligence",
      tone: "gold" as const,
    };
  }

  if (rfq.stageHistory.some((stage) => stage.state === "blocked")) {
    return {
      detail: "A blocked workflow stage is asking for manager response and leadership watch.",
      label: "Manager intervention required",
      tone: "rose" as const,
    };
  }

  if (rfq.priority === "critical") {
    return {
      detail: "Critical RFQ. Keep it on leadership watch even if no blocker is open yet.",
      label: "Leadership watch",
      tone: "gold" as const,
    };
  }

  if (rfq.status === "lost" && rfq.outcomeReason) {
    return {
      detail: "Loss rationale is recorded and ready for leadership review.",
      label: "Outcome rationale captured",
      tone: "steel" as const,
    };
  }

  return {
    detail: "No active escalation signal is recorded right now.",
    label: "No escalation signal",
    tone: "emerald" as const,
  };
}

function buildWhyLeadershipShouldCare(
  rfq: RfqDetailModel,
  deliveryRisk: ReturnType<typeof buildDeliveryRisk>,
  escalationSignal: ReturnType<typeof resolveEscalationSignal>,
  staleIntel: IntelligenceStaleNotice | null,
) {
  const sentences = [
    `${rfq.title} is currently in ${rfq.stageLabel.toLowerCase()} with ${rfq.statusLabel.toLowerCase()} lifecycle posture.`,
  ];

  if (rfq.status === "lost" && rfq.outcomeReason) {
    sentences.push(`Recorded loss rationale: ${rfq.outcomeReason}`);
  } else if (deliveryRisk.label !== "On track" && deliveryRisk.label !== "Closed") {
    sentences.push(`Schedule posture is ${deliveryRisk.label.toLowerCase()} against ${rfq.dueLabel}.`);
  }

  const blockerSignal = resolveBlockerSignal(rfq);
  if (blockerSignal !== "No blocker flagged.") {
    sentences.push(`Current blocker or delay driver: ${blockerSignal}.`);
  }

  if (staleIntel) {
    sentences.push("Intelligence is stale relative to the latest operational update.");
  } else if (escalationSignal.label !== "No escalation signal") {
    sentences.push(`${escalationSignal.label}.`);
  }

  return sentences.slice(0, 3).join(" ");
}

function buildDelayDiagnosis(
  rfq: RfqDetailModel,
  deliveryRisk: ReturnType<typeof buildDeliveryRisk>,
) {
  const blockedSignal = getRfqBlockedSignal(rfq);

  if (blockedSignal.reasonLabel) {
    return {
      detail: blockedSignal.reasonLabel,
      headline: `Blocked at ${blockedSignal.stageLabel ?? rfq.stageLabel}`,
      source: "Captured blocker reason",
      tone: "rose" as const,
    };
  }

  if (blockedSignal.isBlocked) {
    const blockedHeadline = getBlockedStageHeadline(rfq) ?? `Blocked in ${rfq.stageLabel}`;
    return {
      detail:
        rfq.summaryLine ??
        `The RFQ is blocked in ${blockedSignal.stageLabel ?? rfq.stageLabel}.`,
      headline: blockedHeadline.replace("Blocked in", "Blocked at"),
      source: "Lifecycle signal",
      tone: "rose" as const,
    };
  }

  if (deliveryRisk.label === "Overdue" || deliveryRisk.label === "Due soon") {
    return {
      detail: deliveryRisk.detail,
      headline: "Schedule pressure is the primary delay signal",
      source: "Due-date posture",
      tone: deliveryRisk.tone,
    };
  }

  return {
    detail: rfq.summaryLine ?? "No active blocker or delay driver is currently recorded.",
    headline: "No material blocker is currently recorded",
    source: "Strategic summary",
    tone: "emerald" as const,
  };
}

function buildOutcomeState(rfq: RfqDetailModel) {
  switch (getTerminalRfqOutcome(rfq.status)) {
    case "lost":
      return {
        detail: rfq.outcomeReason ?? rfq.summaryLine ?? "Loss rationale is not yet recorded.",
        label: getRfqStatusLabel("lost"),
        tone: "rose" as const,
      };
    case "awarded":
      return {
        detail: rfq.outcomeReason ?? rfq.summaryLine ?? "Award rationale captured in the pursuit summary.",
        label: getRfqStatusLabel("awarded"),
        tone: "emerald" as const,
      };
    case "cancelled":
      return {
        detail: rfq.outcomeReason ?? "Cancellation rationale is available in the RFQ summary.",
        label: getRfqStatusLabel("cancelled"),
        tone: "steel" as const,
      };
    default:
      return {
        detail: "Outcome is still pending while the RFQ remains active.",
        label: "Active pursuit",
        tone: "steel" as const,
      };
  }
}

function buildFreshnessState(
  snapshot: IntelligenceResourceState<IntelligenceSnapshotModel | null>,
  staleIntel: IntelligenceStaleNotice | null,
) {
  if (staleIntel) {
    return {
      detail: `${staleIntel.message} Manager updated ${staleIntel.managerUpdatedLabel}.`,
      label: "Stale",
      tone: "amber" as const,
    };
  }

  if (snapshot.data?.updatedLabel) {
    return {
      detail: `Latest curated intelligence updated ${snapshot.data.updatedLabel}.`,
      label: "Current",
      tone: "emerald" as const,
    };
  }

  if (snapshot.loading) {
    return {
      detail: "Intelligence is still loading for this RFQ.",
      label: "Pending",
      tone: "pending" as const,
    };
  }

  return {
    detail: "Curated intelligence is not available yet for this RFQ.",
    label: "Unavailable",
    tone: "pending" as const,
  };
}

function StrategicSignalCard({
  detail,
  label,
  tone,
  value,
}: {
  detail: string;
  label: string;
  tone: "steel" | "gold" | "emerald" | "rose" | "amber" | "pending";
  value: string;
}) {
  return (
    <div className="rounded-2xl border border-border bg-muted/25 p-4 dark:bg-white/[0.02]">
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-3 flex items-center gap-2">
        <Badge variant={tone}>{value}</Badge>
      </div>
      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{detail}</p>
    </div>
  );
}

export function ExecutiveStrategicDetail({
  actorName,
  briefing,
  permissions,
  rfq,
  snapshot,
  staleIntel,
  workbookProfile,
  workbookReview,
}: {
  actorName: string;
  briefing: IntelligenceResourceState<BriefingArtifactModel | null>;
  permissions: RolePermissions;
  rfq: RfqDetailModel;
  snapshot: IntelligenceResourceState<IntelligenceSnapshotModel | null>;
  staleIntel: IntelligenceStaleNotice | null;
  workbookProfile: IntelligenceResourceState<WorkbookProfileModel | null>;
  workbookReview: IntelligenceResourceState<WorkbookReviewModel | null>;
}) {
  const deliveryRisk = buildDeliveryRisk(rfq);
  const blockerSignal = resolveBlockerSignal(rfq);
  const escalationSignal = resolveEscalationSignal(rfq, Boolean(staleIntel));
  const outcomeState = buildOutcomeState(rfq);
  const delayDiagnosis = buildDelayDiagnosis(rfq, deliveryRisk);
  const freshnessState = buildFreshnessState(snapshot, staleIntel);
  const evidenceAvailability = snapshot.data?.availabilityMatrix ?? [];
  const activeFindingsCount =
    workbookReview.data?.activeFindingsCount ?? snapshot.data?.reviewFlags.length ?? 0;
  const requiresHumanReview =
    snapshot.data?.requiresHumanReview ?? Boolean(activeFindingsCount > 0);
  const whyLeadershipShouldCare = buildWhyLeadershipShouldCare(
    rfq,
    deliveryRisk,
    escalationSignal,
    staleIntel,
  );
  const liveIntelMeta = intelligenceAvailabilityMeta[
    snapshot.data?.availability ?? briefing.data?.availability ?? "not_available_yet"
  ];
  const terminalOutcome = getTerminalRfqOutcome(rfq.status);

  return (
    <div className="space-y-6">
      <motion.section
        animate={{ opacity: 1, y: 0 }}
        className="surface-panel p-6"
        initial={{ opacity: 0, y: 16 }}
        transition={{ duration: 0.2 }}
      >
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0 flex-1">
            <div className="section-kicker">{rfq.rfqCode ?? rfq.id}</div>
            <h1 className="mt-3 text-display text-2xl font-semibold text-foreground lg:text-3xl">
              {rfq.title}
            </h1>
            {rfq.description ? (
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                {rfq.description}
              </p>
            ) : null}
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <RFQStatusChip status={rfq.status} />
            {rfq.workflowName ? <Badge variant="steel">{rfq.workflowName}</Badge> : null}
            <Badge variant={liveIntelMeta.tone}>Intel: {liveIntelMeta.label}</Badge>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="stat-cell">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Client
            </div>
            <div className="mt-1 font-medium text-foreground">{rfq.client}</div>
          </div>
          <div className="stat-cell">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Owner
            </div>
            <div className="mt-1 font-medium text-foreground">{rfq.owner}</div>
          </div>
          <div className="stat-cell">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Due Date
            </div>
            <div className="mt-1 font-mono font-medium text-foreground">{rfq.dueLabel}</div>
          </div>
          <div className="stat-cell">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Updated
            </div>
            <div className="mt-1 font-mono font-medium text-foreground">
              {rfq.updatedAtLabel ?? "Pending"}
            </div>
          </div>
        </div>

        {rfq.stageHistory.length > 0 ? (
          <div className="mt-5 rounded-xl border border-border bg-muted/30 p-4 dark:bg-white/[0.02]">
            <LifecycleProgressStageBox
              rfqProgress={rfq.rfqProgress}
              stageLabel={rfq.stageLabel}
              status={rfq.status}
            />
            <div className="mt-3">
              <RFQStageTimeline stages={rfq.stageHistory} />
            </div>
          </div>
        ) : null}

        <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-5">
          <StrategicSignalCard
            detail={`${rfq.rfqProgress}% through lifecycle${rfq.estimatedSubmissionLabel ? ` · Estimated submission ${rfq.estimatedSubmissionLabel}` : ""}.`}
            label="Current Stage"
            tone="steel"
            value={rfq.stageLabel}
          />
          <StrategicSignalCard
            detail={deliveryRisk.detail}
            label="Delivery Risk"
            tone={deliveryRisk.tone}
            value={deliveryRisk.label}
          />
          <StrategicSignalCard
            detail={blockerSignal}
            label="Blocker / Delay"
            tone={delayDiagnosis.tone}
            value={delayDiagnosis.headline}
          />
          <StrategicSignalCard
            detail={escalationSignal.detail}
            label="Escalation State"
            tone={escalationSignal.tone}
            value={escalationSignal.label}
          />
          <StrategicSignalCard
            detail={outcomeState.detail}
            label="Outcome State"
            tone={outcomeState.tone}
            value={outcomeState.label}
          />
        </div>
      </motion.section>

      <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="space-y-6">
          <motion.section
            animate={{ opacity: 1, y: 0 }}
            className="surface-panel p-6"
            initial={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.2, delay: 0.03 }}
          >
            <div className="section-kicker">
              <Target className="h-3.5 w-3.5" />
              Why Leadership Should Care Now
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {whyLeadershipShouldCare}
            </p>
          </motion.section>

          <motion.section
            animate={{ opacity: 1, y: 0 }}
            className="surface-panel p-6"
            initial={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.2, delay: 0.06 }}
          >
            <div className="section-kicker">
              <AlertTriangle className="h-3.5 w-3.5" />
              Delay / Blocker Diagnosis
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Badge variant={delayDiagnosis.tone}>{delayDiagnosis.headline}</Badge>
              <Badge variant="outline">{delayDiagnosis.source}</Badge>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {delayDiagnosis.detail}
            </p>
          </motion.section>

          {(terminalOutcome || rfq.outcomeReason) ? (
            <motion.section
              animate={{ opacity: 1, y: 0 }}
              className="surface-panel p-6"
              initial={{ opacity: 0, y: 14 }}
              transition={{ duration: 0.2, delay: 0.09 }}
            >
              <div className="section-kicker">
                <NotebookPen className="h-3.5 w-3.5" />
                Outcome Reasoning
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-2">
                <Badge variant={outcomeState.tone}>{outcomeState.label}</Badge>
                {rfq.outcomeReason ? <Badge variant="outline">Captured rationale</Badge> : null}
              </div>
              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                {outcomeState.detail}
              </p>
            </motion.section>
          ) : null}

          <motion.section
            animate={{ opacity: 1, y: 0 }}
            initial={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.2, delay: 0.12 }}
          >
            <div className="mb-4">
              <div className="section-kicker">
                <Sparkles className="h-3.5 w-3.5" />
                Curated Intelligence Briefing
              </div>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                Executive-facing intelligence stays on curated summary, missing information, next actions, and evidence posture.
              </p>
            </div>
            <IntelligencePanel
              briefing={briefing}
              rfq={rfq}
              snapshot={snapshot}
              staleIntel={staleIntel}
              viewMode="curated"
              workbookProfile={workbookProfile}
              workbookReview={workbookReview}
            />
          </motion.section>
        </div>

        <div className="space-y-6">
          <motion.section
            animate={{ opacity: 1, y: 0 }}
            className="surface-panel p-5"
            initial={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.2, delay: 0.05 }}
          >
            <div className="section-kicker">
              <Workflow className="h-3.5 w-3.5" />
              Strategic Snapshot
            </div>
            <div className="mt-4 space-y-3">
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Lifecycle Posture
                </div>
                <div className="mt-1 text-sm font-medium text-foreground">
                  {rfq.statusLabel} · {rfq.stageLabel}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Procurement Lead
                </div>
                <div className="mt-1 text-sm font-medium text-foreground">
                  {rfq.procurementLead ?? "Not recorded"}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Estimated Submission
                </div>
                <div className="mt-1 text-sm font-medium text-foreground">
                  {rfq.estimatedSubmissionLabel ?? "Pending"}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Leadership Attention
                </div>
                <div className="mt-1 text-sm text-muted-foreground">
                  {escalationSignal.detail}
                </div>
              </div>
            </div>
          </motion.section>

          <motion.section
            animate={{ opacity: 1, y: 0 }}
            className="surface-panel p-5"
            initial={{ opacity: 0, y: 14 }}
            transition={{ duration: 0.2, delay: 0.08 }}
          >
            <div className="section-kicker">
              <Clock3 className="h-3.5 w-3.5" />
              Supporting Evidence Summary
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <Badge variant={freshnessState.tone}>{freshnessState.label}</Badge>
              <Badge variant={requiresHumanReview ? "gold" : "emerald"}>
                {requiresHumanReview ? "Human review required" : "Human review not flagged"}
              </Badge>
              <Badge variant={activeFindingsCount > 0 ? "gold" : "emerald"}>
                {activeFindingsCount} active finding(s)
              </Badge>
            </div>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {freshnessState.detail}
            </p>
            {evidenceAvailability.length > 0 ? (
              <div className="mt-4 grid gap-2 sm:grid-cols-2">
                {evidenceAvailability.map((item) => (
                  <div
                    key={`${item.label}-${item.value}`}
                    className="rounded-xl border border-border bg-muted/20 p-3 dark:bg-white/[0.02]"
                  >
                    <div className="text-sm font-medium text-foreground">{item.label}</div>
                    <div className="mt-1 text-sm text-muted-foreground">{item.value}</div>
                  </div>
                ))}
              </div>
            ) : null}
          </motion.section>

          <LeadershipNotesPanel
            actorName={actorName}
            permissions={permissions}
            rfqId={rfq.id}
            role="executive"
          />
        </div>
      </div>
    </div>
  );
}
