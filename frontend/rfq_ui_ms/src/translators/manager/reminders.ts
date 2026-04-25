import type {
  ManagerApiReminder,
  ManagerApiReminderRule,
  ManagerApiReminderStats,
} from "@/models/manager/api-reminder";
import type {
  ReminderModel,
  ReminderRuleModel,
  ReminderStatsModel,
} from "@/models/manager/rfq";
import { formatDate, formatDateTime } from "@/utils/format";

export function translateManagerReminder(
  reminder: ManagerApiReminder,
): ReminderModel {
  return {
    id: reminder.id,
    rfqId: reminder.rfq_id,
    rfqStageId: reminder.rfq_stage_id ?? undefined,
    rfqCode: reminder.rfq_code ?? undefined,
    rfqName: reminder.rfq_name ?? undefined,
    rfqDeadlineValue: reminder.rfq_deadline ?? undefined,
    rfqStageName: reminder.rfq_stage_name ?? undefined,
    source: reminder.source,
    type: reminder.type,
    message: reminder.message,
    dueDateValue: reminder.due_date,
    dueLabel: formatDate(reminder.due_date),
    status: reminder.status,
    delayDays: reminder.delay_days,
    assignedTo: reminder.assigned_to ?? undefined,
    createdBy: reminder.created_by ?? undefined,
    createdAtValue: reminder.created_at,
    createdLabel: formatDateTime(reminder.created_at),
    updatedAtValue: reminder.updated_at ?? undefined,
    updatedLabel: reminder.updated_at ? formatDateTime(reminder.updated_at) : undefined,
    lastSentAtValue: reminder.last_sent_at ?? undefined,
    lastSentLabel: reminder.last_sent_at ? formatDateTime(reminder.last_sent_at) : undefined,
    sendCount: reminder.send_count,
  };
}

export function translateManagerReminderStats(
  stats: ManagerApiReminderStats,
): ReminderStatsModel {
  return {
    openTasks: stats.open_tasks,
    overdueTasks: stats.overdue_tasks,
    dueThisWeek: stats.due_this_week,
    withActiveReminders: stats.with_active_reminders,
  };
}

export function translateManagerReminderRule(
  rule: ManagerApiReminderRule,
): ReminderRuleModel {
  return {
    id: rule.id,
    name: rule.name,
    description: rule.description ?? undefined,
    scope: rule.scope,
    isActive: rule.is_active,
    createdLabel: formatDate(rule.created_at),
  };
}
