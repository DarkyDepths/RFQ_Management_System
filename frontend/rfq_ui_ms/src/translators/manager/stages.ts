import { apiConfig } from "@/config/api";
import type {
  ManagerApiStageDetail,
  ManagerApiStageFile,
  ManagerApiStageNote,
  ManagerApiStageSubtask,
  ManagerApiStageSummary,
} from "@/models/manager/api-stage";
import type { ManagerApiWorkflowStageTemplate } from "@/models/manager/api-workflow";
import type {
  RfqFileModel,
  RfqSubtaskModel,
  StageNoteModel,
} from "@/models/manager/rfq";
import type {
  ManagerStageStatusResponse,
  ManagerStageTemplateResponse,
  StageProgressModel,
  StageProgressState,
  StageTemplateModel,
  StageUpdateInput,
  StageWorkspaceModel,
} from "@/models/manager/stage";
import {
  isControlledStageDecisionField,
  normalizeControlledStageDecisionValue,
} from "@/utils/go-no-go";
import {
  isLifecycleHistorySupportField,
  parseLifecycleHistoryEvents,
} from "@/utils/lifecycle-history";
import {
  isLostReasonCodeField,
  isTerminalOutcomeField,
  normalizeLostReasonCode,
  normalizeTerminalOutcomeValue,
} from "@/utils/terminal-outcome";
import { formatDate } from "@/utils/format";

export function translateStageTemplate(
  stage: ManagerStageTemplateResponse,
): StageTemplateModel {
  return {
    id: stage.id,
    label: stage.label,
    order: stage.order,
    summary: stage.summary,
    ownerRole: stage.ownerRole,
    plannedDurationDays: stage.plannedDurationDays,
    isRequired: stage.isRequired,
  };
}

export function translateStageProgress(
  stage: ManagerStageStatusResponse,
): StageProgressModel {
  return {
    ...translateStageTemplate(stage),
    state: stage.state,
    timestampLabel: stage.timestamp ? formatDate(stage.timestamp) : undefined,
  };
}

function resolveStageProgressState(
  status: string,
  blockerStatus?: string | null,
): StageProgressState {
  if (blockerStatus === "Blocked") {
    return "blocked";
  }

  const normalized = status.trim().toLowerCase();

  if (normalized === "completed") {
    return "completed";
  }

  if (normalized === "skipped") {
    return "skipped";
  }

  if (normalized === "in progress") {
    return "active";
  }

  return "upcoming";
}

function resolveBlockerStatus(
  blockerStatus?: string | null,
): "Blocked" | "Resolved" | undefined {
  return blockerStatus === "Blocked" || blockerStatus === "Resolved"
    ? blockerStatus
    : undefined;
}

function resolveBlockerReasonCode(
  blockerStatus?: string | null,
  blockerReasonCode?: string | null,
) {
  const normalizedStatus = resolveBlockerStatus(blockerStatus);
  const normalizedReason = blockerReasonCode?.trim();

  if (!normalizedStatus || !normalizedReason) {
    return undefined;
  }

  return normalizedReason;
}

function resolveStageTimestamp(stage: ManagerApiStageSummary) {
  if (stage.actual_end) {
    return formatDate(stage.actual_end);
  }

  if (stage.actual_start) {
    return formatDate(stage.actual_start);
  }

  if (stage.planned_end) {
    return formatDate(stage.planned_end);
  }

  return undefined;
}

function resolveDownloadUrl(downloadUrl: string) {
  if (downloadUrl.startsWith("http")) {
    return downloadUrl;
  }

  return `${apiConfig.managerBaseUrl}${downloadUrl}`;
}

export function translateManagerWorkflowStageTemplate(
  stage: ManagerApiWorkflowStageTemplate,
): StageTemplateModel {
  return {
    id: stage.id,
    label: stage.name,
    order: stage.order,
    summary: `Planned duration: ${stage.planned_duration_days} day${
      stage.planned_duration_days === 1 ? "" : "s"
    }`,
    assignedTeam: stage.default_team ?? undefined,
    plannedDurationDays: stage.planned_duration_days,
    isRequired: stage.is_required ?? false,
  };
}

