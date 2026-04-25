export type ProcessingState = "pending" | "partial" | "complete" | "failed";
export type IntelligenceAvailabilityState =
  | "not_available_yet"
  | "pending"
  | "partial"
  | "preliminary"
  | "failed"
  | "available";

export interface SnapshotFlagResponse {
  severity: "low" | "medium" | "high";
  label: string;
  detail: string;
}

export interface SnapshotResponse {
  rfqId: string;
  state: ProcessingState;
  intake: {
    status: ProcessingState;
    summary: string;
    sectionsDetected: number;
    lineItems: number;
    processedAt?: string;
    missing: string[];
  };
  briefing: {
    status: ProcessingState;
    summary: string;
    generatedAt?: string;
    strengths: string[];
    risks: string[];
  };
  workbook: {
    status: ProcessingState | "not_uploaded";
    uploadedAt?: string;
    reviewStatus: ProcessingState | "not_uploaded";
    pendingQuestions: string[];
  };
  quality: {
    summary: string;
    gaps: string[];
  };
  readiness: {
    score: number;
    confidence: number;
    blockers: string[];
  };
  reviewFlags: SnapshotFlagResponse[];
}

export interface IntelligencePortfolioResponse {
  completeCount: number;
  partialCount: number;
  failedCount: number;
  readinessAverage: number;
  narrative: string;
  featuredRfqId: string;
}

export interface SnapshotFlagModel extends SnapshotFlagResponse {}

export interface IntelligenceSnapshotModel {
  kind: "snapshot";
  state: ProcessingState;
  availability: IntelligenceAvailabilityState;
  version?: string;
  updatedLabel: string;
  updatedAtValue?: string;
  generatedLabel: string;
  generatedAtValue?: string;
  summary: string;
  requiresHumanReview: boolean;
  recommendedTabs: string[];
  suggestedQuestions: string[];
  availabilityMatrix: Array<{
    label: string;
    value: string;
  }>;
  intake: {
    availability: IntelligenceAvailabilityState;
    statusLabel: string;
    summary: string;
    bullets: string[];
  };
  briefing: {
    availability: IntelligenceAvailabilityState;
    statusLabel: string;
    summary: string;
    bullets: string[];
  };
  workbook: {
    availability: IntelligenceAvailabilityState;
    statusLabel: string;
    summary: string;
    bullets: string[];
  };
  review: {
    availability: IntelligenceAvailabilityState;
    statusLabel: string;
    summary: string;
    bullets: string[];
  };
  reviewFlags: SnapshotFlagModel[];
}
