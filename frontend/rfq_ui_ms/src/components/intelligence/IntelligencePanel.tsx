"use client";

import type { ReactNode } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  ClipboardCheck,
  FileText,
  Sparkles,
} from "lucide-react";

import { PartialIntelligenceState } from "@/components/intelligence/PartialIntelligenceState";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import { Badge } from "@/components/ui/badge";
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
import { intelligenceAvailabilityMeta } from "@/utils/status";

function sanitizePackageSignal(item: string) {
  if (item.startsWith("Project: ")) {
    return item;
  }

  if (item.startsWith("Client: ")) {
    return item;
  }

  if (item.startsWith("Source package:")) {
    return "Client RFQ package is linked and available for review.";
  }

  const mrMatch = item.match(/^MR\s+(.+)$/i);
  if (mrMatch) {
    return `Inquiry reference: ${mrMatch[1]}`;
  }

  const bomMatch = item.match(/^(\d+)\s+BOM tag\(s\)$/i);
  if (bomMatch) {
    return `${bomMatch[1]} BOM tag(s) detected in the package.`;
  }

  const rvlMatch = item.match(/^(\d+)\s+RVL vendor\(s\)$/i);
  if (rvlMatch) {
    return `${rvlMatch[1]} vendor reference(s) detected in the package.`;
  }

  if (item.startsWith("Standards families:")) {
    return item.replace("Standards families:", "Standards detected:");
  }

  return item;
}

function sanitizePackageGap(item: string) {
  switch (item.toLowerCase()) {
    case "semantic pdf understanding":
      return "Detailed document reading is still limited.";
    case "deep qaqc extraction":
      return "Detailed QA/QC extraction is still limited.";
    case "structured compliance extraction":
      return "Structured compliance extraction still needs deeper parsing.";
    case "deep file inventory":
      return "Detailed package inventory still needs review.";
    case "document extraction":
      return "Detailed document extraction is still limited.";
    case "workbook comparison":
      return "Workbook comparison is not ready until the estimator workbook is reviewed.";
    default:
      return item;
  }
}

function sanitizePackageAction(item: string) {
  const normalized = item.toLowerCase();

  if (normalized.includes("workbook_profile") || normalized.includes("review_report")) {
    return "Upload the estimator workbook to unlock workbook comparison.";
  }

  if (normalized.includes("deterministic package findings")) {
    return "Review the package findings and warnings before using them in decisions.";
  }

  if (normalized.includes("human review")) {
    return "Treat this as early guidance and confirm the important points with human review.";
  }

  if (normalized.includes("upload the incoming rfq package")) {
    return "Upload the incoming client RFQ package to start package intelligence.";
  }

  if (normalized.includes("run package intelligence")) {
    return "Generate the first package summary for this RFQ.";
  }

  return item;
}

function sanitizePackageSummary(item: string) {
  const normalized = item.toLowerCase();

  if (normalized.includes("deterministic-enriched v1 briefing")) {
    return "An initial package summary is available from the client RFQ package. It helps early review, but it still needs human confirmation.";
  }

  if (normalized.includes("manager-provided context only")) {
    return "An initial package summary is available from the current RFQ package and manager context. Use it as early guidance, not final decision support.";
  }

  if (normalized.includes("semantic pdf understanding remains deferred")) {
    return "An initial package summary is available, but deeper document understanding is still limited.";
  }

  return item;
}

function sanitizeWorkbookCoverage(item: string) {
  if (item.includes("tracked sheet(s)")) {
    return item.replace("tracked sheet(s)", "workbook sheet(s) recognized");
  }

  if (item.startsWith("Template: ")) {
    return item.replace("Template: ", "Workbook template: ");
  }

  if (item.startsWith("Template match: ")) {
    return item.replace("Template match: ", "Template recognition: ");
  }

  return item;
}

function sanitizeWorkbookFinding(item: string) {
  if (item.includes("Workbook template recognition indicates missing expected sheets.")) {
    return "Some expected workbook sheets are missing, so the comparison needs human review.";
  }

  if (item.includes("Workbook fixture processed as standalone input")) {
    return "The workbook was reviewed separately, so its comparison against the RFQ package still needs confirmation.";
  }

  if (item.includes("Insufficient historical base for benchmark analysis")) {
    return "Benchmark comparison is not available yet because the historical base is still too small.";
  }

  if (item.includes("Upload the late-lifecycle estimator workbook")) {
    return "Upload the estimator workbook to unlock workbook comparison.";
  }

  return item;
}

function sanitizeWorkbookSummary(item: string) {
  const normalized = item.toLowerCase();

  if (normalized.includes("review posture:")) {
    return "Workbook comparison is available, but it still needs human review before it is used in decisions.";
  }

  if (normalized.includes("workbook review report")) {
    return "Workbook comparison results are available for review.";
  }

  return item;
}

