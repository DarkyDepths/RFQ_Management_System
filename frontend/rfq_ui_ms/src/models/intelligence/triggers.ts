export interface IntelligenceLifecycleArtifactResult {
  id?: string | null;
  status?: string | null;
  version?: number | null;
}

export interface IntelligenceLifecycleTriggerResult {
  status: string;
  eventId?: string;
  eventType?: string;
  rfqId?: string;
  reason?: string;
  artifacts?: Record<string, IntelligenceLifecycleArtifactResult>;
}

export interface TriggerWorkbookInput {
  workbookRef?: string;
  workbookFilename?: string;
  uploadedAt?: string;
}

export interface TriggerOutcomeInput {
  outcome: "awarded" | "lost" | "cancelled";
  outcomeReason?: string;
  recordedAt?: string;
}
