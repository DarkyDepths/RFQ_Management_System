export interface ManagerApiReminder {
  id: string;
  rfq_id: string;
  rfq_stage_id?: string | null;
  rfq_code?: string | null;
  rfq_name?: string | null;
  rfq_deadline?: string | null;
  rfq_stage_name?: string | null;
  source: "manual" | "automatic";
  type: "internal" | "external";
  message: string;
  due_date: string;
  assigned_to?: string | null;
  status: string;
  delay_days: number;
  created_by?: string | null;
  created_at: string;
  updated_at?: string | null;
  last_sent_at?: string | null;
  send_count: number;
}

export interface ManagerApiReminderListResponse {
  data: ManagerApiReminder[];
}

export interface ManagerApiReminderStats {
  open_tasks: number;
  overdue_tasks: number;
  due_this_week: number;
  with_active_reminders: number;
}

export interface ManagerApiReminderRule {
  id: string;
  name: string;
  description?: string | null;
  scope: string;
  is_active: boolean;
  created_at: string;
}

export interface ManagerApiReminderRuleListResponse {
  data: ManagerApiReminderRule[];
}

export interface ManagerApiReminderCreateInput {
  rfq_id: string;
  rfq_stage_id?: string;
  type: "internal" | "external";
  message: string;
  due_date: string;
  assigned_to?: string;
}

export interface ManagerApiReminderRuleUpdateInput {
  is_active: boolean;
}