export function translateManagerStageSummary(
  stage: ManagerApiStageSummary,
): StageProgressModel {
  return {
    id: stage.id,
    label: stage.name,
    order: stage.order,
    summary: stage.assigned_team ? `Assigned team: ${stage.assigned_team}` : undefined,
    assignedTeam: stage.assigned_team ?? undefined,
    state: resolveStageProgressState(stage.status, stage.blocker_status),
    timestampLabel: resolveStageTimestamp(stage),
    progress: stage.progress,
    statusLabel: stage.status,
    blockerReasonCode: resolveBlockerReasonCode(
      stage.blocker_status,
      stage.blocker_reason_code,
    ),
  };
}

export function translateManagerStageNote(
  note: ManagerApiStageNote,
): StageNoteModel {
  return {
    id: note.id,
    author: note.user_name,
    note: note.text,
    createdAtValue: note.created_at,
    createdLabel: formatDate(note.created_at),
  };
}

export function translateManagerStageFile(
  file: ManagerApiStageFile,
): RfqFileModel {
  return {
    id: file.id,
    label: file.filename,
    type: file.type,
    uploadedAtValue: file.uploaded_at,
    uploadedLabel: formatDate(file.uploaded_at),
    uploadedBy: file.uploaded_by,
    downloadUrl: resolveDownloadUrl(file.download_url),
    storageReference: file.storage_reference ?? undefined,
  };
}

function normalizeSubtaskState(
  status: string,
): RfqSubtaskModel["state"] {
  switch (status.trim().toLowerCase()) {
    case "done":
      return "done";
    case "in progress":
      return "in_progress";
    default:
      return "open";
  }
}

export function translateManagerSubtask(
  subtask: ManagerApiStageSubtask,
): RfqSubtaskModel {
  return {
    id: subtask.id,
    label: subtask.name,
    owner: subtask.assigned_to ?? "Unassigned",
    dueDateValue: subtask.due_date ?? undefined,
    dueLabel: subtask.due_date ? formatDate(subtask.due_date) : "Pending",
    state: normalizeSubtaskState(subtask.status),
    progress: subtask.progress,
  };
}

export function translateManagerStageDetailCollections(
  stage: ManagerApiStageDetail | null,
) {
  return {
    files: stage ? stage.files.map(translateManagerStageFile) : [],
    notes: stage ? stage.notes.map(translateManagerStageNote) : [],
    subtasks: stage ? stage.subtasks.map(translateManagerSubtask) : [],
  };
}

