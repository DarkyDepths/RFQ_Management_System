export interface ManagerApiWorkflowStageTemplate {
  id: string;
  name: string;
  order: number;
  default_team?: string | null;
  planned_duration_days: number;
  is_required?: boolean;
}

export interface ManagerApiWorkflowSummary {
  id: string;
  name: string;
  code: string;
  stage_count: number;
  is_active: boolean;
  is_default: boolean;
  selection_mode?: "fixed" | "customizable";
  base_workflow_id?: string | null;
}

export interface ManagerApiWorkflowListResponse {
  data: ManagerApiWorkflowSummary[];
}

export interface ManagerApiWorkflowDetail extends ManagerApiWorkflowSummary {
  description?: string | null;
  stages: ManagerApiWorkflowStageTemplate[];
}
