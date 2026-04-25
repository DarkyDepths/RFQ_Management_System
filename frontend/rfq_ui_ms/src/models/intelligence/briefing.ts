import type {
  IntelligenceAvailabilityState,
  ProcessingState,
} from "@/models/intelligence/snapshot";

export interface BriefingResponse {
  rfqId: string;
  status: ProcessingState;
  version: string;
  updatedAt?: string;
  executiveSummary: string;
  strategicSignals: string[];
  openQuestions: string[];
  recommendation: string;
}

export interface BriefingArtifactModel {
  kind: "briefing";
  status: ProcessingState;
  availability: IntelligenceAvailabilityState;
  title: string;
  version?: string;
  updatedLabel: string;
  updatedAtValue?: string;
  summary: string;
  keySignals: string[];
  openQuestions: string[];
  recommendedActions: string[];
  limitations: string[];
  sectionAvailability: Array<{
    label: string;
    value: string;
  }>;
  preliminary: boolean;
}
