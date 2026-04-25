import type { AppRole } from "@/models/ui/role";

export type StageProgressState =
  | "completed"
  | "active"
  | "upcoming"
  | "blocked"
  | "skipped";

export type StageLifecycleEventType =
  | "decision_recorded"
  | "blocker_created"
  | "blocker_updated"
  | "blocker_resolved"
  | "terminal_outcome_recorded";

export interface ManagerStageTemplateResponse {
  id: string;
  label: string;
  order: number;
  summary: string;
  ownerRole: AppRole | "shared";
  plannedDurationDays?: number;
  isRequired?: boolean;
}

export interface ManagerStageStatusResponse
  extends ManagerStageTemplateResponse {
  state: StageProgressState;
  timestamp?: string;
}

export interface StageTemplateModel {
  id: string;
  label: string;
  order: number;
  summary?: string;
  ownerRole?: AppRole | "shared";
  assignedTeam?: string;
  plannedDurationDays?: number;
  isRequired?: boolean;
}

export interface StageProgressModel extends StageTemplateModel {
  state: StageProgressState;
  timestampLabel?: string;
  progress?: number;
  statusLabel?: string;
  blockerReasonCode?: string;
}

export interface StageLifecycleEventModel {
  id: string;
  type: StageLifecycleEventType;
  timestampValue?: string;
  timestampLabel: string;
  actorName?: string;
  fieldKey?: string;
  fieldLabel?: string;
  value?: string;
  valueLabel?: string;
  reason?: string;
  detail?: string;
  source?: "automatic" | "manual";
  title: string;
  summary: string;
  tone: "steel" | "amber" | "emerald" | "rose";
}

export interface StageWorkspaceModel extends StageProgressModel {
  capturedData: Record<string, string>;
  mandatoryFields: string[];
  lifecycleEvents: StageLifecycleEventModel[];
  blockerStatus?: "Blocked" | "Resolved";
  plannedStartValue?: string;
  plannedStartLabel?: string;
  plannedEndValue?: string;
  plannedEndLabel?: string;
  actualStartValue?: string;
  actualStartLabel?: string;
  actualEndValue?: string;
  actualEndLabel?: string;
}

export interface StageUpdateInput {
  capturedData?: Record<string, string>;
  blockerStatus?: "Blocked" | "Resolved";
  blockerReasonCode?: string;
}

export interface StageAdvanceInput {
  confirmNoGoCancel?: boolean;
  terminalOutcome?: string;
  lostReasonCode?: string;
  outcomeReason?: string;
}