export function translateManagerStageWorkspace(
  stage: ManagerApiStageDetail,
): StageWorkspaceModel {
  const mandatoryFields = (stage.mandatory_fields ?? "")
    .split(",")
    .map((field) => field.trim())
    .filter(Boolean);
  const lifecycleEvents = parseLifecycleHistoryEvents(
    stage.captured_data?.workflow_history_events,
  );

  const capturedData = Object.entries(stage.captured_data ?? {}).reduce<Record<string, string>>(
    (accumulator, [key, value]) => {
      if (isLifecycleHistorySupportField(key)) {
        return accumulator;
      }

      if (isControlledStageDecisionField(key)) {
        accumulator[key] = normalizeControlledStageDecisionValue(
          key,
          typeof value === "boolean" || typeof value === "string"
            ? value
            : String(value ?? ""),
        );
        return accumulator;
      }

      if (isTerminalOutcomeField(key)) {
        accumulator[key] = normalizeTerminalOutcomeValue(
          typeof value === "string" ? value : String(value ?? ""),
        );
        return accumulator;
      }

      if (isLostReasonCodeField(key)) {
        accumulator[key] = normalizeLostReasonCode(
          typeof value === "string" ? value : String(value ?? ""),
        );
        return accumulator;
      }

      accumulator[key] = typeof value === "string" ? value : JSON.stringify(value);
      return accumulator;
    },
    {},
  );

  mandatoryFields.forEach((field) => {
    if (!(field in capturedData)) {
      capturedData[field] = "";
    }
  });

  return {
    id: stage.id,
    label: stage.name,
    order: stage.order,
    summary: stage.assigned_team ? `Assigned team: ${stage.assigned_team}` : undefined,
    assignedTeam: stage.assigned_team ?? undefined,
    state: resolveStageProgressState(stage.status, stage.blocker_status),
    progress: stage.progress,
    statusLabel: stage.status,
    blockerStatus: resolveBlockerStatus(stage.blocker_status),
    blockerReasonCode: resolveBlockerReasonCode(
      stage.blocker_status,
      stage.blocker_reason_code,
    ),
    capturedData,
    mandatoryFields,
    lifecycleEvents,
    plannedStartValue: stage.planned_start ?? undefined,
    plannedStartLabel: stage.planned_start ? formatDate(stage.planned_start) : undefined,
    plannedEndValue: stage.planned_end ?? undefined,
    plannedEndLabel: stage.planned_end ? formatDate(stage.planned_end) : undefined,
    actualStartValue: stage.actual_start ?? undefined,
    actualStartLabel: stage.actual_start ? formatDate(stage.actual_start) : undefined,
    actualEndValue: stage.actual_end ?? undefined,
    actualEndLabel: stage.actual_end ? formatDate(stage.actual_end) : undefined,
  };
}

export function translateStageUpdateInput(
  input: StageUpdateInput,
): Record<string, unknown> {
  const captured_data = input.capturedData
    ? Object.entries(input.capturedData).reduce<Record<string, unknown>>(
        (accumulator, [key, value]) => {
          if (isControlledStageDecisionField(key)) {
            const normalizedDecision = normalizeControlledStageDecisionValue(
              key,
              value,
            );
            if (normalizedDecision) {
              accumulator[key] = normalizedDecision;
            }
            return accumulator;
          }

          if (isTerminalOutcomeField(key)) {
            const normalizedOutcome = normalizeTerminalOutcomeValue(value);
            if (normalizedOutcome) {
              accumulator[key] = normalizedOutcome;
            }
            return accumulator;
          }

          if (isLostReasonCodeField(key)) {
            const normalizedLostReason = normalizeLostReasonCode(value);
            if (normalizedLostReason) {
              accumulator[key] = normalizedLostReason;
            }
            return accumulator;
          }

          const trimmed = value.trim();

          if (!trimmed) {
            return accumulator;
          }

          if (trimmed === "true") {
            accumulator[key] = true;
            return accumulator;
          }

          if (trimmed === "false") {
            accumulator[key] = false;
            return accumulator;
          }

          if (!Number.isNaN(Number(trimmed)) && trimmed !== "") {
            accumulator[key] = Number(trimmed);
            return accumulator;
          }

          try {
            accumulator[key] = JSON.parse(trimmed);
            return accumulator;
          } catch {
            accumulator[key] = trimmed;
            return accumulator;
          }
        },
        {},
      )
    : undefined;

  const hasBlockerStatus = Object.prototype.hasOwnProperty.call(
    input,
    "blockerStatus",
  );
  const hasBlockerReasonCode = Object.prototype.hasOwnProperty.call(
    input,
    "blockerReasonCode",
  );
  const blockerStatus = input.blockerStatus;
  const blockerReasonCode = blockerStatus
    ? input.blockerReasonCode?.trim() || null
    : null;

  return {
    captured_data,
    blocker_status: hasBlockerStatus ? blockerStatus ?? null : undefined,
    blocker_reason_code:
      hasBlockerStatus || hasBlockerReasonCode ? blockerReasonCode : undefined,
  };
}
