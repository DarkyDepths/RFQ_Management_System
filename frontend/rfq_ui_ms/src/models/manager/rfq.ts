import type {
  ManagerStageStatusResponse,
  StageProgressModel,
} from "@/models/manager/stage";

export type LiveManagerRfqStatus =
  | "in_preparation"
  | "awarded"
  | "lost"
  | "cancelled";

export type DemoOnlyManagerRfqStatus =
  | "draft"
  | "under_review"
  | "submitted"
  | "attention_required";

export type ManagerRfqStatus =
  | LiveManagerRfqStatus
  | DemoOnlyManagerRfqStatus;

export type IntelligenceState = "pending" | "partial" | "complete" | "failed";
export type PriorityLevel = "critical" | "high" | "normal";

export interface ManagerMetricResponse {
  id: string;
  label: string;
  value: number;
  unit: "count" | "percent" | "days";
  helper: string;
  trendLabel: string;
  trendDirection: "up" | "down" | "steady";
  tone: "steel" | "gold" | "emerald" | "amber";
}

export interface ManagerRfqListItemResponse {
  id: string;
  title: string;
  client: string;
  owner: string;
  region: string;
  valueSar: number;
  dueDate: string;
  createdAt: string;
  updatedAt: string;
  workflowId: string;
  workflowName: string;
  status: ManagerRfqStatus;
  outcomeReason?: string;
  intelligenceState: IntelligenceState;
  priority: PriorityLevel;
  nextAction: string;
  summaryLine: string;
  tags: string[];
  stageHistory: ManagerStageStatusResponse[];
}

export interface ManagerRfqListResponse {
  items: ManagerRfqListItemResponse[];
  metrics: ManagerMetricResponse[];
}

export interface ManagerStageNoteResponse {
  id: string;
  stageId: string;
  author: string;
  note: string;
  createdAt: string;
  tone: "info" | "warning" | "success";
}

export interface ManagerFileResponse {
  id: string;
  label: string;
  type: string;
  uploadedAt: string;
  uploadedBy?: string;
  status: "processed" | "pending" | "rejected";
}

export interface ManagerSubtaskResponse {
  id: string;
  label: string;
  owner: string;
  dueDate: string;
  state: "open" | "in_progress" | "done";
}

export interface ManagerUploadSlotResponse {
  kind: "zip" | "workbook";
  title: string;
  description: string;
  status: "ready" | "processing" | "missing" | "failed";
  fileName?: string;
  uploadedAt?: string;
}

export interface ManagerRfqDetailResponse extends ManagerRfqListItemResponse {
  description: string;
  industry?: string;
  country?: string;
  outcomeReason?: string;
  sourcePackageAvailable?: boolean;
  sourcePackageUpdatedAt?: string;
  workbookAvailable?: boolean;
  workbookUpdatedAt?: string;
  procurementLead: string;
  estimatedSubmissionDate: string;
  stageNotes: ManagerStageNoteResponse[];
  recentFiles: ManagerFileResponse[];
  subtasks: ManagerSubtaskResponse[];
  uploads: ManagerUploadSlotResponse[];
}

export interface DashboardMetricModel {
  id: string;
  label: string;
  value: string;
  helper: string;
  trendLabel: string;
  trendDirection: "up" | "down" | "steady";
  tone: "steel" | "gold" | "emerald" | "amber";
}

export interface StageNoteModel {
  id: string;
  author: string;
  note: string;
  createdAtValue?: string;
  createdLabel: string;
  tone?: "info" | "warning" | "success";
}

export interface RfqFileModel {
  id: string;
  label: string;
  type: string;
  uploadedAtValue?: string;
  uploadedLabel: string;
  status?: "processed" | "pending" | "rejected";
  uploadedBy?: string;
  downloadUrl?: string;
  storageReference?: string;
}

