import type {
  IntelligenceArtifactEnvelope,
  IntelligenceBriefingContent,
} from "@/models/intelligence/api";
import type {
  BriefingArtifactModel,
  BriefingResponse,
} from "@/models/intelligence/briefing";
import {
  formatArtifactVersion,
  formatContractLabel,
  pickList,
  resolveArtifactTimestamp,
  resolveUpdatedLabel,
  toAvailabilityState,
  toProcessingState,
} from "@/translators/intelligence/shared";

export function translateBriefing(
  briefing: BriefingResponse,
): BriefingArtifactModel {
  return {
    kind: "briefing",
    title: "Bid Briefing",
    status: briefing.status,
    availability: toAvailabilityState(briefing.status, {
      preliminary: briefing.status !== "complete",
    }),
    version: briefing.version,
    updatedLabel: briefing.updatedAt ? resolveUpdatedLabel(briefing.updatedAt) : "Pending",
    updatedAtValue: resolveArtifactTimestamp(briefing.updatedAt),
    summary: briefing.executiveSummary,
    keySignals: briefing.strategicSignals,
    openQuestions: briefing.openQuestions,
    recommendedActions: briefing.recommendation ? [briefing.recommendation] : [],
    limitations: [],
    sectionAvailability: [],
    preliminary: briefing.status !== "complete",
  };
}

export function translateLiveBriefing(
  envelope: IntelligenceArtifactEnvelope<IntelligenceBriefingContent>,
): BriefingArtifactModel {
  const content = envelope.content ?? {};
  const generatedAt = content.artifact_meta?.generated_at;
  const known = content.what_is_known;
  const missing = content.what_is_missing ?? [];
  const knownPoints = pickList([
    ...(known?.known_points ?? []),
    known?.project_title ? `Project: ${known.project_title}` : undefined,
    known?.client_name ? `Client: ${known.client_name}` : undefined,
    known?.source_package_reference
      ? `Source package: ${known.source_package_reference}`
      : undefined,
  ]);
  const preliminary =
    content.artifact_meta?.slice === "rfq.created_vertical_slice_v1" ||
    content.section_availability?.document_understanding === "limited";

  return {
    kind: "briefing",
    title: "Intelligence Briefing",
    status: toProcessingState(envelope.status),
    availability: toAvailabilityState(envelope.status, { preliminary }),
    version: formatArtifactVersion(envelope.version),
    updatedLabel: resolveUpdatedLabel(envelope.updated_at, envelope.created_at, generatedAt),
    updatedAtValue: resolveArtifactTimestamp(
      envelope.updated_at,
      envelope.created_at,
      generatedAt,
    ),
    summary:
      content.executive_summary ??
      "No briefing summary is available yet.",
    keySignals: knownPoints,
    openQuestions: missing,
    recommendedActions: content.recommended_next_actions ?? [],
    limitations: content.cold_start_limitations ?? [],
    sectionAvailability: Object.entries(content.section_availability ?? {}).map(
      ([label, value]) => ({
        label: formatContractLabel(label),
        value: formatContractLabel(value),
      }),
    ),
    preliminary,
  };
}
