import type {
  IntelligenceArtifactEnvelope,
  IntelligenceWorkbookProfileContent,
  IntelligenceWorkbookReviewContent,
  IntelligenceWorkbookReviewFinding,
} from "@/models/intelligence/api";
import type {
  WorkbookProfileModel,
  WorkbookProfileResponse,
  WorkbookReviewFindingModel,
  WorkbookReviewModel,
  WorkbookReviewResponse,
} from "@/models/intelligence/workbook";
import {
  formatArtifactVersion,
  formatContractLabel,
  pickList,
  resolveArtifactTimestamp,
  resolveUpdatedLabel,
  toAvailabilityState,
  toProcessingState,
} from "@/translators/intelligence/shared";

export function translateWorkbookProfile(
  profile: WorkbookProfileResponse,
): WorkbookProfileModel {
  return {
    kind: "workbook_profile",
    status: profile.status,
    availability: toAvailabilityState(profile.status),
    version: profile.version,
    updatedLabel: profile.updatedAt ? resolveUpdatedLabel(profile.updatedAt) : "Pending",
    updatedAtValue: resolveArtifactTimestamp(profile.updatedAt),
    summary:
      profile.status === "not_uploaded"
        ? "Workbook has not been uploaded yet."
        : profile.missingSections.length > 0
          ? profile.missingSections.join(" ")
          : "Workbook profile is available.",
    completion: profile.completion,
    trackedSheets: profile.trackedSheets,
    missingSections: profile.missingSections,
    owner: profile.owner,
    sheetStats: profile.trackedSheets.length
      ? [`${profile.trackedSheets.length} tracked sheet(s)`]
      : [],
    notes: profile.owner ? [`Owner: ${profile.owner}`] : [],
  };
}

function translateFinding(
  finding: IntelligenceWorkbookReviewFinding,
): WorkbookReviewFindingModel {
  return {
    id: finding.finding_id ?? `${finding.family ?? "finding"}-${finding.title ?? "item"}`,
    severity: finding.severity ?? "low",
    title: finding.title ?? "Review finding",
    detail: finding.description ?? "This deserves review.",
    family: finding.family ?? undefined,
    status: finding.status ?? undefined,
  };
}

export function translateWorkbookReview(
  review: WorkbookReviewResponse,
): WorkbookReviewModel {
  return {
    kind: "workbook_review",
    status: review.status,
    availability: toAvailabilityState(review.status),
    version: review.version,
    updatedLabel: review.updatedAt ? resolveUpdatedLabel(review.updatedAt) : "Pending",
    updatedAtValue: resolveArtifactTimestamp(review.updatedAt),
    summary:
      review.flags.length > 0
        ? review.flags[0]?.detail ?? "Workbook review has open findings."
        : review.status === "not_uploaded"
          ? "Workbook review is not available until workbook intake begins."
          : "Workbook review is available.",
    readiness: review.readiness,
    missingResponses: review.missingResponses,
    activeFindingsCount: review.flags.length,
    unavailableFamilies: [],
    findings: review.flags.map((flag, index) => ({
      id: `${flag.label}-${index}`,
      severity: flag.severity,
      title: flag.label,
      detail: flag.detail,
    })),
    flags: review.flags,
  };
}

export function translateLiveWorkbookProfile(
  envelope: IntelligenceArtifactEnvelope<IntelligenceWorkbookProfileContent>,
): WorkbookProfileModel {
  const content = envelope.content ?? {};
  const generatedAt = content.artifact_meta?.generated_at;
  const structure = content.workbook_structure;
  const trackedSheets = structure?.sheet_names ?? [];
  const missingSections = structure?.missing_sheets ?? [];
  const extraSheets = structure?.extra_sheets ?? [];

  return {
    kind: "workbook_profile",
    status: toProcessingState(envelope.status),
    availability: toAvailabilityState(
      content.parser_report_status === "failed" ? "failed" : envelope.status,
    ),
    version: formatArtifactVersion(envelope.version),
    updatedLabel: resolveUpdatedLabel(envelope.updated_at, envelope.created_at, generatedAt),
    updatedAtValue: resolveArtifactTimestamp(
      envelope.updated_at,
      envelope.created_at,
      generatedAt,
    ),
    summary:
      content.workbook_source?.workbook_filename
        ? `Workbook source: ${content.workbook_source.workbook_filename}`
        : "Workbook profile is available from the intelligence service.",
    completion: 0,
    trackedSheets,
    missingSections,
    owner: undefined,
    sheetStats: pickList([
      typeof structure?.sheet_count_found === "number"
        ? `${structure.sheet_count_found} sheet(s) found`
        : undefined,
      typeof structure?.expected_sheet_count === "number"
        ? `${structure.expected_sheet_count} expected`
        : undefined,
      content.template_name ? `Template: ${content.template_name}` : undefined,
      content.template_match
        ? `Template match: ${formatContractLabel(content.template_match)}`
        : undefined,
    ]),
    notes: pickList([
      content.parser_report_status
        ? `Parser status: ${formatContractLabel(content.parser_report_status)}`
        : undefined,
      content.pairing_validation?.pairing_status
        ? `Pairing: ${formatContractLabel(content.pairing_validation.pairing_status)}`
        : undefined,
      content.pairing_validation?.notes ?? undefined,
      ...extraSheets.map((sheet) => `Extra sheet: ${sheet}`),
    ]),
  };
}

export function translateLiveWorkbookReview(
  envelope: IntelligenceArtifactEnvelope<IntelligenceWorkbookReviewContent>,
): WorkbookReviewModel {
  const content = envelope.content ?? {};
  const generatedAt = content.artifact_meta?.generated_at;
  const findings = [
    ...(content.structural_completeness_findings ?? []),
    ...(content.workbook_internal_consistency_findings ?? []),
    ...(content.intake_vs_workbook_findings ?? []),
    ...(content.benchmark_outlier_findings ?? []),
  ].map(translateFinding);

  return {
    kind: "workbook_review",
    status: toProcessingState(envelope.status),
    availability: toAvailabilityState(envelope.status),
    version: formatArtifactVersion(envelope.version),
    updatedLabel: resolveUpdatedLabel(envelope.updated_at, envelope.created_at, generatedAt),
    updatedAtValue: resolveArtifactTimestamp(
      envelope.updated_at,
      envelope.created_at,
      generatedAt,
    ),
    summary:
      content.summary?.review_posture
        ? `Review posture: ${formatContractLabel(content.summary.review_posture)}`
        : "Workbook review metadata is available.",
    readiness: 0,
    missingResponses: 0,
    activeFindingsCount: content.summary?.active_findings_count ?? undefined,
    unavailableFamilies: content.summary?.unavailable_families ?? [],
    findings,
    flags: findings.map((finding) => ({
      severity: finding.severity,
      label: finding.title,
      detail: finding.detail,
    })),
  };
}
