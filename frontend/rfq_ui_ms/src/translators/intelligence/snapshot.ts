import type {
  IntelligenceArtifactEnvelope,
  IntelligenceSnapshotContent,
} from "@/models/intelligence/api";
import type {
  IntelligencePortfolioResponse,
  IntelligenceSnapshotModel,
  SnapshotResponse,
} from "@/models/intelligence/snapshot";
import type {
  IntelligencePortfolioModel,
  KPIMetricModel,
} from "@/models/ui/dashboard";
import { intelligenceStatusMeta } from "@/utils/status";
import {
  formatArtifactVersion,
  formatContractLabel,
  pickList,
  resolveArtifactTimestamp,
  resolveUpdatedLabel,
  toAvailabilityState,
  toProcessingState,
} from "@/translators/intelligence/shared";

export function translatePortfolioSummary(
  summary: IntelligencePortfolioResponse,
): IntelligencePortfolioModel {
  return {
    completeCount: summary.completeCount,
    partialCount: summary.partialCount,
    failedCount: summary.failedCount,
    readinessAverage: summary.readinessAverage,
    narrative: summary.narrative,
    featuredRfqId: summary.featuredRfqId,
  };
}

export function translatePortfolioKpis(
  summary: IntelligencePortfolioResponse,
): KPIMetricModel[] {
  return [
    {
      id: "intel-complete",
      label: "Complete Intelligence",
      value: `${summary.completeCount}`,
      helper: "RFQs with package and workbook artifacts aligned.",
      trendLabel: `${summary.partialCount} partial`,
      trendDirection: "steady",
      tone: "emerald",
    },
    {
      id: "intel-readiness",
      label: "Portfolio Readiness",
      value: `${summary.readinessAverage}%`,
      helper: "Average readiness across the monitored queue.",
      trendLabel: `${summary.failedCount} failed`,
      trendDirection: "steady",
      tone: "steel",
    },
  ];
}

export function translateSnapshot(
  snapshot: SnapshotResponse,
): IntelligenceSnapshotModel {
  const updatedAtValue =
    snapshot.workbook.uploadedAt ?? snapshot.briefing.generatedAt ?? snapshot.intake.processedAt;

  return {
    kind: "snapshot",
    state: snapshot.state,
    availability: toAvailabilityState(snapshot.state),
    version: undefined,
    updatedLabel: resolveUpdatedLabel(updatedAtValue),
    updatedAtValue: resolveArtifactTimestamp(updatedAtValue),
    generatedLabel: resolveUpdatedLabel(updatedAtValue),
    generatedAtValue: resolveArtifactTimestamp(updatedAtValue),
    summary: snapshot.quality.summary,
    requiresHumanReview: snapshot.reviewFlags.length > 0 || snapshot.readiness.blockers.length > 0,
    recommendedTabs: ["snapshot", "briefing"],
    suggestedQuestions: pickList([
      snapshot.briefing.summary,
      ...snapshot.workbook.pendingQuestions,
    ]).slice(0, 3),
    availabilityMatrix: [
      {
        label: "Intake",
        value: formatContractLabel(snapshot.intake.status),
      },
      {
        label: "Briefing",
        value: formatContractLabel(snapshot.briefing.status),
      },
      {
        label: "Workbook",
        value: formatContractLabel(snapshot.workbook.status),
      },
      {
        label: "Review",
        value: formatContractLabel(snapshot.workbook.reviewStatus),
      },
    ],
    intake: {
      availability: toAvailabilityState(snapshot.intake.status),
      statusLabel: intelligenceStatusMeta[snapshot.intake.status].label,
      summary: snapshot.intake.summary,
      bullets: [
        `${snapshot.intake.sectionsDetected} sections detected`,
        `${snapshot.intake.lineItems} line items`,
        ...snapshot.intake.missing,
      ],
    },
    briefing: {
      availability: toAvailabilityState(snapshot.briefing.status),
      statusLabel: intelligenceStatusMeta[snapshot.briefing.status].label,
      summary: snapshot.briefing.summary,
      bullets: [...snapshot.briefing.strengths, ...snapshot.briefing.risks],
    },
    workbook: {
      availability: toAvailabilityState(snapshot.workbook.status),
      statusLabel:
        snapshot.workbook.status === "not_uploaded"
          ? intelligenceStatusMeta.not_uploaded.label
          : intelligenceStatusMeta[snapshot.workbook.status].label,
      summary:
        snapshot.workbook.status === "not_uploaded"
          ? "Workbook has not been uploaded yet."
          : "Workbook intelligence is available for review.",
      bullets: snapshot.workbook.pendingQuestions,
    },
    review: {
      availability: toAvailabilityState(snapshot.workbook.reviewStatus),
      statusLabel:
        snapshot.workbook.reviewStatus === "not_uploaded"
          ? intelligenceStatusMeta.not_uploaded.label
          : intelligenceStatusMeta[snapshot.workbook.reviewStatus].label,
      summary: snapshot.quality.summary,
      bullets: [...snapshot.readiness.blockers, ...snapshot.quality.gaps],
    },
    reviewFlags: snapshot.reviewFlags,
  };
}

