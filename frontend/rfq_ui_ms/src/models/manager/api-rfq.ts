export type ManagerApiRfqStatus =
  | "In preparation"
  | "Awarded"
  | "Lost"
  | "Cancelled";

export type ManagerApiPriority = "normal" | "critical";

export interface ManagerApiRfqSummary {
  id: string;
  rfq_code?: string | null;
  name: string;
  client: string;
  country?: string | null;
  owner: string;
  priority: ManagerApiPriority;
  status: ManagerApiRfqStatus;
  progress: number;
  deadline: string;
  current_stage_id?: string | null;
  current_stage_name?: string | null;
  current_stage_order?: number | null;
  current_stage_status?: string | null;
  current_stage_blocker_status?: "Blocked" | null;
  current_stage_blocker_reason_code?: string | null;
  workflow_name?: string | null;
}

export interface ManagerApiRfqListResponse {
  data: ManagerApiRfqSummary[];
  total: number;
  page: number;
  size: number;
}

export interface ManagerApiRfqDetail {
  id: string;
  rfq_code?: string | null;
  name: string;
  client: string;
  status: ManagerApiRfqStatus;
  progress: number;
  deadline: string;
  current_stage_name?: string | null;
  workflow_name?: string | null;
  industry?: string | null;
  country?: string | null;
  priority: ManagerApiPriority;
  owner: string;
  description?: string | null;
  workflow_id: string;
  current_stage_id?: string | null;
  source_package_available: boolean;
  source_package_updated_at?: string | null;
  workbook_available: boolean;
  workbook_updated_at?: string | null;
  outcome_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ManagerApiRfqStats {
  total_rfqs_12m: number;
  open_rfqs: number;
  critical_rfqs: number;
  avg_cycle_days: number;
}

export interface ManagerApiRfqAnalyticsByClient {
  client: string;
  rfq_count: number;
  avg_margin: number | null;
}

export interface ManagerApiRfqAnalytics {
  avg_margin_submitted: number | null;
  avg_margin_awarded: number | null;
  estimation_accuracy: number | null;
  win_rate: number;
  by_client: ManagerApiRfqAnalyticsByClient[];
}

export interface ManagerApiCreateRfqInput {
  name: string;
  client: string;
  deadline: string;
  owner: string;
  workflow_id: string;
  skip_stages?: string[];
  industry: string;
  country: string;
  priority: "normal" | "critical";
  description?: string;
}

export interface ManagerApiUpdateRfqInput {
  name?: string;
  client?: string;
  industry?: string;
  country?: string;
  priority?: "normal" | "critical";
  deadline?: string;
  owner?: string;
  description?: string;
  outcome_reason?: string;
}

export interface ManagerApiCancelRfqInput {
  outcome_reason: string;
}
