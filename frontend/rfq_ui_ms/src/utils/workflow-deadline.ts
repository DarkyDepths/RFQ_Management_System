import type { StageTemplateModel } from "@/models/manager/stage";
import type { WorkflowModel } from "@/models/manager/workflow";

const monthLabels = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function getLocalDateIsoString(baseDate = new Date()) {
  const year = baseDate.getFullYear();
  const month = `${baseDate.getMonth() + 1}`.padStart(2, "0");
  const day = `${baseDate.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDaysToLocalDate(baseDate: Date, dayOffset: number) {
  const nextDate = new Date(baseDate);
  nextDate.setDate(nextDate.getDate() + dayOffset);
  return getLocalDateIsoString(nextDate);
}

function sumWorkflowStageDurations(stages: StageTemplateModel[]) {
  const durations = stages
    .map((stage) => stage.plannedDurationDays)
    .filter((duration): duration is number => typeof duration === "number");

  if (durations.length !== stages.length || durations.length === 0) {
    return null;
  }

  return durations.reduce((total, duration) => total + duration, 0);
}

export function getWorkflowPlannedDurationDays(
  workflow?: WorkflowModel | null,
) {
  if (!workflow) {
    return null;
  }

  const stageDurationDays = sumWorkflowStageDurations(workflow.stages);
  if (stageDurationDays !== null) {
    return stageDurationDays;
  }

  return typeof workflow.turnaroundDays === "number"
    ? workflow.turnaroundDays
    : null;
}

export function getMinimumWorkflowFeasibleDeadlineIso(
  workflow?: WorkflowModel | null,
  baseDate = new Date(),
) {
  const durationDays = getWorkflowPlannedDurationDays(workflow);
  if (durationDays === null) {
    return null;
  }

  return addDaysToLocalDate(baseDate, durationDays);
}

export function buildWorkflowDeadlineTooNarrowMessage(
  minimumDeadlineIso: string,
) {
  return `This deadline is too narrow for the selected workflow. Choose ${formatWorkflowDeadlineIso(minimumDeadlineIso)} or later.`;
}

export function formatWorkflowDeadlineIso(deadlineIso: string) {
  const [year, month, day] = deadlineIso.split("-").map(Number);
  return Number.isInteger(year) &&
    Number.isInteger(month) &&
    Number.isInteger(day) &&
    month >= 1 &&
    month <= 12
    ? `${`${day}`.padStart(2, "0")} ${monthLabels[month - 1]} ${year}`
    : deadlineIso;
}

export { getLocalDateIsoString, addDaysToLocalDate };
