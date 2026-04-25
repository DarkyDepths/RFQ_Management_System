import { apiConfig } from "@/config/api";
import { requestManagerJson } from "@/connectors/manager/base";
import type {
  ManagerApiReminderCreateInput,
  ManagerApiReminderListResponse,
  ManagerApiReminderRuleListResponse,
  ManagerApiReminderRuleUpdateInput,
  ManagerApiReminderStats,
} from "@/models/manager/api-reminder";
import type {
  ReminderCreateInput,
  ReminderModel,
  ReminderRuleModel,
  ReminderStatsModel,
} from "@/models/manager/rfq";
import {
  translateManagerReminder,
  translateManagerReminderRule,
  translateManagerReminderStats,
} from "@/translators/manager/reminders";

interface ReminderListFilters {
  rfqId?: string;
  status?: string;
  user?: string;
}

const DEMO_REMINDER_UNAVAILABLE_MESSAGE =
  "Reminder service stays live-only in this phase. Switch to live mode for reminder operations.";

export async function listReminders(
  filters: ReminderListFilters = {},
): Promise<ReminderModel[]> {
  if (apiConfig.useMockData) {
    return [];
  }

  const response = await requestManagerJson<ManagerApiReminderListResponse>(
    "/reminders",
    undefined,
    {
      rfq_id: filters.rfqId,
      status: filters.status,
      user: filters.user,
    },
  );

  return response.data.map(translateManagerReminder);
}

export async function getRfqReminders(
  rfqId: string,
): Promise<ReminderModel[]> {
  return listReminders({ rfqId });
}

export async function getReminderStats(): Promise<ReminderStatsModel> {
  if (apiConfig.useMockData) {
    return {
      dueThisWeek: 0,
      openTasks: 0,
      overdueTasks: 0,
      withActiveReminders: 0,
    };
  }

  const response = await requestManagerJson<ManagerApiReminderStats>(
    "/reminders/stats",
  );

  return translateManagerReminderStats(response);
}

export async function getReminderRules(): Promise<ReminderRuleModel[]> {
  if (apiConfig.useMockData) {
    return [];
  }

  const response = await requestManagerJson<ManagerApiReminderRuleListResponse>(
    "/reminders/rules",
  );

  return response.data.map(translateManagerReminderRule);
}

export async function createReminder(
  input: ReminderCreateInput,
): Promise<void> {
  if (apiConfig.useMockData) {
    throw new Error(DEMO_REMINDER_UNAVAILABLE_MESSAGE);
  }

  await requestManagerJson(
    "/reminders",
    {
      method: "POST",
      body: JSON.stringify({
        rfq_id: input.rfqId,
        rfq_stage_id: input.rfqStageId,
        type: input.type,
        message: input.message,
        due_date: input.dueDate,
        assigned_to: input.assignedTo,
      } satisfies ManagerApiReminderCreateInput),
    },
  );
}

export async function resolveReminder(
  reminderId: string,
): Promise<void> {
  if (apiConfig.useMockData) {
    throw new Error(DEMO_REMINDER_UNAVAILABLE_MESSAGE);
  }

  await requestManagerJson(
    `/reminders/${reminderId}/resolve`,
    {
      method: "POST",
    },
  );
}

export async function processReminders(): Promise<string> {
  if (apiConfig.useMockData) {
    throw new Error(DEMO_REMINDER_UNAVAILABLE_MESSAGE);
  }

  const response = await requestManagerJson<{ message: string }>(
    "/reminders/process",
    {
      method: "POST",
    },
  );

  return response.message;
}

export async function sendReminderTestEmail(): Promise<string> {
  if (apiConfig.useMockData) {
    throw new Error(DEMO_REMINDER_UNAVAILABLE_MESSAGE);
  }

  const response = await requestManagerJson<{ message: string }>(
    "/reminders/test",
    {
      method: "POST",
    },
  );

  return response.message;
}

export async function updateReminderRule(
  ruleId: string,
  isActive: boolean,
): Promise<void> {
  if (apiConfig.useMockData) {
    throw new Error(DEMO_REMINDER_UNAVAILABLE_MESSAGE);
  }

  await requestManagerJson(
    `/reminders/rules/${ruleId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        is_active: isActive,
      } satisfies ManagerApiReminderRuleUpdateInput),
    },
  );
}
