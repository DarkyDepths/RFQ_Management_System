import type {
  IntelligenceApiArtifactStatus,
  IntelligenceApiArtifactType,
} from "@/models/intelligence/api";
import type { ArtifactKind, ArtifactStatus } from "@/models/intelligence/artifacts";
import type {
  IntelligenceAvailabilityState,
  ProcessingState,
} from "@/models/intelligence/snapshot";
import { formatDate } from "@/utils/format";

export function formatContractLabel(value?: string | null) {
  if (!value) {
    return "Unknown";
  }

  return value
    .replaceAll("_", " ")
    .replaceAll("-", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function formatArtifactVersion(value?: number | string | null) {
  if (value === undefined || value === null || value === "") {
    return undefined;
  }

  if (typeof value === "number") {
    return `v${value}`;
  }

  return String(value);
}

export function resolveArtifactTimestamp(
  updatedAt?: string | null,
  createdAt?: string | null,
  generatedAt?: string | null,
) {
  return updatedAt ?? createdAt ?? generatedAt ?? undefined;
}

export function resolveUpdatedLabel(
  updatedAt?: string | null,
  createdAt?: string | null,
  generatedAt?: string | null,
) {
  return formatDate(resolveArtifactTimestamp(updatedAt, createdAt, generatedAt));
}

export function toAvailabilityState(
  value?: string | null,
  options?: {
    preliminary?: boolean;
  },
): IntelligenceAvailabilityState {
  const normalized = value?.trim().toLowerCase();

  if (normalized === "complete" || normalized === "available" || normalized === "recorded") {
    return "available";
  }

  if (normalized === "pending" || normalized === "processing") {
    return "pending";
  }

  if (normalized === "failed") {
    return "failed";
  }

  if (
    normalized === "not_ready" ||
    normalized === "not uploaded" ||
    normalized === "not_uploaded" ||
    normalized === "unavailable"
  ) {
    return "not_available_yet";
  }

  if (normalized === "limited") {
    return "preliminary";
  }

  if (
    normalized === "partial" ||
    normalized === "partial_deterministic" ||
    normalized === "deterministic_enriched" ||
    normalized === "ready_from_package_intake"
  ) {
    return options?.preliminary ? "preliminary" : "partial";
  }

  if (normalized === "insufficient_historical_base") {
    return "not_available_yet";
  }

  return options?.preliminary ? "preliminary" : "partial";
}

export function toArtifactStatus(
  status: IntelligenceApiArtifactStatus | "not_uploaded",
): ArtifactStatus {
  return status;
}

export function toProcessingState(status: IntelligenceApiArtifactStatus): ProcessingState {
  return status;
}

export function mapArtifactTypeToKind(type: IntelligenceApiArtifactType): ArtifactKind {
  switch (type) {
    case "rfq_intelligence_snapshot":
      return "snapshot";
    case "intelligence_briefing":
      return "briefing";
    case "workbook_profile":
      return "workbook_profile";
    case "workbook_review_report":
      return "workbook_review";
    case "rfq_intake_profile":
      return "intake_profile";
    case "cost_breakdown_profile":
      return "cost_breakdown";
    case "parser_report":
      return "parser_report";
    case "rfq_analytical_record":
      return "analytical_record";
    default:
      return "other";
  }
}

export function summarizeArtifactStatus(
  type: IntelligenceApiArtifactType,
  status: ArtifactStatus,
  isCurrent?: boolean,
  schemaVersion?: string,
) {
  const kindLabel = formatContractLabel(type);

  if (!isCurrent) {
    return `Historical ${kindLabel} version retained for traceability.`;
  }

  if (status === "failed") {
    return `Current ${kindLabel} artifact is marked failed.`;
  }

  if (status === "pending") {
    return `Current ${kindLabel} artifact is still pending generation.`;
  }

  if (status === "partial") {
    return `Current ${kindLabel} artifact is available in a partial slice${schemaVersion ? ` (${schemaVersion})` : ""}.`;
  }

  if (status === "not_uploaded") {
    return `Current ${kindLabel} artifact is waiting for workbook input.`;
  }

  return `Current ${kindLabel} artifact is available${schemaVersion ? ` (${schemaVersion})` : ""}.`;
}

export function pickList(values: Array<string | null | undefined>) {
  return values.filter((value): value is string => Boolean(value && value.trim().length > 0));
}
