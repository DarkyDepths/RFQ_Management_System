import type {
  IntelligenceArtifactSummaryResponse,
} from "@/models/intelligence/api";
import type {
  ArtifactModel,
  ArtifactResponse,
} from "@/models/intelligence/artifacts";
import { artifactKindLabel, getAccentForArtifact } from "@/utils/status";
import {
  formatArtifactVersion,
  mapArtifactTypeToKind,
  resolveArtifactTimestamp,
  resolveUpdatedLabel,
  summarizeArtifactStatus,
  toArtifactStatus,
} from "@/translators/intelligence/shared";

export function translateArtifact(artifact: ArtifactResponse): ArtifactModel {
  return {
    id: artifact.id,
    kind: artifact.kind,
    title: artifact.title,
    version: artifact.version,
    status: artifact.status,
    updatedLabel: artifact.updatedAt ? resolveUpdatedLabel(artifact.updatedAt) : "Pending",
    updatedAtValue: resolveArtifactTimestamp(artifact.updatedAt),
    summary: artifact.summary,
    accent: getAccentForArtifact(artifact.kind),
  };
}

export function translateLiveArtifactSummary(
  artifact: IntelligenceArtifactSummaryResponse,
): ArtifactModel {
  const kind = mapArtifactTypeToKind(artifact.artifact_type);

  return {
    id: artifact.id,
    kind,
    title: artifactKindLabel[kind],
    version: formatArtifactVersion(artifact.version) ?? "Unknown",
    status: toArtifactStatus(artifact.status),
    updatedLabel: resolveUpdatedLabel(artifact.updated_at, artifact.created_at),
    updatedAtValue: resolveArtifactTimestamp(artifact.updated_at, artifact.created_at),
    summary: summarizeArtifactStatus(
      artifact.artifact_type,
      artifact.status,
      artifact.is_current,
      artifact.schema_version,
    ),
    schemaVersion: artifact.schema_version,
    isCurrent: artifact.is_current,
    accent: getAccentForArtifact(kind),
  };
}
