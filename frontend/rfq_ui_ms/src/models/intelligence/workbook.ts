import type {
  IntelligenceAvailabilityState,
  ProcessingState,
  SnapshotFlagResponse,
} from "@/models/intelligence/snapshot";

export interface WorkbookProfileResponse {
  rfqId: string;
  status: ProcessingState | "not_uploaded";
  version: string;
  updatedAt?: string;
  completion: number;
  trackedSheets: string[];
  missingSections: string[];
  owner: string;
}

export interface WorkbookReviewResponse {
  rfqId: string;
  status: ProcessingState | "not_uploaded";
  version: string;
  updatedAt?: string;
  readiness: number;
  missingResponses: number;
  flags: SnapshotFlagResponse[];
}

export interface WorkbookProfileModel {
  kind: "workbook_profile";
  status: ProcessingState | "not_uploaded";
  availability: IntelligenceAvailabilityState;
  version?: string;
  updatedLabel: string;
  updatedAtValue?: string;
  summary: string;
  completion: number;
  trackedSheets: string[];
  missingSections: string[];
  owner?: string;
  sheetStats: string[];
  notes: string[];
}

export interface WorkbookReviewFindingModel {
  id: string;
  severity: "low" | "medium" | "high";
  title: string;
  detail: string;
  family?: string;
  status?: string;
}

export interface WorkbookReviewModel {
  kind: "workbook_review";
  status: ProcessingState | "not_uploaded";
  availability: IntelligenceAvailabilityState;
  version?: string;
  updatedLabel: string;
  updatedAtValue?: string;
  summary: string;
  readiness: number;
  missingResponses: number;
  activeFindingsCount?: number;
  unavailableFamilies: string[];
  findings: WorkbookReviewFindingModel[];
  flags: SnapshotFlagResponse[];
}