export function translateLiveSnapshot(
  envelope: IntelligenceArtifactEnvelope<IntelligenceSnapshotContent>,
): IntelligenceSnapshotModel {
  const content = envelope.content ?? {};
  const generatedAt = content.artifact_meta?.generated_at;
  const updatedAtValue = resolveArtifactTimestamp(
    envelope.updated_at,
    envelope.created_at,
    generatedAt,
  );
  const intakeStatus = content.intake_panel_summary?.status ?? "not_ready";
  const briefingStatus = content.briefing_panel_summary?.status ?? "not_ready";
  const workbookStatus = content.workbook_panel?.status ?? "not_ready";
  const reviewStatus = content.review_panel?.status ?? "not_ready";
  const reviewFlags = [
    ...(content.intake_panel_summary?.key_gaps ?? []).map((gap) => ({
      severity: "medium" as const,
      label: "Intake Gap",
      detail: gap,
    })),
    ...(content.briefing_panel_summary?.missing_info ?? []).slice(0, 2).map((item) => ({
      severity: "medium" as const,
      label: "Missing Info",
      detail: item,
    })),
    ...pickList([
      content.workbook_panel?.parser_failure?.message,
      content.workbook_panel?.reason,
      content.review_panel?.reason,
    ]).slice(0, 2).map((detail) => ({
      severity: "high" as const,
      label: "Review Attention",
      detail,
    })),
  ];

  return {
    kind: "snapshot",
    state: toProcessingState(envelope.status),
    availability: toAvailabilityState(content.overall_status ?? envelope.status),
    version: formatArtifactVersion(envelope.version),
    updatedLabel: resolveUpdatedLabel(envelope.updated_at, envelope.created_at, generatedAt),
    updatedAtValue,
    generatedLabel: resolveUpdatedLabel(generatedAt),
    generatedAtValue: generatedAt ?? undefined,
    summary:
      content.briefing_panel_summary?.executive_summary ??
      content.workbook_panel?.reason ??
      "Snapshot reflects the latest intelligence artifacts that are currently available.",
    requiresHumanReview: Boolean(content.requires_human_review),
    recommendedTabs: content.consumer_hints?.ui_recommended_tabs ?? [],
    suggestedQuestions: content.consumer_hints?.chatbot_suggested_questions ?? [],
    availabilityMatrix: Object.entries(content.availability_matrix ?? {}).map(
      ([label, value]) => ({
        label: formatContractLabel(label),
        value: formatContractLabel(value),
      }),
    ),
    intake: {
      availability: toAvailabilityState(intakeStatus),
      statusLabel: formatContractLabel(intakeStatus),
      summary:
        content.intake_panel_summary?.source_reference
          ? `Source package reference: ${content.intake_panel_summary.source_reference}`
          : "No intake source reference is available yet.",
      bullets: pickList([
        content.intake_panel_summary?.quality_status
          ? `Quality status: ${formatContractLabel(content.intake_panel_summary.quality_status)}`
          : undefined,
        ...(content.intake_panel_summary?.key_gaps ?? []),
      ]),
    },
    briefing: {
      availability: toAvailabilityState(
        briefingStatus,
        {
          preliminary:
            content.artifact_meta?.slice === "rfq.created_vertical_slice_v1",
        },
      ),
      statusLabel: formatContractLabel(briefingStatus),
      summary:
        content.briefing_panel_summary?.executive_summary ??
        "No briefing summary is available yet.",
      bullets: content.briefing_panel_summary?.missing_info ?? [],
    },
    workbook: {
      availability: toAvailabilityState(workbookStatus),
      statusLabel: formatContractLabel(workbookStatus),
      summary:
        content.workbook_panel?.reason ??
        "Workbook intelligence is not available yet.",
      bullets: pickList([
        content.workbook_panel?.parser_status
          ? `Parser status: ${formatContractLabel(content.workbook_panel.parser_status)}`
          : undefined,
        content.workbook_panel?.template_recognition
          ? "Template recognition available"
          : undefined,
        content.workbook_panel?.pairing_validation
          ? "Pairing validation metadata available"
          : undefined,
        content.workbook_panel?.parser_failure?.message,
      ]),
    },
    review: {
      availability: toAvailabilityState(reviewStatus),
      statusLabel: formatContractLabel(reviewStatus),
      summary:
        content.review_panel?.reason ??
        (typeof content.review_panel?.active_findings_count === "number"
          ? `${content.review_panel.active_findings_count} active finding(s) currently recorded.`
          : "Workbook review is not available yet."),
      bullets: pickList([
        typeof content.review_panel?.active_findings_count === "number"
          ? `${content.review_panel.active_findings_count} active finding(s)`
          : undefined,
        ...(content.analytical_status_summary?.notes ?? []),
      ]),
    },
    reviewFlags,
  };
}
