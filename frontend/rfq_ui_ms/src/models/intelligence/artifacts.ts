import type { ProcessingState } from "@/models/intelligence/snapshot";

export type ArtifactKind =
  | "analytical_record"
  | "briefing"
  | "cost_breakdown"
  | "intake_profile"
  | "other"
  | "parser_report"
  | "workbook_profile"
  | "workbook_review"
  | "snapshot";

export type ArtifactStatus = ProcessingState | "not_uploaded";

export interface ArtifactResponse {
  id: string;
  rfqId: string;
  kind: ArtifactKind;
  title: string;
  version: string;
  status: ArtifactStatus;
  updatedAt?: string;
  summary: string;
  owner: string;
}

export interface ArtifactModel {
  id: string;
  kind: ArtifactKind;
  title: string;
  version: string;
  status: ArtifactStatus;
  updatedLabel: string;
  updatedAtValue?: string;
  summary: string;
  schemaVersion?: string;
  isCurrent?: boolean;
  accent: "steel" | "gold" | "emerald" | "rose";
}

export type ReprocessKind = "intake" | "workbook";

export interface ReprocessResult {
  kind: ReprocessKind;
  accepted: boolean;
  message: string;
  status: string;
}
