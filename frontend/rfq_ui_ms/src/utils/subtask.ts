export const SUBTASK_DUE_DATE_WINDOW_MESSAGE =
  "Subtask due date must fall within the current stage window.";
export const SUBTASK_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE =
  "Subtask due date cannot be set because the current stage schedule is incomplete.";
export const SUBTASK_PROGRESS_DECREASE_MESSAGE =
  "Subtask progress cannot move backward once saved.";
export const SUBTASK_NAME_REQUIRED_MESSAGE = "Subtask name is required.";
export const SUBTASK_ASSIGNEE_REQUIRED_MESSAGE =
  "Please assign the subtask before creating it.";
export const SUBTASK_DUE_DATE_REQUIRED_MESSAGE =
  "Please choose a subtask due date before creating it.";

type SubtaskStatus = "Open" | "In progress" | "Done";

type ResolvedSubtaskStageWindow = {
  startValue?: string;
  endValue?: string;
  mode: "planned" | "shifted_actual" | "actual" | "incomplete";
};

function differenceInDays(startValue: string, endValue: string) {
  const start = new Date(`${startValue}T00:00:00Z`);
  const end = new Date(`${endValue}T00:00:00Z`);
  const diffMs = end.getTime() - start.getTime();
  return Number.isFinite(diffMs) ? Math.max(Math.round(diffMs / 86400000), 0) : 0;
}

function addDaysToIsoDate(value: string, days: number) {
  const next = new Date(`${value}T00:00:00Z`);
  next.setUTCDate(next.getUTCDate() + days);
  return next.toISOString().slice(0, 10);
}

export function resolveSubtaskStageWindow(
  plannedStartValue?: string,
  plannedEndValue?: string,
  actualStartValue?: string,
  actualEndValue?: string,
): ResolvedSubtaskStageWindow {
  if (actualStartValue && actualEndValue) {
    return {
      startValue: actualStartValue,
      endValue: actualEndValue,
      mode: "actual",
    };
  }

  if (actualStartValue) {
    if (!plannedStartValue || !plannedEndValue) {
      return { mode: "incomplete" };
    }

    const plannedDurationDays = differenceInDays(plannedStartValue, plannedEndValue);
    const shiftedEndValue = addDaysToIsoDate(actualStartValue, plannedDurationDays);

    return {
      startValue: actualStartValue,
      endValue: shiftedEndValue > plannedEndValue ? shiftedEndValue : plannedEndValue,
      mode: "shifted_actual",
    };
  }

  if (!plannedStartValue || !plannedEndValue) {
    return { mode: "incomplete" };
  }

  return {
    startValue: plannedStartValue,
    endValue: plannedEndValue,
    mode: "planned",
  };
}

export function deriveSubtaskStatusFromProgress(
  progress: string | number,
): SubtaskStatus | null {
  const parsedProgress =
    typeof progress === "number" ? progress : Number.parseInt(progress, 10);

  if (!Number.isFinite(parsedProgress)) {
    return null;
  }

  if (parsedProgress <= 0) {
    return "Open";
  }

  if (parsedProgress >= 100) {
    return "Done";
  }

  return "In progress";
}

export function normalizeSubtaskDraftState<
  T extends {
    progress: string;
    status: SubtaskStatus;
  },
>(draft: T): T {
  const nextStatus = deriveSubtaskStatusFromProgress(draft.progress);
  if (!nextStatus) {
    return draft;
  }

  if (draft.status !== nextStatus) {
    return {
      ...draft,
      status: nextStatus,
    };
  }

  return draft;
}

export function getSubtaskCreateValidationMessage(
  name: string,
  assignedTo: string,
  dueDate: string,
  plannedStartValue?: string,
  plannedEndValue?: string,
  actualStartValue?: string,
  actualEndValue?: string,
) {
  if (!name.trim()) {
    return SUBTASK_NAME_REQUIRED_MESSAGE;
  }

  if (!assignedTo.trim()) {
    return SUBTASK_ASSIGNEE_REQUIRED_MESSAGE;
  }

  if (!dueDate) {
    return SUBTASK_DUE_DATE_REQUIRED_MESSAGE;
  }

  return getSubtaskDueDateValidationMessage(
    dueDate,
    plannedStartValue,
    plannedEndValue,
    actualStartValue,
    actualEndValue,
  );
}

export function getSubtaskDueDateValidationMessage(
  dueDate: string,
  plannedStartValue?: string,
  plannedEndValue?: string,
  actualStartValue?: string,
  actualEndValue?: string,
) {
  if (!dueDate) {
    return null;
  }

  const window = resolveSubtaskStageWindow(
    plannedStartValue,
    plannedEndValue,
    actualStartValue,
    actualEndValue,
  );

  if (!window.startValue || !window.endValue) {
    return SUBTASK_DUE_DATE_SCHEDULE_INCOMPLETE_MESSAGE;
  }

  if (dueDate < window.startValue || dueDate > window.endValue) {
    return SUBTASK_DUE_DATE_WINDOW_MESSAGE;
  }

  return null;
}

export function getSubtaskProgressValidationMessage(
  progress: string,
  persistedProgress?: number,
) {
  if (persistedProgress === undefined) {
    return null;
  }

  const parsedProgress = Number.parseInt(progress, 10);
  if (!Number.isFinite(parsedProgress)) {
    return null;
  }

  if (parsedProgress < persistedProgress) {
    return SUBTASK_PROGRESS_DECREASE_MESSAGE;
  }

  return null;
}