function sanitizeHistoricalSignal(item: string) {
  if (item.startsWith("Similarity:")) {
    return "Similarity benchmark: historical base is still too small.";
  }

  if (item.startsWith("Benchmarking:")) {
    return "Benchmark comparison: historical base is still too small.";
  }

  if (item.includes("cold-start maturity mode")) {
    return "The historical learning base is still in its early stage.";
  }

  return item;
}

function getUserFacingAvailability(
  availability: keyof typeof intelligenceAvailabilityMeta,
) {
  switch (availability) {
    case "partial":
      return "Needs Review";
    case "preliminary":
      return "Initial Review";
    case "available":
      return "Ready";
    case "failed":
      return "Needs Attention";
    default:
      return intelligenceAvailabilityMeta[availability].label;
  }
}

function PhaseCard({
  title,
  icon: Icon,
  children,
}: {
  title: string;
  icon: typeof Sparkles;
  children: ReactNode;
}) {
  return (
    <div className="surface-panel p-5">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-muted/40 dark:bg-white/[0.03]">
          <Icon className="h-4.5 w-4.5 text-primary" />
        </div>
        <h3 className="text-sm font-semibold text-foreground">{title}</h3>
      </div>
      <div className="mt-4">{children}</div>
    </div>
  );
}

function ListSection({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: string[];
  emptyLabel: string;
}) {
  return (
    <div>
      <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        {title}
      </div>
      {items.length > 0 ? (
        <div className="mt-2 space-y-1.5">
          {items.map((item) => (
            <div key={item} className="stat-cell text-sm text-muted-foreground">
              {item}
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">{emptyLabel}</p>
      )}
    </div>
  );
}

function MetaRow({
  availability,
  updatedLabel,
  version,
}: {
  availability: keyof typeof intelligenceAvailabilityMeta;
  updatedLabel?: string;
  version?: string;
}) {
  const meta = intelligenceAvailabilityMeta[availability];
  const label = getUserFacingAvailability(availability);

  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant={meta.tone}>{label}</Badge>
      {version ? <Badge variant="default">{version}</Badge> : null}
      {updatedLabel ? (
        <span className="text-xs text-muted-foreground">Updated {updatedLabel}</span>
      ) : null}
    </div>
  );
}

function buildPackagePhase(
  rfq: RfqDetailModel,
  snapshot: IntelligenceResourceState<IntelligenceSnapshotModel | null>,
  briefing: IntelligenceResourceState<BriefingArtifactModel | null>,
) {
  if (!rfq.sourcePackageAvailable) {
    return {
      actions: ["Upload the incoming RFQ package to start package intelligence."],
      availability: "not_available_yet" as const,
      description:
        "Waiting for RFQ package upload. Package intelligence starts as soon as the client package is available in the RFQ.",
      details: [],
      summary: "No client RFQ package is currently available for package intelligence.",
      title: "Waiting for RFQ Package",
      updatedLabel: undefined,
      version: undefined,
    };
  }

  if (snapshot.loading || briefing.loading) {
    return {
      actions: [],
      availability: "pending" as const,
      description:
        "Package intelligence is being refreshed from the latest client RFQ package.",
      details: [],
      summary: "Package intelligence is loading for this RFQ.",
      title: "Package Intelligence In Progress",
      updatedLabel: undefined,
      version: undefined,
    };
  }

  if (snapshot.data || briefing.data) {
    const data = snapshot.data;
    return {
      actions: briefing.data?.recommendedActions ?? [],
      availability:
        snapshot.data?.availability
        ?? briefing.data?.availability
        ?? "available",
      description:
        "A first package summary is available from the client RFQ package and can support early pursuit understanding.",
      details: [
        ...(briefing.data?.keySignals.map(sanitizePackageSignal) ?? []),
        ...(snapshot.data?.reviewFlags.map((flag) => sanitizePackageGap(flag.detail)) ?? []),
      ],
      summary:
        sanitizePackageSummary(
          briefing.data?.summary
          ?? data?.summary
          ?? "Initial package intelligence is available.",
        ),
      title: "Initial Package Intelligence Ready",
      updatedLabel: briefing.data?.updatedLabel ?? data?.updatedLabel,
      version: briefing.data?.version ?? data?.version,
    };
  }

  return {
    actions: ["Generate the first package summary for this RFQ."],
    availability: "not_available_yet" as const,
    description:
      "RFQ package is available, but package intelligence has not been generated yet.",
    details: [],
    summary: "Package intelligence is ready to be generated from the uploaded client RFQ package.",
    title: "Package Ready To Process",
    updatedLabel: rfq.sourcePackageUpdatedLabel,
    version: undefined,
  };
}

function buildWorkbookPhase(
  rfq: RfqDetailModel,
  workbookProfile: IntelligenceResourceState<WorkbookProfileModel | null>,
  workbookReview: IntelligenceResourceState<WorkbookReviewModel | null>,
) {
  if (!rfq.workbookAvailable) {
    return {
      actions: ["Upload the late-lifecycle estimator workbook to unlock workbook enrichment."],
      availability: "not_available_yet" as const,
      description:
        "Workbook enrichment starts only after the estimator workbook exists.",
      details: [],
      summary:
        "Workbook enrichment is waiting for workbook upload and should not be treated as an early RFQ step.",
      title: "Waiting for Workbook Upload",
      updatedLabel: undefined,
      version: undefined,
    };
  }

  if (workbookProfile.loading || workbookReview.loading) {
    return {
      actions: [],
      availability: "pending" as const,
      description:
        "Workbook enrichment is being refreshed from the latest estimator workbook.",
      details: [],
      summary: "Workbook enrichment is loading for this RFQ.",
      title: "Workbook Enrichment In Progress",
      updatedLabel: undefined,
      version: undefined,
    };
  }

  if (workbookProfile.data || workbookReview.data) {
    return {
      actions: workbookReview.data?.findings.map((finding) => finding.title) ?? [],
      availability:
        workbookReview.data?.availability
        ?? workbookProfile.data?.availability
        ?? "available",
      description:
        "Workbook enrichment compares the estimator workbook against the original RFQ package.",
      details: [
        ...(workbookProfile.data?.sheetStats.map(sanitizeWorkbookCoverage) ?? []),
        ...(workbookProfile.data?.missingSections ?? []),
        ...(workbookReview.data?.findings.map((finding) => sanitizeWorkbookFinding(`${finding.title}: ${finding.detail}`)) ?? []),
      ],
      summary:
        sanitizeWorkbookSummary(
          workbookReview.data?.summary
          ?? workbookProfile.data?.summary
          ?? "Workbook enrichment is available.",
        ),
      title: "Workbook Comparison Ready",
      updatedLabel:
        workbookReview.data?.updatedLabel ?? workbookProfile.data?.updatedLabel,
      version: workbookReview.data?.version ?? workbookProfile.data?.version,
    };
  }

  return {
    actions: ["Run workbook enrichment to compare the workbook against the RFQ package."],
    availability: "not_available_yet" as const,
    description:
      "Workbook is available, but workbook enrichment has not been generated yet.",
    details: [],
    summary: "Workbook enrichment is ready to be generated from the uploaded workbook.",
    title: "Workbook Ready To Process",
    updatedLabel: rfq.workbookUpdatedLabel,
    version: undefined,
  };
}

function buildHistoricalPhase(
  rfq: RfqDetailModel,
  snapshot: IntelligenceResourceState<IntelligenceSnapshotModel | null>,
) {
  const availabilityEntries = snapshot.data?.availabilityMatrix ?? [];
  const historicalSignals = availabilityEntries.filter((entry) =>
    ["Benchmarking", "Similarity"].includes(entry.label),
  );

  return {
    actions: [
      rfq.status === "awarded" || rfq.status === "lost" || rfq.status === "cancelled"
        ? "This RFQ can contribute to the historical base after closeout and workbook retention."
        : "Historical insights unlock after enough completed RFQs and retained workbooks exist.",
    ],
    availability: "not_available_yet" as const,
    description:
      "Historical insights are portfolio-powered and remain intentionally maturity-gated in this phase.",
    details:
      historicalSignals.length > 0
        ? historicalSignals.map((entry) => sanitizeHistoricalSignal(`${entry.label}: ${entry.value}`))
        : ["Benchmarking and similarity are still building from a small historical base."],
    summary:
      "Historical insights become useful after enough completed RFQs and retained workbooks are available. The current portfolio is not mature enough yet.",
    title: "Historical Maturity Not Reached Yet",
    updatedLabel: undefined,
    version: undefined,
  };
}

export function IntelligencePanel({
  briefing,
  rfq,
  snapshot,
  staleIntel,
  viewMode = "working",
  workbookProfile,
  workbookReview,
}: {
  briefing: IntelligenceResourceState<BriefingArtifactModel | null>;
  rfq: RfqDetailModel;
  snapshot: IntelligenceResourceState<IntelligenceSnapshotModel | null>;
  staleIntel: IntelligenceStaleNotice | null;
  viewMode?: "curated" | "working";
  workbookProfile: IntelligenceResourceState<WorkbookProfileModel | null>;
  workbookReview: IntelligenceResourceState<WorkbookReviewModel | null>;
}) {
  const packagePhase = buildPackagePhase(rfq, snapshot, briefing);
  const workbookPhase = buildWorkbookPhase(rfq, workbookProfile, workbookReview);
  const historicalPhase = buildHistoricalPhase(rfq, snapshot);

  const heroState =
    packagePhase.availability === "available" || packagePhase.availability === "preliminary"
      ? workbookPhase.availability === "available" || workbookPhase.availability === "partial"
        ? "available"
        : "partial"
      : packagePhase.availability;

  const heroSummary =
    packagePhase.availability === "not_available_yet"
      ? "The intelligence assistant is waiting for the first client RFQ package."
      : workbookPhase.availability === "not_available_yet"
        ? "An initial package summary is available, while workbook enrichment remains a later lifecycle step."
        : "Package intelligence and workbook enrichment are both available for this RFQ, but they still need human review.";

  return (
    <div className="space-y-6">
      {staleIntel ? (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 p-4 text-sm text-amber-700 dark:text-amber-300">
          <div className="font-medium text-foreground">Intelligence needs refresh review</div>
          <p className="mt-1.5 leading-relaxed">
            {staleIntel.message} RFQ updated {staleIntel.managerUpdatedLabel}; latest intelligence refresh {staleIntel.intelligenceUpdatedLabel}.
          </p>
        </div>
      ) : null}

      <motion.div
        animate={{ opacity: 1, y: 0 }}
        className="surface-panel overflow-hidden p-6"
        initial={{ opacity: 0, y: 16 }}
        transition={{ duration: 0.35 }}
      >
        <div className="section-kicker">
          <Sparkles className="h-3.5 w-3.5" />
          Intelligence Overview
        </div>
        <div className="mt-4">
          <PartialIntelligenceState
            actions={[
              packagePhase.title,
              workbookPhase.title,
              "Historical insights remain maturity-gated in this phase.",
            ]}
            state={heroState}
            summary={heroSummary}
          />
        </div>
      </motion.div>

      <div className="grid gap-5 xl:grid-cols-2">
        <PhaseCard icon={ClipboardCheck} title="Package Intelligence">
          {briefing.loading || snapshot.loading ? (
            <SkeletonCard lines={5} />
          ) : (
            <div className="space-y-4">
              <MetaRow
                availability={packagePhase.availability}
                updatedLabel={packagePhase.updatedLabel}
                version={packagePhase.version}
              />
              <p className="text-sm leading-relaxed text-muted-foreground">
                {packagePhase.summary}
              </p>
              <ListSection
                emptyLabel="No package signals are listed yet."
                items={briefing.data?.keySignals.map(sanitizePackageSignal) ?? []}
                title="Known From Package"
              />
              <ListSection
                emptyLabel="No package review gaps are listed yet."
                items={(briefing.data?.openQuestions ?? packagePhase.actions).map(sanitizePackageGap)}
                title="Needs Human Review"
              />
              <ListSection
                emptyLabel="No next step is currently listed."
                items={(briefing.data?.recommendedActions ?? []).map(sanitizePackageAction)}
                title="Recommended Next Step"
              />
            </div>
          )}
        </PhaseCard>

        <PhaseCard icon={FileText} title="Workbook Enrichment">
          {workbookProfile.loading || workbookReview.loading ? (
            <SkeletonCard lines={5} />
          ) : (
            <div className="space-y-4">
              <MetaRow
                availability={workbookPhase.availability}
                updatedLabel={workbookPhase.updatedLabel}
                version={workbookPhase.version}
              />
              <p className="text-sm leading-relaxed text-muted-foreground">
                {workbookPhase.summary}
              </p>
              <ListSection
                emptyLabel="Workbook coverage details will appear once enrichment is available."
                items={[
                  ...(workbookProfile.data?.sheetStats.map(sanitizeWorkbookCoverage) ?? []),
                  ...(workbookProfile.data?.trackedSheets ?? []),
                ]}
                title="Workbook Coverage"
              />
              <ListSection
                emptyLabel="No workbook comparison issues are currently listed."
                items={
                  workbookReview.data?.findings.map(
                    (finding) => sanitizeWorkbookFinding(`${finding.title}: ${finding.detail}`),
                  ) ?? workbookPhase.actions.map(sanitizeWorkbookFinding)
                }
                title="What Needs Review"
              />
            </div>
          )}
        </PhaseCard>

        {viewMode === "working" ? (
          <PhaseCard icon={BarChart3} title="Historical Insights">
            <div className="space-y-4">
              <MetaRow availability={historicalPhase.availability} />
              <p className="text-sm leading-relaxed text-muted-foreground">
                {historicalPhase.summary}
              </p>
              <ListSection
                emptyLabel="Historical maturity notes are not currently available."
                items={historicalPhase.details.map(sanitizeHistoricalSignal)}
                title="Current Maturity Signals"
              />
              <ListSection
                emptyLabel="No historical readiness guidance is currently listed."
                items={historicalPhase.actions}
                title="What Will Unlock This Phase"
              />
            </div>
          </PhaseCard>
        ) : null}
      </div>
    </div>
  );
}