export interface RfqSubtaskModel {
  id: string;
  label: string;
  owner: string;
  dueDateValue?: string;
  dueLabel: string;
  state: "open" | "in_progress" | "done";
  progress?: number;
}

export interface ReminderModel {
  id: string;
  rfqId: string;
  rfqStageId?: string | null;
  rfqCode?: string;
  rfqName?: string;
  rfqDeadlineValue?: string;
  rfqStageName?: string;
  source: "manual" | "automatic";
  type: "internal" | "external";
  message: string;
  dueDateValue: string;
  dueLabel: string;
  status: string;
  delayDays: number;
  assignedTo?: string;
  createdBy?: string;
  createdAtValue: string;
  createdLabel: string;
  updatedAtValue?: string;
  updatedLabel?: string;
  lastSentAtValue?: string;
  lastSentLabel?: string;
  sendCount: number;
}

export interface ReminderStatsModel {
  openTasks: number;
  overdueTasks: number;
  dueThisWeek: number;
  withActiveReminders: number;
}

export interface ReminderRuleModel {
  id: string;
  name: string;
  description?: string;
  scope: string;
  isActive: boolean;
  createdLabel: string;
}

export interface UploadSlotModel {
  kind: "zip" | "workbook";
  title: string;
  description: string;
  status: "ready" | "processing" | "missing" | "failed";
  fileName?: string;
  uploadedLabel?: string;
}

export interface RfqCardModel {
  id: string;
  rfqCode?: string;
  title: string;
  client: string;
  owner: string;
  workflowId?: string;
  region?: string;
  workflowName?: string;
  valueLabel?: string;
  dueDateValue: string;
  dueLabel: string;
  status: ManagerRfqStatus;
  statusLabel: string;
  outcomeReason?: string;
  intelligenceState?: IntelligenceState;
  priority: PriorityLevel;
  nextAction?: string;
  summaryLine?: string;
  tags: string[];
  stageLabel: string;
  rfqProgress: number;
  stageHistory: StageProgressModel[];
  blockerStatus?: "Blocked";
  blockerReasonCode?: string;
  updatedAtValue?: string;
  updatedAtLabel?: string;
}

export interface RfqDetailModel extends RfqCardModel {
  description?: string;
  industry?: string;
  procurementLead?: string;
  estimatedSubmissionLabel?: string;
  currentStageId?: string | null;
  sourcePackageAvailable: boolean;
  sourcePackageUpdatedAtValue?: string;
  sourcePackageUpdatedLabel?: string;
  workbookAvailable: boolean;
  workbookUpdatedAtValue?: string;
  workbookUpdatedLabel?: string;
  outcomeReason?: string;
  stageNotes: StageNoteModel[];
  recentFiles: RfqFileModel[];
  subtasks: RfqSubtaskModel[];
  uploads: UploadSlotModel[];
}

export interface CreateRfqInput {
  name: string;
  client: string;
  owner: string;
  workflowId: string;
  skipStageIds?: string[];
  deadline: string;
  priority: "normal" | "critical";
  description?: string;
  industry: string;
  country: string;
}

export interface UpdateRfqInput {
  name?: string;
  client?: string;
  industry?: string;
  country?: string;
  priority?: "normal" | "critical";
  deadline?: string;
  owner?: string;
  description?: string;
  outcomeReason?: string;
}

export interface CancelRfqInput {
  outcomeReason: string;
}

export interface RfqMutationResult {
  id: string;
  message: string;
  status: "demo_staged" | "created" | "updated";
}

export interface SubtaskCreateInput {
  name: string;
  assignedTo: string;
  dueDate: string;
}

export interface SubtaskUpdateInput {
  name?: string;
  assignedTo?: string;
  dueDate?: string;
  progress?: number;
  status?: "Open" | "In progress" | "Done";
}

export interface ReminderCreateInput {
  rfqId: string;
  rfqStageId?: string;
  type: "internal" | "external";
  message: string;
  dueDate: string;
  assignedTo?: string;
}
