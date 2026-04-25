import type { ReminderModel } from "@/models/manager/rfq";
import { formatDate } from "@/utils/format";
import { resolveSubtaskStageWindow } from "@/utils/subtask";

export const REMINDER_PAST_DUE_DATE_MESSAGE =
  "Reminder due date cannot be in the past.";
export const REMINDER_RFQ_DUE_DATE_WINDOW_MESSAGE =
  "RFQ-level reminder due date must fall between today and the RFQ deadline.";
export const REMINDER_STAGE_DUE_DATE_WINDOW_MESSAGE =
  "Stage-linked reminder due date must fall within the current stage window.";
export const REMINDER_STAGE_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE =
  "Stage-linked reminder due date cannot be set because the current stage schedule is incomplete.";

type ReminderScope = "rfq" | "stage";

type ReminderDateWindow = {
  maxValue?: string;
  minValue?: string;
  mode: "rfq" | "planned" | "shifted_actual" | "actual" | "incomplete";
};

function maxIsoDate(left?: string, right?: string) {
  if (!left) {
    return right;
  }

  if (!right) {
    return left;
  }

  return left > right ? left : right;
}

export function getReminderScopeLabel(reminder: ReminderModel) {
  return reminder.rfqStageId ? "Stage-linked" : "RFQ-level";
}

export function getReminderTypeLabel(type: ReminderModel["type"]) {
  return type === "external" ? "External" : "Internal";
}

export function sortRemindersForDisplay(reminders: ReminderModel[]) {
  const statusRank: Record<string, number> = {
    overdue: 0,
    open: 1,
    resolved: 2,
  };

  return [...reminders].sort((left, right) => {
    const leftRank = statusRank[left.status] ?? 3;
    const rightRank = statusRank[right.status] ?? 3;
    if (leftRank !== rightRank) {
      return leftRank - rightRank;
    }

    if (left.dueDateValue !== right.dueDateValue) {
      return left.dueDateValue.localeCompare(right.dueDateValue);
    }

    return right.createdAtValue.localeCompare(left.createdAtValue);
  });
}

export function resolveReminderDateWindow(options: {
  actualEndValue?: string;
  actualStartValue?: string;
  plannedEndValue?: string;
  plannedStartValue?: string;
  rfqDeadlineValue?: string;
  scope: ReminderScope;
  todayValue: string;
}): ReminderDateWindow {
  const { rfqDeadlineValue, scope, todayValue } = options;

  if (scope === "rfq") {
    return {
      maxValue: rfqDeadlineValue,
      minValue: todayValue,
      mode: "rfq",
    };
  }

  const stageWindow = resolveSubtaskStageWindow(
    options.plannedStartValue,
    options.plannedEndValue,
    options.actualStartValue,
    options.actualEndValue,
  );

  if (!stageWindow.startValue || !stageWindow.endValue) {
    return { mode: "incomplete" };
  }

  return {
    maxValue: stageWindow.endValue,
    minValue: maxIsoDate(todayValue, stageWindow.startValue),
    mode: stageWindow.mode,
  };
}

export function getReminderDueDateValidationMessage(options: {
  actualEndValue?: string;
  actualStartValue?: string;
  dueDate: string;
  plannedEndValue?: string;
  plannedStartValue?: string;
  rfqDeadlineValue?: string;
  scope: ReminderScope;
  todayValue: string;
}) {
  if (!options.dueDate) {
    return null;
  }

  if (options.dueDate < options.todayValue) {
    return REMINDER_PAST_DUE_DATE_MESSAGE;
  }

  const window = resolveReminderDateWindow(options);
  if (options.scope === "stage" && window.mode === "incomplete") {
    return REMINDER_STAGE_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE;
  }

  if (!window.minValue || !window.maxValue) {
    return options.scope === "stage"
      ? REMINDER_STAGE_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE
      : REMINDER_RFQ_DUE_DATE_WINDOW_MESSAGE;
  }

  if (options.dueDate < window.minValue || options.dueDate > window.maxValue) {
    return options.scope === "stage"
      ? REMINDER_STAGE_DUE_DATE_WINDOW_MESSAGE
      : REMINDER_RFQ_DUE_DATE_WINDOW_MESSAGE;
  }

  return null;
}

export function getReminderDueDateHint(options: {
  actualEndValue?: string;
  actualStartValue?: string;
  plannedEndValue?: string;
  plannedStartValue?: string;
  rfqDeadlineValue?: string;
  scope: ReminderScope;
  todayValue: string;
}) {
  const window = resolveReminderDateWindow(options);

  if (options.scope === "rfq") {
    if (!window.maxValue) {
      return "Reminder due date is limited to the RFQ lifecycle window.";
    }

    return `RFQ-level reminders must be due between today and ${formatDate(window.maxValue)}.`;
  }

  if (window.mode === "incomplete" || !window.minValue || !window.maxValue) {
    return REMINDER_STAGE_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE;
  }

  const timelineLabel =
    window.mode === "actual"
      ? "actual stage execution window"
      : window.mode === "shifted_actual"
        ? "shifted actual stage window"
        : "planned stage window";

  return `Stage-linked reminders must be due within the ${timelineLabel}: ${formatDate(window.minValue)} to ${formatDate(window.maxValue)}.`;
}
