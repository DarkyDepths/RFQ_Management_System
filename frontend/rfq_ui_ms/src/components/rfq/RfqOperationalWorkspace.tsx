"use client";

import { useEffect, useState } from "react";
import {
  ArrowRight,
  CircleSlash,
  BellRing,
  Download,
  Plus,
  RefreshCw,
  Save,
  Send,
  Trash2,
  Upload,
} from "lucide-react";

import { ReminderDetailDialog } from "@/components/reminders/ReminderDetailDialog";
import type { RolePermissions } from "@/config/role-permissions";
import {
  DEFAULT_INDUSTRY_OPTION,
  OTHER_INDUSTRY_OPTION,
  industryOptions,
  resolveIndustrySelection,
  resolveIndustryValue,
  type IndustryOption,
} from "@/config/industry-options";
import { createReminder, resolveReminder } from "@/connectors/manager/reminders";
import { getWorkflow } from "@/connectors/manager/workflows";
import {
  addStageNote,
  advanceStage,
  createSubtask,
  deleteStageFile,
  deleteSubtask,
  getStageDetail,
  updateStage,
  updateSubtask,
  uploadStageFile,
} from "@/connectors/manager/stages";
import { cancelRfqRecord, updateRfqRecord } from "@/connectors/manager/rfqs";
import { useRfqReminders } from "@/hooks/use-rfq-reminders";
import { useStageWorkspace } from "@/hooks/use-stage-workspace";
import type {
  ReminderCreateInput,
  ReminderModel,
  RfqDetailModel,
  RfqFileModel,
  StageNoteModel,
  RfqSubtaskModel,
  SubtaskCreateInput,
  SubtaskUpdateInput,
  UpdateRfqInput,
} from "@/models/manager/rfq";
import type { StageUpdateInput } from "@/models/manager/stage";
import type { WorkflowModel } from "@/models/manager/workflow";
import type { AppRole } from "@/models/ui/role";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import { UploadZone } from "@/components/common/UploadZone";
import { getRoleActorProfile } from "@/lib/manager-actor";
import { getRfqBusinessIdentity } from "@/lib/rfq-display";
import { getRfqStatusMeta } from "@/lib/rfq-status-display";
import {
  buildWorkflowDeadlineTooNarrowMessage,
  formatWorkflowDeadlineIso,
  getLocalDateIsoString,
  getMinimumWorkflowFeasibleDeadlineIso,
} from "@/utils/workflow-deadline";
import {
  AUTO_BLOCKER_SOURCE_FIELD_KEY,
  getAutoBlockingDecisionSource,
  getCapturedFieldLabel,
  getControlledStageDecisionOptions,
  getControlledStageDecisionPlaceholder,
  getControlledStageDecisionValidationMessage,
  getNegativeDecisionBlockerReasonMessage,
  GO_NO_GO_FIELD_KEY,
  GO_NO_GO_VALUE_NO_GO,
  isAutoBlockerSupportField,
  isControlledStageDecisionField,
  isNegativeAutoBlockingDecision,
  YES_NO_VALUE_YES,
} from "@/utils/go-no-go";
import {
  APPROVAL_SIGNATURE_FIELD_KEY,
  APPROVAL_SIGNATURE_VALIDATION_MESSAGE,
  CURRENCY_OPTIONS,
  DEFAULT_CURRENCY_CODE,
  ESTIMATION_COMPLETED_FIELD_KEY,
  getApprovalSignatureHelpText,
  getApprovalSignaturePlaceholder,
  getCommercialFieldAmountKey,
  getCommercialFieldAmountPlaceholder,
  getCommercialFieldAmountValue,
  getCommercialFieldCurrencyKey,
  getCommercialFieldCurrencyValue,
  getCommercialFieldHelpText,
  getCommercialFieldNumericValidationError,
  getManagedStageSupportFieldOwnerLabel,
  isApprovalSignatureField,
  isCommercialFieldSatisfied,
  isCommercialStageField,
  isManagedStageSupportField,
} from "@/utils/commercial-fields";
import {
  buildCapturedData,
  buildCapturedFieldState,
  createEmptyCapturedFieldEntry,
  hasVisibleCapturedFieldEntries,
  type CapturedFieldEntry,
} from "@/utils/captured-data";
import {
  buildLifecycleHistoryCapturedEntries,
} from "@/utils/lifecycle-history";
import {
  getReminderDueDateHint,
  getReminderDueDateValidationMessage,
  getReminderScopeLabel,
  getReminderTypeLabel,
  resolveReminderDateWindow,
  sortRemindersForDisplay,
} from "@/utils/reminder";
import {
  formatCommercialAmountWithCurrency,
  formatDate,
  formatDateTime,
} from "@/utils/format";
import {
  canDeleteStageFile,
  canReadEscalationState,
  canReadOperationalWorkspace,
  canManageSubtasks as canManageScopedSubtasks,
  canUploadStageFiles,
} from "@/lib/rfq-access";
import { isTerminalRfqStatus } from "@/utils/status";
import {
  getSubtaskCreateValidationMessage,
  getSubtaskDueDateValidationMessage,
  getSubtaskProgressValidationMessage,
  normalizeSubtaskDraftState,
  resolveSubtaskStageWindow,
} from "@/utils/subtask";
import {
  getLostReasonHelpText,
  getLostReasonLabel,
  getTerminalOutcomeHelpText,
  getTerminalOutcomeLabel,
  getTerminalOutcomeManagedFieldOwnerLabel,
  isLostReasonCodeField,
  isTerminalOutcomeField,
  isTerminalOutcomeSupportField,
  LOST_REASON_CODE_FIELD_KEY,
  LOST_REASON_OPTIONS,
  LOST_REASON_OTHER_DETAIL_FIELD_KEY,
  LOST_REASON_OTHER_REQUIRED_MESSAGE,
  LOST_REASON_OTHER_VALUE,
  LOST_REASON_REQUIRED_MESSAGE,
  normalizeLostReasonCode,
  normalizeTerminalOutcomeValue,
  TERMINAL_OUTCOME_AWARDED,
  TERMINAL_OUTCOME_FIELD_KEY,
  TERMINAL_OUTCOME_LOST,
  TERMINAL_OUTCOME_OPTIONS,
  TERMINAL_OUTCOME_VALIDATION_MESSAGE,
} from "@/utils/terminal-outcome";
import {
  translateManagerStageDetailCollections,
  translateManagerStageWorkspace,
} from "@/translators/manager/stages";

type SubtaskDraft = {
  assignedTo: string;
  dueDate: string;
  name: string;
  progress: string;
  status: "Open" | "In progress" | "Done";
};

const selectClassName =
  "flex h-11 w-full rounded-xl border border-input bg-card px-3 py-2 text-sm text-foreground ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:border-transparent disabled:cursor-not-allowed disabled:opacity-50";

const fileTypeOptions = [
  "Client RFQ",
  "Design report",
  "BOQ / BOM",
  "Estimation Workbook",
  "Other",
];

const reminderStatusTone: Record<
  string,
  "amber" | "emerald" | "pending" | "rose" | "steel"
> = {
  open: "pending",
  overdue: "rose",
  resolved: "emerald",
  sent: "steel",
};

function getErrorMessage(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function mapSubtaskStateToManagerStatus(
  state: RfqSubtaskModel["state"],
): "Open" | "In progress" | "Done" {
  switch (state) {
    case "done":
      return "Done";
    case "in_progress":
      return "In progress";
    default:
      return "Open";
  }
}

function formatCapturedFieldLabel(key: string) {
  return getCapturedFieldLabel(key);
}

function truncateStageNotePreview(note: string, maxLength = 150) {
  const trimmed = note.trim();
  if (trimmed.length <= maxLength) {
    return trimmed;
  }

  return `${trimmed.slice(0, maxLength).trimEnd()}…`;
}

function upsertCapturedFieldEntry(
  entries: CapturedFieldEntry[],
  key: string,
  value: string,
) {
  let updated = false;
  const next = entries.map((entry) => {
    if (entry.key !== key) {
      return entry;
    }

    updated = true;
    return {
      ...entry,
      value,
    };
  });

  if (updated) {
    return next;
  }

  return [
    ...next,
    {
      id: key.trim() ? `captured:${key.trim()}` : createEmptyCapturedFieldEntry().id,
      key,
      value,
    },
  ];
}

function removeCapturedFieldEntry(entries: CapturedFieldEntry[], key: string) {
  return entries.filter((entry) => entry.key !== key);
}

function getDefaultHistoryStageId(rfq: RfqDetailModel) {
  const currentStage = rfq.stageHistory.find((stage) => stage.id === rfq.currentStageId);
  if (currentStage?.id) {
    return currentStage.id;
  }

  const lastInspectableStage = [...rfq.stageHistory]
    .reverse()
    .find((stage) => stage.state !== "upcoming" && stage.state !== "skipped");
  if (lastInspectableStage?.id) {
    return lastInspectableStage.id;
  }

  const firstSkippedStage = rfq.stageHistory.find((stage) => stage.state === "skipped");
  if (firstSkippedStage?.id) {
    return firstSkippedStage.id;
  }

  return lastInspectableStage?.id ?? rfq.stageHistory[0]?.id ?? null;
}

function getHistoryStageBadgeVariant(state?: string) {
  switch (state) {
    case "blocked":
      return "amber" as const;
    case "skipped":
      return "rose" as const;
    case "completed":
      return "emerald" as const;
    case "active":
      return "steel" as const;
    default:
      return "pending" as const;
  }
}

export function RfqOperationalWorkspace({
  permissions,
  rfq,
  role,
  onRefreshRfq,
}: {
  permissions: RolePermissions;
  rfq: RfqDetailModel;
  role: AppRole;
  onRefreshRfq: () => void;
}) {
  const stageWorkspace = useStageWorkspace(rfq.id, rfq.currentStageId);
  const reminders = useRfqReminders(rfq.id);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [selectedIndustryOption, setSelectedIndustryOption] =
    useState<IndustryOption>(DEFAULT_INDUSTRY_OPTION);
  const [customIndustry, setCustomIndustry] = useState("");
  const [noteText, setNoteText] = useState("");
  const [fileType, setFileType] = useState("Client RFQ");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [capturedFields, setCapturedFields] = useState<CapturedFieldEntry[]>([]);
  const [showAdditionalCapturedData, setShowAdditionalCapturedData] = useState(false);
  const [stageForm, setStageForm] = useState({
    blockerReasonCode: "",
    blockerStatus: "" as "" | "Blocked" | "Resolved",
  });
  const [rfqForm, setRfqForm] = useState({
    client: "",
    deadline: "",
    description: "",
    outcomeReason: "",
    owner: "",
    priority: "normal" as "normal" | "critical",
    title: "",
  });
  const [rfqWorkflow, setRfqWorkflow] = useState<WorkflowModel | null>(null);
  const [newSubtask, setNewSubtask] = useState({
    assignedTo: "",
    dueDate: "",
    name: "",
  });
  const [subtaskDrafts, setSubtaskDrafts] = useState<Record<string, SubtaskDraft>>({});
  const [reminderForm, setReminderForm] = useState({
    assignedTo: "",
    dueDate: "",
    message: "",
    scope: "rfq" as "rfq" | "stage",
    type: "internal" as "internal" | "external",
  });
  const [selectedReminder, setSelectedReminder] = useState<ReminderModel | null>(null);
  const [selectedStageNote, setSelectedStageNote] = useState<StageNoteModel | null>(null);
  const [isNoGoDialogOpen, setNoGoDialogOpen] = useState(false);
  const [noGoCancellationReason, setNoGoCancellationReason] = useState("");
  const [noGoDialogError, setNoGoDialogError] = useState("");
  const [isAdvanceStageDialogOpen, setAdvanceStageDialogOpen] = useState(false);
  const [isCancelRfqDialogOpen, setCancelRfqDialogOpen] = useState(false);
  const [cancelRfqReason, setCancelRfqReason] = useState("");
  const [cancelRfqDialogError, setCancelRfqDialogError] = useState("");
  const [selectedHistoryStageId, setSelectedHistoryStageId] = useState<string | null>(null);
  const [isHistoryDetailDialogOpen, setHistoryDetailDialogOpen] = useState(false);
  const [historyStageLoading, setHistoryStageLoading] = useState(false);
  const [historyStageError, setHistoryStageError] = useState("");
  const [historyStageWorkspace, setHistoryStageWorkspace] = useState<ReturnType<typeof translateManagerStageWorkspace> | null>(null);
  const [historyStageCollections, setHistoryStageCollections] = useState<ReturnType<typeof translateManagerStageDetailCollections>>({
    files: [],
    notes: [],
    subtasks: [],
  });

  useEffect(() => {
    const industrySelection = resolveIndustrySelection(
      rfq.industry,
      DEFAULT_INDUSTRY_OPTION,
    );

    setRfqForm({
      client: rfq.client,
      deadline: rfq.dueDateValue.slice(0, 10),
      description: rfq.description ?? "",
      outcomeReason: rfq.outcomeReason ?? "",
      owner: rfq.owner,
      priority: rfq.priority === "critical" ? "critical" : "normal",
      title: rfq.title,
    });
    setSelectedIndustryOption(industrySelection.selectedOption);
    setCustomIndustry(industrySelection.customValue);
    setSubtaskDrafts(
      rfq.subtasks.reduce<Record<string, SubtaskDraft>>((accumulator, task) => {
        accumulator[task.id] = {
          assignedTo: task.owner === "Unassigned" ? "" : task.owner,
          dueDate: task.dueDateValue?.slice(0, 10) ?? "",
          name: task.label,
          progress: typeof task.progress === "number" ? `${task.progress}` : "0",
          status: mapSubtaskStateToManagerStatus(task.state),
        };
        return accumulator;
      }, {}),
    );
  }, [rfq]);

  useEffect(() => {
    if (!stageWorkspace.workspace) {
      setCapturedFields([]);
      setShowAdditionalCapturedData(false);
      setStageForm({
        blockerReasonCode: "",
        blockerStatus: "",
      });
      return;
    }

    const nextCapturedFieldState = buildCapturedFieldState(
      stageWorkspace.workspace.capturedData,
      stageWorkspace.workspace.mandatoryFields,
    );

    setCapturedFields(nextCapturedFieldState.entries);
    setShowAdditionalCapturedData(nextCapturedFieldState.showAdditionalSection);
    setStageForm({
      blockerReasonCode: stageWorkspace.workspace.blockerReasonCode ?? "",
      blockerStatus: stageWorkspace.workspace.blockerStatus ?? "",
    });
  }, [stageWorkspace.workspace]);

  useEffect(() => {
    setSelectedStageNote(null);
    setSelectedReminder(null);
  }, [rfq.id, rfq.currentStageId]);

  useEffect(() => {
    setSelectedHistoryStageId((current) => {
      if (current && rfq.stageHistory.some((stage) => stage.id === current)) {
        return current;
      }

      return getDefaultHistoryStageId(rfq);
    });
  }, [rfq]);

  useEffect(() => {
    setHistoryDetailDialogOpen(false);
  }, [rfq.id, selectedHistoryStageId]);

  useEffect(() => {
    let active = true;

    if (!selectedHistoryStageId) {
      setHistoryStageLoading(false);
      setHistoryStageError("");
      setHistoryStageWorkspace(null);
      setHistoryStageCollections({ files: [], notes: [], subtasks: [] });
      return () => {
        active = false;
      };
    }

    setHistoryStageLoading(true);
    setHistoryStageError("");

    async function loadHistoryStage() {
      try {
        const detail = await getStageDetail(rfq.id, selectedHistoryStageId);

        if (!active) {
          return;
        }

        if (!detail) {
          setHistoryStageWorkspace(null);
          setHistoryStageCollections({ files: [], notes: [], subtasks: [] });
          setHistoryStageError("Stage history detail is not available.");
          setHistoryStageLoading(false);
          return;
        }

        setHistoryStageWorkspace(translateManagerStageWorkspace(detail));
        setHistoryStageCollections(translateManagerStageDetailCollections(detail));
        setHistoryStageLoading(false);
      } catch (historyError) {
        if (!active) {
          return;
        }

        setHistoryStageWorkspace(null);
        setHistoryStageCollections({ files: [], notes: [], subtasks: [] });
        setHistoryStageError(
          getErrorMessage(historyError, "Stage history detail could not be loaded."),
        );
        setHistoryStageLoading(false);
      }
    }

    void loadHistoryStage();

    return () => {
      active = false;
    };
  }, [rfq.id, rfq.updatedAtValue, selectedHistoryStageId]);

  useEffect(() => {
    let active = true;
    const workflowId = rfq.workflowId;

    if (!workflowId) {
      setRfqWorkflow(null);
      return () => {
        active = false;
      };
    }

    setRfqWorkflow(null);

    async function loadWorkflow() {
      if (!workflowId) {
        return;
      }

      try {
        const workflow = await getWorkflow(workflowId);

        if (!active) {
          return;
        }

        setRfqWorkflow(workflow);
      } catch {
        if (!active) {
          return;
        }

        setRfqWorkflow(null);
      }
    }

    void loadWorkflow();

    return () => {
      active = false;
    };
  }, [rfq.workflowId]);

  const currentStageId = rfq.currentStageId ?? undefined;
  const actorProfile = getRoleActorProfile(role);
  const actorName = actorProfile.userName;
  const actorTeam = actorProfile.team;
  const actorUserId = actorProfile.userId;
  const canReadWorkspace = canReadOperationalWorkspace(role, permissions, rfq, actorName);
  const canManageWorkspace = permissions.canManageStageWorkspace && canReadWorkspace;
  const canManageSubtasks = canManageScopedSubtasks(role, permissions, rfq, actorName);
  const canManageReminders = permissions.canManageReminders && canReadWorkspace;
  const canReadReminderState = canReadEscalationState(role, permissions, rfq, actorName);
  const canEditRfq = permissions.canEditCoreRfq;
  const isTerminalRfq = isTerminalRfqStatus(rfq.status);
  const canEditLifecycleControls = canEditRfq && !isTerminalRfq;
  const canUploadFiles = canUploadStageFiles(role, permissions, rfq, actorName);
  const workspaceReadOnly = canReadWorkspace && !canManageWorkspace;
  const rfqBusinessIdentity = getRfqBusinessIdentity(rfq, "this RFQ");
  const canCancelRfq =
    permissions.canEditCoreRfq &&
    rfq.status !== "cancelled" &&
    rfq.status !== "awarded" &&
    rfq.status !== "lost";
  const capturedData = buildCapturedData(capturedFields);
  const todayIso = getLocalDateIsoString();
  const minimumFeasibleRfqDeadlineIso =
    getMinimumWorkflowFeasibleDeadlineIso(rfqWorkflow);
  const rfqDeadlineTooNarrow =
    minimumFeasibleRfqDeadlineIso !== null &&
    rfqForm.deadline < minimumFeasibleRfqDeadlineIso;
  const mandatoryFieldKeys = stageWorkspace.workspace?.mandatoryFields ?? [];
  const mandatoryFieldSet = new Set(mandatoryFieldKeys);
  const missingMandatoryFields = mandatoryFieldKeys.filter((fieldKey) => {
    if (isCommercialStageField(fieldKey)) {
      return !isCommercialFieldSatisfied(capturedData, fieldKey);
    }

    if (isApprovalSignatureField(fieldKey)) {
      return !capturedData[fieldKey]?.trim();
    }

    return !capturedData[fieldKey]?.trim();
  });
  const controlledDecisionValidationMessage =
    getControlledStageDecisionValidationMessage(missingMandatoryFields);
  const commercialFieldValidationMessage = mandatoryFieldKeys.reduce<string | null>(
    (message, fieldKey) => {
      if (message || !isCommercialStageField(fieldKey)) {
        return message;
      }

      return getCommercialFieldNumericValidationError(capturedData, fieldKey);
    },
    null,
  );
  const approvalSignatureValidationMessage = missingMandatoryFields.includes(
    APPROVAL_SIGNATURE_FIELD_KEY,
  )
    ? APPROVAL_SIGNATURE_VALIDATION_MESSAGE
    : null;
  const autoBlockingDecisionField =
    mandatoryFieldKeys.find((fieldKey) =>
      isNegativeAutoBlockingDecision(fieldKey, capturedData[fieldKey]),
    ) ?? null;
  const autoBlockingDecisionSource = getAutoBlockingDecisionSource(capturedData);
  const autoBlockingDecisionLabel = autoBlockingDecisionField
    ? formatCapturedFieldLabel(autoBlockingDecisionField)
    : null;
  const decisionDrivenBlockerReasonMessage =
    autoBlockingDecisionField && !stageForm.blockerReasonCode.trim()
      ? getNegativeDecisionBlockerReasonMessage(autoBlockingDecisionField)
      : null;
  const effectiveBlockerStatus = autoBlockingDecisionField
    ? "Blocked"
    : stageForm.blockerStatus;
  const mandatoryCapturedFields = mandatoryFieldKeys.map((fieldKey) => {
    const matchingEntry = capturedFields.find((entry) => entry.key === fieldKey);
    return {
      key: fieldKey,
      value: matchingEntry?.value ?? "",
    };
  });
  const additionalCapturedFields = capturedFields.filter(({ key }) => {
      const trimmedKey = key.trim();
      return (
        (!trimmedKey || !mandatoryFieldSet.has(trimmedKey)) &&
        !isAutoBlockerSupportField(trimmedKey) &&
        !isManagedStageSupportField(trimmedKey) &&
        !isTerminalOutcomeSupportField(trimmedKey)
      );
    });
  const shouldShowAdditionalCapturedData =
    showAdditionalCapturedData ||
    additionalCapturedFields.length > 0 ||
    hasVisibleCapturedFieldEntries(additionalCapturedFields);
  const currentStageLabel =
    stageWorkspace.workspace?.label ?? rfq.stageLabel ?? "Current Stage";
  const hasStageLinkedReminderScope = Boolean(currentStageId);
  const sortedRfqReminders = sortRemindersForDisplay(reminders.reminders);
  const reminderDateWindow = resolveReminderDateWindow({
    actualEndValue: stageWorkspace.workspace?.actualEndValue,
    actualStartValue: stageWorkspace.workspace?.actualStartValue,
    plannedEndValue: stageWorkspace.workspace?.plannedEndValue,
    plannedStartValue: stageWorkspace.workspace?.plannedStartValue,
    rfqDeadlineValue: rfq.dueDateValue.slice(0, 10),
    scope: reminderForm.scope,
    todayValue: todayIso,
  });
  const reminderDueDateValidationMessage = getReminderDueDateValidationMessage({
    actualEndValue: stageWorkspace.workspace?.actualEndValue,
    actualStartValue: stageWorkspace.workspace?.actualStartValue,
    dueDate: reminderForm.dueDate,
    plannedEndValue: stageWorkspace.workspace?.plannedEndValue,
    plannedStartValue: stageWorkspace.workspace?.plannedStartValue,
    rfqDeadlineValue: rfq.dueDateValue.slice(0, 10),
    scope: reminderForm.scope,
    todayValue: todayIso,
  });
  const reminderDueDateHint = getReminderDueDateHint({
    actualEndValue: stageWorkspace.workspace?.actualEndValue,
    actualStartValue: stageWorkspace.workspace?.actualStartValue,
    plannedEndValue: stageWorkspace.workspace?.plannedEndValue,
    plannedStartValue: stageWorkspace.workspace?.plannedStartValue,
    rfqDeadlineValue: rfq.dueDateValue.slice(0, 10),
    scope: reminderForm.scope,
    todayValue: todayIso,
  });
  const nextStageSummary =
    stageWorkspace.workspace
      ? rfq.stageHistory.find((stage) => stage.order === stageWorkspace.workspace!.order + 1) ?? null
      : null;
  const nextStageLabel = nextStageSummary?.label ?? "the next workflow stage";
  const subtaskStageWindow = resolveSubtaskStageWindow(
    stageWorkspace.workspace?.plannedStartValue,
    stageWorkspace.workspace?.plannedEndValue,
    stageWorkspace.workspace?.actualStartValue,
    stageWorkspace.workspace?.actualEndValue,
  );
  const stageWindowStartValue = subtaskStageWindow.startValue;
  const stageWindowEndValue = subtaskStageWindow.endValue;
  const stageWindowStartLabel = stageWindowStartValue ? formatDate(stageWindowStartValue) : undefined;
  const stageWindowEndLabel = stageWindowEndValue ? formatDate(stageWindowEndValue) : undefined;
  const stageWindowHint =
    stageWindowStartLabel && stageWindowEndLabel
      ? subtaskStageWindow.mode === "actual"
        ? `Due date must stay within the actual stage window (${stageWindowStartLabel} -> ${stageWindowEndLabel}).`
        : subtaskStageWindow.mode === "shifted_actual"
          ? `Due date must stay within the shifted execution window (${stageWindowStartLabel} -> ${stageWindowEndLabel}).`
          : `Due date must stay within the current stage window (${stageWindowStartLabel} -> ${stageWindowEndLabel}).`
      : null;
  const newSubtaskDueDateError = getSubtaskDueDateValidationMessage(
    newSubtask.dueDate,
    stageWorkspace.workspace?.plannedStartValue,
    stageWorkspace.workspace?.plannedEndValue,
    stageWorkspace.workspace?.actualStartValue,
    stageWorkspace.workspace?.actualEndValue,
  );
  const newSubtaskCreateError = getSubtaskCreateValidationMessage(
    newSubtask.name,
    newSubtask.assignedTo,
    newSubtask.dueDate,
    stageWorkspace.workspace?.plannedStartValue,
    stageWorkspace.workspace?.plannedEndValue,
    stageWorkspace.workspace?.actualStartValue,
    stageWorkspace.workspace?.actualEndValue,
  );
  const selectedStageNoteDateTime = selectedStageNote?.createdAtValue
    ? formatDateTime(selectedStageNote.createdAtValue)
    : "Pending";
  const isTerminalOutcomeStage = Boolean(
    stageWorkspace.workspace &&
      rfq.stageHistory.length > 0 &&
      stageWorkspace.workspace.order === rfq.stageHistory.length,
  );
  const terminalOutcomeValue = normalizeTerminalOutcomeValue(
    capturedData[TERMINAL_OUTCOME_FIELD_KEY],
  );
  const lostReasonCodeValue = normalizeLostReasonCode(
    capturedData[LOST_REASON_CODE_FIELD_KEY],
  );
  const lostReasonOtherValue = capturedData[LOST_REASON_OTHER_DETAIL_FIELD_KEY] ?? "";
  const terminalOutcomeValidationMessage =
    isTerminalOutcomeStage && !terminalOutcomeValue
      ? TERMINAL_OUTCOME_VALIDATION_MESSAGE
      : null;
  const lostReasonValidationMessage =
    isTerminalOutcomeStage &&
    terminalOutcomeValue === TERMINAL_OUTCOME_LOST &&
    !lostReasonCodeValue
      ? LOST_REASON_REQUIRED_MESSAGE
      : null;
  const lostReasonOtherValidationMessage =
    isTerminalOutcomeStage &&
    terminalOutcomeValue === TERMINAL_OUTCOME_LOST &&
    lostReasonCodeValue === LOST_REASON_OTHER_VALUE &&
    !lostReasonOtherValue.trim()
      ? LOST_REASON_OTHER_REQUIRED_MESSAGE
      : null;
  const stageDecisionValidationMessage =
    terminalOutcomeValidationMessage ??
    lostReasonValidationMessage ??
    lostReasonOtherValidationMessage ??
    controlledDecisionValidationMessage;
  const selectedHistoryStageSummary =
    selectedHistoryStageId
      ? rfq.stageHistory.find((stage) => stage.id === selectedHistoryStageId) ?? null
      : null;
  const historyCapturedEntries = historyStageWorkspace
    ? buildLifecycleHistoryCapturedEntries(historyStageWorkspace.capturedData)
    : [];
  const historyLifecycleEvents = historyStageWorkspace?.lifecycleEvents ?? [];
  const recentHistoryEvents = [...historyLifecycleEvents].slice(-3).reverse();

  useEffect(() => {
    if (!hasStageLinkedReminderScope) {
      setReminderForm((current) =>
        current.scope === "stage" ? { ...current, scope: "rfq" } : current,
      );
    }
  }, [hasStageLinkedReminderScope]);

  if (!canReadWorkspace) {
    return (
      <div className="rounded-xl border border-border bg-muted/20 p-5 text-sm text-muted-foreground">
        Operational workspace access is not available for this RFQ under your current role scope.
      </div>
    );
  }

  const refreshOperational = () => {
    onRefreshRfq();
    stageWorkspace.refresh();
    reminders.refresh();
  };

  async function runAction<T>(key: string, task: () => Promise<T>, successMessage: string) {
    setBusyAction(key);
    setError("");
    setMessage("");

    try {
      const result = await task();
      refreshOperational();
      setMessage(successMessage);
      return result;
    } catch (actionError) {
      setError(getErrorMessage(actionError, "The manager action could not be completed."));
      return null;
    } finally {
      setBusyAction(null);
    }
  }

  const handleMandatoryCapturedFieldChange = (fieldKey: string, value: string) => {
    setError("");
    setCapturedFields((current) => {
      let next = upsertCapturedFieldEntry(current, fieldKey, value);

      if (isNegativeAutoBlockingDecision(fieldKey, value)) {
        next = upsertCapturedFieldEntry(next, AUTO_BLOCKER_SOURCE_FIELD_KEY, fieldKey);
      } else if (
        value === YES_NO_VALUE_YES &&
        autoBlockingDecisionSource === fieldKey
      ) {
        next = removeCapturedFieldEntry(next, AUTO_BLOCKER_SOURCE_FIELD_KEY);
      }

      return next;
    });

    if (isNegativeAutoBlockingDecision(fieldKey, value)) {
      setStageForm((current) => ({
        ...current,
        blockerStatus: "Blocked",
      }));
    } else if (
      value === YES_NO_VALUE_YES &&
      autoBlockingDecisionSource === fieldKey
    ) {
      setStageForm((current) => ({
        ...current,
        blockerReasonCode: "",
        blockerStatus: current.blockerStatus === "Blocked" ? "Resolved" : current.blockerStatus,
      }));
    }
  };

  const handleCommercialFieldChange = (
    fieldKey: string,
    nextAmountValue: string,
    nextCurrencyValue?: string,
  ) => {
    if (!isCommercialStageField(fieldKey)) {
      return;
    }

    const normalizedAmount = nextAmountValue.trim();
    const amountKey = getCommercialFieldAmountKey(fieldKey);
    const currencyKey = getCommercialFieldCurrencyKey(fieldKey);
    const resolvedCurrencyValue =
      nextCurrencyValue ??
      getCommercialFieldCurrencyValue(capturedData, fieldKey) ??
      DEFAULT_CURRENCY_CODE;

    setError("");
    setCapturedFields((current) => {
      let next = [...current];

      if (!normalizedAmount) {
        next = removeCapturedFieldEntry(next, fieldKey);
        if (amountKey !== fieldKey) {
          next = removeCapturedFieldEntry(next, amountKey);
        }
        if (currencyKey) {
          next = upsertCapturedFieldEntry(next, currencyKey, resolvedCurrencyValue);
        }
        return next;
      }

      if (fieldKey === ESTIMATION_COMPLETED_FIELD_KEY) {
        next = upsertCapturedFieldEntry(next, fieldKey, "true");
      } else {
        next = upsertCapturedFieldEntry(next, fieldKey, normalizedAmount);
      }

      if (amountKey !== fieldKey) {
        next = upsertCapturedFieldEntry(next, amountKey, normalizedAmount);
      }

      if (currencyKey) {
        next = upsertCapturedFieldEntry(next, currencyKey, resolvedCurrencyValue);
      }

      return next;
    });
  };

  const handleTerminalOutcomeChange = (value: string) => {
    setError("");
    setCapturedFields((current) => {
      let next = upsertCapturedFieldEntry(current, TERMINAL_OUTCOME_FIELD_KEY, value);

      if (value !== TERMINAL_OUTCOME_LOST) {
        next = removeCapturedFieldEntry(next, LOST_REASON_CODE_FIELD_KEY);
        next = removeCapturedFieldEntry(next, LOST_REASON_OTHER_DETAIL_FIELD_KEY);
      }

      return next;
    });
  };

  const handleLostReasonChange = (value: string) => {
    setError("");
    setCapturedFields((current) => {
      let next = upsertCapturedFieldEntry(current, LOST_REASON_CODE_FIELD_KEY, value);
      if (value !== LOST_REASON_OTHER_VALUE) {
        next = removeCapturedFieldEntry(next, LOST_REASON_OTHER_DETAIL_FIELD_KEY);
      }
      return next;
    });
  };

  const handleLostReasonOtherChange = (value: string) => {
    setError("");
    setCapturedFields((current) =>
      upsertCapturedFieldEntry(current, LOST_REASON_OTHER_DETAIL_FIELD_KEY, value),
    );
  };

  const handleAddAdditionalCapturedField = () => {
    setShowAdditionalCapturedData(true);
    setError("");
    setCapturedFields((current) => [...current, createEmptyCapturedFieldEntry()]);
  };

  const handleAdditionalCapturedFieldChange = (
    entryId: string,
    field: "key" | "value",
    nextValue: string,
  ) => {
    if (field === "key") {
      const trimmedKey = nextValue.trim();

      if (trimmedKey && mandatoryFieldSet.has(trimmedKey)) {
        setError(
          `${formatCapturedFieldLabel(trimmedKey)} is already defined by the workflow stage. Update it in the required fields section instead.`,
        );
        return;
      }

      if (trimmedKey && isAutoBlockerSupportField(trimmedKey)) {
        setError(
          "Workflow blocker handling already manages this field. Update the stage decision instead.",
        );
        return;
      }

      if (trimmedKey && isManagedStageSupportField(trimmedKey)) {
        setError(
          `${getManagedStageSupportFieldOwnerLabel(trimmedKey)} already manages this commercial field. Update it in the required fields section instead.`,
        );
        return;
      }

      if (trimmedKey && isTerminalOutcomeSupportField(trimmedKey)) {
        setError(
          `${getTerminalOutcomeManagedFieldOwnerLabel()} already manages this field. Update it in the terminal outcome section instead.`,
        );
        return;
      }
    }

    setError("");
    setCapturedFields((current) =>
      current.map((entry) =>
        entry.id === entryId
          ? {
              ...entry,
              [field]: nextValue,
            }
          : entry,
      ),
    );
  };

  const handleRemoveAdditionalCapturedField = (entryId: string) => {
    setCapturedFields((current) => {
      const next = current.filter((entry) => entry.id !== entryId);
      const remainingAdditionalFields = next.filter((entry) => {
        const trimmedKey = entry.key.trim();
        return (
          (!trimmedKey || !mandatoryFieldSet.has(trimmedKey)) &&
          !isAutoBlockerSupportField(trimmedKey) &&
          !isManagedStageSupportField(trimmedKey) &&
          !isTerminalOutcomeSupportField(trimmedKey)
        );
      });

      if (!hasVisibleCapturedFieldEntries(remainingAdditionalFields)) {
        setShowAdditionalCapturedData(false);
      }

      return next;
    });
  };

  const buildCurrentStageUpdateInput = (): StageUpdateInput => {
    return {
      blockerReasonCode: stageForm.blockerReasonCode || undefined,
      blockerStatus: effectiveBlockerStatus || undefined,
      capturedData,
    };
  };

  const openNoGoDialog = () => {
    setError("");
    setMessage("");
    setNoGoDialogError("");
    setNoGoCancellationReason(rfq.outcomeReason ?? "");
    setNoGoDialogOpen(true);
  };

  const closeNoGoDialog = () => {
    if (busyAction === "advance-stage") {
      return;
    }

    setNoGoDialogError("");
    setNoGoCancellationReason(rfq.outcomeReason ?? "");
    setNoGoDialogOpen(false);
  };

  const openAdvanceStageDialog = () => {
    setError("");
    setMessage("");
    setAdvanceStageDialogOpen(true);
  };

  const closeAdvanceStageDialog = () => {
    if (busyAction === "advance-stage") {
      return;
    }

    setAdvanceStageDialogOpen(false);
  };

  const openCancelRfqDialog = () => {
    if (!canCancelRfq) {
      return;
    }

    setError("");
    setMessage("");
    setCancelRfqDialogError("");
    setCancelRfqReason(rfq.outcomeReason ?? "");
    setCancelRfqDialogOpen(true);
  };

  const closeCancelRfqDialog = () => {
    if (busyAction === "cancel-rfq") {
      return;
    }

    setCancelRfqDialogError("");
    setCancelRfqReason(rfq.outcomeReason ?? "");
    setCancelRfqDialogOpen(false);
  };

  const openHistoryDetailDialog = () => {
    if (!historyStageWorkspace) {
      return;
    }

    setHistoryDetailDialogOpen(true);
  };

  const closeHistoryDetailDialog = () => {
    setHistoryDetailDialogOpen(false);
  };

  const openStageNoteDetail = (note: StageNoteModel) => {
    setSelectedStageNote(note);
  };

  const closeStageNoteDetail = () => {
    setSelectedStageNote(null);
  };

  const handleSaveStage = async () => {
    if (!currentStageId || !canManageWorkspace) {
      return;
    }

    if (commercialFieldValidationMessage) {
      setError(commercialFieldValidationMessage);
      setMessage("");
      return;
    }

    if (approvalSignatureValidationMessage) {
      setError(approvalSignatureValidationMessage);
      setMessage("");
      return;
    }

    if (stageDecisionValidationMessage) {
      setError(stageDecisionValidationMessage);
      setMessage("");
      return;
    }

    if (decisionDrivenBlockerReasonMessage) {
      setError(decisionDrivenBlockerReasonMessage);
      setMessage("");
      return;
    }

    await runAction(
      "save-stage",
      () => updateStage(rfq.id, currentStageId, buildCurrentStageUpdateInput(), { actorTeam }),
      "Current stage updated.",
    );
  };

  const handleAdvanceStage = async () => {
    if (!currentStageId || !permissions.canAdvanceStage) {
      return;
    }

    if (commercialFieldValidationMessage) {
      setError(commercialFieldValidationMessage);
      setMessage("");
      return;
    }

    if (approvalSignatureValidationMessage) {
      setError(approvalSignatureValidationMessage);
      setMessage("");
      return;
    }

    if (stageDecisionValidationMessage) {
      setError(stageDecisionValidationMessage);
      setMessage("");
      return;
    }

    if (autoBlockingDecisionField) {
      setError(
        `${autoBlockingDecisionLabel} is set to No, so this stage is blocked. Save or resolve the blocker before advancing.`,
      );
      setMessage("");
      return;
    }

    const goNoGoDecision = capturedData[GO_NO_GO_FIELD_KEY]?.trim();
    const isNoGoDecision = goNoGoDecision === GO_NO_GO_VALUE_NO_GO;

    if (isNoGoDecision) {
      openNoGoDialog();
      return;
    }

    if (isTerminalOutcomeStage) {
      const successMessage =
        terminalOutcomeValue === TERMINAL_OUTCOME_AWARDED
          ? "RFQ marked as Awarded. History is preserved."
          : "RFQ marked as Lost. History is preserved.";
      const response = await runAction(
        "advance-stage",
        async () => {
          if (canManageWorkspace) {
            await updateStage(rfq.id, currentStageId, buildCurrentStageUpdateInput(), {
              actorTeam,
            });
          }

          return advanceStage(
            rfq.id,
            currentStageId,
            {
              terminalOutcome: terminalOutcomeValue || undefined,
              lostReasonCode:
                terminalOutcomeValue === TERMINAL_OUTCOME_LOST
                  ? lostReasonCodeValue || undefined
                  : undefined,
            },
            { actorTeam },
          );
        },
        successMessage,
      );

      if (response) {
        onRefreshRfq();
      }
      return;
    }

    openAdvanceStageDialog();
  };

  const handleConfirmAdvanceStage = async () => {
    if (!currentStageId || !permissions.canAdvanceStage) {
      return;
    }

    const response = await runAction(
      "advance-stage",
      () => advanceStage(rfq.id, currentStageId, {}, { actorTeam }),
      "Stage advanced.",
    );

    if (response) {
      setAdvanceStageDialogOpen(false);
      onRefreshRfq();
    }
  };

  const handleAddNote = async () => {
    if (!currentStageId || !permissions.canManageStageNotes || !noteText.trim()) {
      return;
    }

    const response = await runAction(
      "add-note",
      () =>
        addStageNote(rfq.id, currentStageId, noteText.trim(), {
          actorTeam,
          actorUserId,
          actorUserName: actorName,
        }),
      "Stage note added.",
    );

    if (response) {
      setNoteText("");
    }
  };

  const handleUploadFile = async () => {
    if (!currentStageId || !canUploadFiles || !selectedFile) {
      return;
    }

    const response = await runAction(
      "upload-file",
      () => uploadStageFile(rfq.id, currentStageId, selectedFile, fileType, { actorTeam }),
      `File uploaded as ${fileType}.`,
    );

    if (response) {
      setSelectedFile(null);
      setFileType("Client RFQ");
    }
  };

  const handleDeleteFile = async (file: RfqFileModel) => {
    if (!canDeleteStageFile(role, permissions, rfq, file, actorName)) {
      return;
    }

    await runAction(
      `delete-file:${file.id}`,
      () => deleteStageFile(file.id),
      "File deleted.",
    );
  };

  const handleCreateSubtask = async () => {
    if (!currentStageId || !canManageSubtasks) {
      return;
    }

    if (newSubtaskCreateError) {
      setError(newSubtaskCreateError);
      setMessage("");
      return;
    }

    const input: SubtaskCreateInput = {
      assignedTo: newSubtask.assignedTo.trim(),
      dueDate: newSubtask.dueDate,
      name: newSubtask.name.trim(),
    };

    const response = await runAction(
      "create-subtask",
      () => createSubtask(rfq.id, currentStageId, input, { actorTeam }),
      "Subtask created.",
    );

    if (response !== null) {
      setNewSubtask({ assignedTo: "", dueDate: "", name: "" });
    }
  };

  const handleUpdateSubtask = async (subtaskId: string) => {
    if (!currentStageId || !canManageSubtasks) {
      return;
    }

    const draft = subtaskDrafts[subtaskId];
    if (!draft) {
      return;
    }

    const draftDueDateError = getSubtaskDueDateValidationMessage(
      draft.dueDate,
      stageWindowStartValue,
      stageWindowEndValue,
    );
    if (draftDueDateError) {
      setError(draftDueDateError);
      setMessage("");
      return;
    }

    const draftProgressError = getSubtaskProgressValidationMessage(
      draft.progress,
      rfq.subtasks.find((task) => task.id === subtaskId)?.progress,
    );
    if (draftProgressError) {
      setError(draftProgressError);
      setMessage("");
      return;
    }

    const progress = Number.parseInt(draft.progress, 10);
    if (!Number.isFinite(progress)) {
      setError("Enter a valid subtask progress between 0 and 100.");
      setMessage("");
      return;
    }

    const input: SubtaskUpdateInput = {
      assignedTo: draft.assignedTo || undefined,
      dueDate: draft.dueDate || undefined,
      name: draft.name,
      progress,
      status: draft.status,
    };

    await runAction(
      `update-subtask:${subtaskId}`,
      () => updateSubtask(rfq.id, currentStageId, subtaskId, input, { actorTeam }),
      "Subtask updated.",
    );
  };

  const handleDeleteSubtask = async (subtaskId: string) => {
    if (!currentStageId || !canManageSubtasks) {
      return;
    }

    await runAction(
      `delete-subtask:${subtaskId}`,
      () => deleteSubtask(rfq.id, currentStageId, subtaskId, { actorTeam }),
      "Subtask deleted.",
    );
  };

  const handleCreateReminder = async () => {
    if (
      !canManageReminders ||
      !reminderForm.message.trim() ||
      !reminderForm.dueDate ||
      reminderDueDateValidationMessage
    ) {
      return;
    }

    const input: ReminderCreateInput = {
      assignedTo: reminderForm.assignedTo || undefined,
      dueDate: reminderForm.dueDate,
      message: reminderForm.message.trim(),
      rfqId: rfq.id,
      rfqStageId: reminderForm.scope === "stage" ? currentStageId : undefined,
      type: reminderForm.type,
    };

    const response = await runAction("create-reminder", () => createReminder(input), "Reminder created.");

    if (response !== null) {
      setReminderForm({
        assignedTo: "",
        dueDate: "",
        message: "",
        scope: "rfq",
        type: "internal",
      });
    }
  };

  const handleResolveReminder = async (reminderId: string) => {
    await runAction(
      `resolve-reminder:${reminderId}`,
      () => resolveReminder(reminderId),
      "Reminder resolved.",
    );
  };

  const handleSaveRfq = async () => {
    if (isTerminalRfq) {
      setError("Terminal RFQs are read-only through standard lifecycle controls.");
      setMessage("");
      return;
    }

    if (!canEditLifecycleControls) {
      return;
    }

    const resolvedIndustry = resolveIndustryValue(
      selectedIndustryOption,
      customIndustry,
    );

    if (!resolvedIndustry) {
      setError("Select an industry or enter a custom industry value before saving the RFQ.");
      setMessage("");
      return;
    }

    const input: UpdateRfqInput = {};

    if (rfqForm.title !== rfq.title) {
      input.name = rfqForm.title;
    }

    if (rfqForm.client !== rfq.client) {
      input.client = rfqForm.client;
    }

    if (rfqForm.owner !== rfq.owner) {
      input.owner = rfqForm.owner;
    }

    if (rfqForm.deadline !== rfq.dueDateValue.slice(0, 10)) {
      if (rfqForm.deadline < todayIso) {
        setError("Deadline cannot be moved into the past.");
        setMessage("");
        return;
      }

      if (
        minimumFeasibleRfqDeadlineIso &&
        rfqForm.deadline < minimumFeasibleRfqDeadlineIso
      ) {
        setError(
          buildWorkflowDeadlineTooNarrowMessage(minimumFeasibleRfqDeadlineIso),
        );
        setMessage("");
        return;
      }

      input.deadline = rfqForm.deadline;
    }

    if (rfqForm.priority !== (rfq.priority === "critical" ? "critical" : "normal")) {
      input.priority = rfqForm.priority;
    }

    if (rfqForm.description !== (rfq.description ?? "")) {
      input.description = rfqForm.description;
    }

    if (resolvedIndustry !== (rfq.industry ?? "")) {
      input.industry = resolvedIndustry;
    }

    if (Object.keys(input).length === 0) {
      setError("");
      setMessage("No RFQ shell metadata changes to save.");
      return;
    }

    const response = await runAction("save-rfq", () => updateRfqRecord(rfq.id, input), "RFQ updated.");
    if (response) {
      onRefreshRfq();
    }
  };

  const handleConfirmNoGoCancellation = async () => {
    if (!currentStageId || !permissions.canAdvanceStage) {
      return;
    }

    if (controlledDecisionValidationMessage) {
      setNoGoDialogError(controlledDecisionValidationMessage);
      return;
    }

    const normalizedReason = noGoCancellationReason.trim();
    if (!normalizedReason) {
      setNoGoDialogError("Please enter a cancellation reason.");
      return;
    }

    setNoGoDialogError("");

    const response = await runAction(
      "advance-stage",
      async () => {
        if (canManageWorkspace) {
          await updateStage(rfq.id, currentStageId, buildCurrentStageUpdateInput(), {
            actorTeam,
          });
        }

        return cancelRfqRecord(rfq.id, {
          outcomeReason: normalizedReason,
        });
      },
      "RFQ cancelled from Go / No-Go. History is preserved.",
    );

    if (response) {
      setNoGoDialogError("");
      setNoGoCancellationReason("");
      setNoGoDialogOpen(false);
      onRefreshRfq();
    }
  };

  const handleCancelRfq = async () => {
    const normalizedReason = cancelRfqReason.trim();
    if (!normalizedReason) {
      setCancelRfqDialogError("Please enter a cancellation reason.");
      return;
    }

    const response = await runAction(
      "cancel-rfq",
      () =>
        cancelRfqRecord(rfq.id, {
          outcomeReason: normalizedReason,
        }),
      "RFQ cancelled. History is preserved; no hard delete was performed.",
    );

    if (response) {
      setCancelRfqDialogError("");
      setCancelRfqReason("");
      setCancelRfqDialogOpen(false);
      onRefreshRfq();
    }
  };

  return (
    <div className="space-y-5">
      {selectedStageNote ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6">
          <div
            aria-describedby="stage-note-dialog-description"
            aria-labelledby="stage-note-dialog-title"
            aria-modal="true"
            className="w-full max-w-2xl rounded-[1.75rem] border border-border bg-background p-6 shadow-2xl"
            role="dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-foreground" id="stage-note-dialog-title">
                  Stage note detail
                </h3>
                <p
                  className="mt-2 text-sm leading-relaxed text-muted-foreground"
                  id="stage-note-dialog-description"
                >
                  Review the full note text and its RFQ stage context here.
                </p>
              </div>
              <Badge variant="steel">Operational note</Badge>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  RFQ Code
                </div>
                <div className="mt-1 text-sm text-foreground">{rfq.rfqCode ?? rfq.id}</div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Stage
                </div>
                <div className="mt-1 text-sm text-foreground">{currentStageLabel}</div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Author
                </div>
                <div className="mt-1 text-sm text-foreground">{selectedStageNote.author}</div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Written
                </div>
                <div className="mt-1 text-sm text-foreground">{selectedStageNoteDateTime}</div>
              </div>
            </div>

            <div className="mt-5 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Note
              </div>
              <div className="mt-3 max-h-[45vh] overflow-y-auto whitespace-pre-wrap text-sm leading-relaxed text-foreground">
                {selectedStageNote.note}
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <Button onClick={closeStageNoteDetail} type="button" variant="secondary">
                Close
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      <ReminderDetailDialog
        onClose={() => setSelectedReminder(null)}
        reminder={selectedReminder}
      />

      {isHistoryDetailDialogOpen && historyStageWorkspace ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6"
          onClick={closeHistoryDetailDialog}
        >
          <div
            aria-describedby="history-detail-description"
            aria-labelledby="history-detail-title"
            aria-modal="true"
            className="max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-[1.75rem] border border-border bg-background p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h3 className="text-lg font-semibold text-foreground" id="history-detail-title">
                  View Full Stage Detail
                </h3>
                <p
                  className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground"
                  id="history-detail-description"
                >
                  Review the full stage-owned record for {historyStageWorkspace.label}, including
                  blocker events, captured data, notes, files, and subtasks that remained attached
                  to this stage.
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Badge variant={getHistoryStageBadgeVariant(historyStageWorkspace.state)}>
                  {historyStageWorkspace.statusLabel ?? selectedHistoryStageSummary?.state ?? "Recorded"}
                </Badge>
                {historyStageWorkspace.blockerStatus ? (
                  <Badge variant="amber">{historyStageWorkspace.blockerStatus}</Badge>
                ) : null}
              </div>
            </div>

            <div className="mt-5 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Actual Start
                </div>
                <div className="mt-1 text-sm font-semibold text-foreground">
                  {historyStageWorkspace.actualStartLabel ?? "Not started"}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Actual End
                </div>
                <div className="mt-1 text-sm font-semibold text-foreground">
                  {historyStageWorkspace.actualEndLabel ?? "Not finished"}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Assigned Team
                </div>
                <div className="mt-1 text-sm text-foreground">
                  {historyStageWorkspace.assignedTeam ?? "Unassigned"}
                </div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Planned Window
                </div>
                <div className="mt-1 text-sm text-foreground">
                  {historyStageWorkspace.plannedStartLabel && historyStageWorkspace.plannedEndLabel
                    ? `${historyStageWorkspace.plannedStartLabel} -> ${historyStageWorkspace.plannedEndLabel}`
                    : "Not scheduled"}
                </div>
              </div>
            </div>

            <div className="mt-6 grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-foreground">
                      Recent Lifecycle Events
                    </div>
                    <Badge variant="steel">{historyLifecycleEvents.length} event(s)</Badge>
                  </div>
                  {historyLifecycleEvents.length === 0 ? (
                    <p className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                      No blocker or decision events were recorded for this stage.
                    </p>
                  ) : (
                    <div className="space-y-3">
                      {[...historyLifecycleEvents].reverse().map((event) => (
                        <div key={event.id} className="stat-cell">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div>
                              <div className="text-sm font-medium text-foreground">
                                {event.title}
                              </div>
                              <div className="mt-1 text-xs text-muted-foreground">
                                {event.summary}
                              </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2">
                              <Badge variant={event.tone}>{event.timestampLabel}</Badge>
                              {event.source ? (
                                <Badge variant="steel">
                                  {event.source === "automatic" ? "Automatic" : "Manual"}
                                </Badge>
                              ) : null}
                            </div>
                          </div>
                          {event.actorName ? (
                            <div className="mt-2 text-xs text-muted-foreground">
                              Recorded by {event.actorName}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-foreground">Captured Data</div>
                    <Badge variant="steel">{historyCapturedEntries.length} item(s)</Badge>
                  </div>
                  {historyCapturedEntries.length === 0 ? (
                    <p className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                      No captured stage data was stored for this step.
                    </p>
                  ) : (
                    <div className="grid gap-3 md:grid-cols-2">
                      {historyCapturedEntries.map((entry) => (
                        <div key={entry.key} className="stat-cell">
                          <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                            {entry.label}
                          </div>
                          <div className="mt-1 break-words text-sm text-foreground">
                            {entry.value}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="space-y-6">
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-foreground">Stage Notes</div>
                    <Badge variant="steel">{historyStageCollections.notes.length} note(s)</Badge>
                  </div>
                  {historyStageCollections.notes.length === 0 ? (
                    <p className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                      No notes were recorded for this stage.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {historyStageCollections.notes.map((note) => (
                        <div key={note.id} className="stat-cell">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-medium text-foreground">
                              {note.author}
                            </div>
                            <Badge variant="steel">
                              {note.createdAtValue
                                ? formatDateTime(note.createdAtValue)
                                : note.createdLabel}
                            </Badge>
                          </div>
                          <div className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                            {note.note}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-foreground">Files</div>
                    <Badge variant="steel">{historyStageCollections.files.length} file(s)</Badge>
                  </div>
                  {historyStageCollections.files.length === 0 ? (
                    <p className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                      No files were attached to this stage.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {historyStageCollections.files.map((file) => (
                        <div key={file.id} className="stat-cell">
                          <div className="text-sm font-medium text-foreground">{file.label}</div>
                          <div className="mt-1 text-xs text-muted-foreground">
                            {file.type}
                            {file.uploadedLabel ? ` · ${file.uploadedLabel}` : ""}
                            {file.uploadedBy ? ` · ${file.uploadedBy}` : ""}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-sm font-semibold text-foreground">Subtasks</div>
                    <Badge variant="steel">{historyStageCollections.subtasks.length} task(s)</Badge>
                  </div>
                  {historyStageCollections.subtasks.length === 0 ? (
                    <p className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                      No subtasks were stored for this stage.
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {historyStageCollections.subtasks.map((task) => (
                        <div key={task.id} className="stat-cell">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <div className="text-sm font-medium text-foreground">
                              {task.label}
                            </div>
                            <Badge
                              variant={
                                task.state === "done"
                                  ? "emerald"
                                  : task.state === "in_progress"
                                    ? "steel"
                                    : "pending"
                              }
                            >
                              {task.state.replace("_", " ")}
                            </Badge>
                          </div>
                          <div className="mt-1 text-xs text-muted-foreground">
                            {task.owner}
                            {task.dueLabel ? ` · due ${task.dueLabel}` : ""}
                            {typeof task.progress === "number" ? ` · ${task.progress}%` : ""}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <Button onClick={closeHistoryDetailDialog} type="button" variant="secondary">
                Close
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {isAdvanceStageDialogOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6"
          onClick={closeAdvanceStageDialog}
        >
          <div
            aria-describedby="advance-stage-dialog-description"
            aria-labelledby="advance-stage-dialog-title"
            aria-modal="true"
            className="w-full max-w-xl rounded-[1.75rem] border border-border bg-background p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl border border-steel-500/20 bg-steel-500/10 p-2 text-steel-600 dark:text-steel-300">
                  <ArrowRight className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground" id="advance-stage-dialog-title">
                    Advance to next stage?
                  </h3>
                  <p
                    className="mt-2 text-sm leading-relaxed text-muted-foreground"
                    id="advance-stage-dialog-description"
                  >
                    You are moving this RFQ from {currentStageLabel} to {nextStageLabel}.
                  </p>
                </div>
              </div>
              <Badge variant="steel">Stage action</Badge>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Current Stage
                </div>
                <div className="mt-1 text-sm font-medium text-foreground">{currentStageLabel}</div>
              </div>
              <div className="stat-cell">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Next Stage
                </div>
                <div className="mt-1 text-sm font-medium text-foreground">{nextStageLabel}</div>
              </div>
            </div>

            <p className="mt-4 text-sm text-muted-foreground">
              Use this confirmation window once your stage data is ready and you want the lifecycle
              to move forward.
            </p>

            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <Button
                disabled={busyAction === "advance-stage"}
                onClick={closeAdvanceStageDialog}
                type="button"
                variant="ghost"
              >
                Keep Editing
              </Button>
              <Button
                disabled={busyAction === "advance-stage"}
                onClick={handleConfirmAdvanceStage}
                type="button"
                variant="secondary"
              >
                <ArrowRight className="h-4 w-4" />
                Advance Stage
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {isNoGoDialogOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6"
          onClick={closeNoGoDialog}
        >
          <div
            aria-describedby="no-go-dialog-description"
            aria-labelledby="no-go-dialog-title"
            aria-modal="true"
            className="w-full max-w-xl rounded-[1.75rem] border border-border bg-background p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-2 text-rose-600 dark:text-rose-300">
                  <CircleSlash className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground" id="no-go-dialog-title">
                    Confirm No-Go decision
                  </h3>
                  <p
                    className="mt-2 text-sm leading-relaxed text-muted-foreground"
                    id="no-go-dialog-description"
                  >
                    This will cancel {rfqBusinessIdentity}, preserve its history, and skip the
                    remaining workflow stages.
                  </p>
                </div>
              </div>
              <Badge variant="rose">Terminal action</Badge>
            </div>

            <div className="mt-5 space-y-2">
              <Label htmlFor="no-go-cancellation-reason">Cancellation reason</Label>
              <Textarea
                autoFocus
                disabled={busyAction === "advance-stage"}
                id="no-go-cancellation-reason"
                onChange={(event) => {
                  setNoGoDialogError("");
                  setNoGoCancellationReason(event.target.value);
                }}
                placeholder="Explain why this RFQ is not moving forward."
                rows={4}
                value={noGoCancellationReason}
              />
              <p className="text-xs text-muted-foreground">
                This reason will be stored on the cancelled RFQ record.
              </p>
              {noGoDialogError ? (
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-3 text-sm text-rose-700 dark:text-rose-300">
                  {noGoDialogError}
                </div>
              ) : null}
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <Button
                disabled={busyAction === "advance-stage"}
                onClick={closeNoGoDialog}
                type="button"
                variant="ghost"
              >
                Keep RFQ Active
              </Button>
              <Button
                disabled={busyAction === "advance-stage"}
                onClick={handleConfirmNoGoCancellation}
                type="button"
                variant="destructive"
              >
                <CircleSlash className="h-4 w-4" />
                Confirm No-Go and Cancel RFQ
              </Button>
            </div>
          </div>
        </div>
      ) : null}

      {isCancelRfqDialogOpen ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6"
          onClick={closeCancelRfqDialog}
        >
          <div
            aria-describedby="cancel-rfq-dialog-description"
            aria-labelledby="cancel-rfq-dialog-title"
            aria-modal="true"
            className="w-full max-w-xl rounded-[1.75rem] border border-border bg-background p-6 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
            role="dialog"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-3">
                <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-2 text-rose-600 dark:text-rose-300">
                  <CircleSlash className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-foreground" id="cancel-rfq-dialog-title">
                    Cancel RFQ
                  </h3>
                  <p
                    className="mt-2 text-sm leading-relaxed text-muted-foreground"
                    id="cancel-rfq-dialog-description"
                  >
                    This will cancel {rfqBusinessIdentity}, preserve its history, and mark the
                    remaining workflow stages as skipped rather than completed.
                  </p>
                </div>
              </div>
              <Badge variant="rose">Terminal action</Badge>
            </div>

            <div className="mt-5 space-y-2">
              <Label htmlFor="cancel-rfq-reason">Cancellation reason</Label>
              <Textarea
                autoFocus
                disabled={busyAction === "cancel-rfq"}
                id="cancel-rfq-reason"
                onChange={(event) => {
                  setCancelRfqDialogError("");
                  setCancelRfqReason(event.target.value);
                }}
                placeholder="Explain why this RFQ is being cancelled."
                rows={4}
                value={cancelRfqReason}
              />
              <p className="text-xs text-muted-foreground">
                This reason will be stored on the cancelled RFQ record.
              </p>
              {cancelRfqDialogError ? (
                <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-3 text-sm text-rose-700 dark:text-rose-300">
                  {cancelRfqDialogError}
                </div>
              ) : null}
            </div>

            <div className="mt-6 flex flex-wrap justify-end gap-3">
              <Button
                disabled={busyAction === "cancel-rfq"}
                onClick={closeCancelRfqDialog}
                type="button"
                variant="ghost"
              >
                Keep RFQ Active
              </Button>
              <Button
                disabled={busyAction === "cancel-rfq"}
                onClick={handleCancelRfq}
                type="button"
                variant="destructive"
              >
                <CircleSlash className="h-4 w-4" />
                Confirm Cancellation
              </Button>
            </div>
          </div>
        </div>
      ) : null}
      {message ? (
        <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/8 p-4 text-sm text-emerald-700 dark:text-emerald-300">
          {message}
        </div>
      ) : null}
      {error ? (
        <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-700 dark:text-rose-300">
          {error}
        </div>
      ) : null}
      {workspaceReadOnly ? (
        <div className="rounded-xl border border-gold-500/20 bg-gold-500/10 p-4 text-sm text-gold-700 dark:text-gold-200">
          Contributor mode is active. You can work on scoped files and subtasks, but stage truth, reminders, and operational notes remain manager-owned.
        </div>
      ) : null}
      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-5">
          <div className="surface-panel p-5">
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  Current Stage Workspace
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  {workspaceReadOnly
                    ? "Review current-stage data, blocker state, stage ownership, and required decisions here. Stage truth remains manager-owned."
                    : "Edit captured data, blocker state, and stage decisions here. This workspace focuses on what the team must record now instead of asking for manual stage progress updates."}
                </p>
              </div>
              <Button onClick={refreshOperational} size="sm" variant="secondary">
                <RefreshCw className="h-3.5 w-3.5" />
                Refresh
              </Button>
            </div>

            {stageWorkspace.loading ? (
              <div className="mt-4">
                <SkeletonCard className="h-[220px]" lines={6} />
              </div>
            ) : stageWorkspace.error ? (
              <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/8 p-4 text-sm text-amber-700 dark:text-amber-300">
                {stageWorkspace.error}
              </div>
            ) : !stageWorkspace.workspace ? (
              <div className="mt-4 rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                This RFQ has no active current-stage workspace. Terminal RFQs keep history, but there is no active stage to edit.
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge variant="steel">
                    {stageWorkspace.workspace.statusLabel ?? rfq.stageLabel}
                  </Badge>
                  {stageWorkspace.workspace.assignedTeam ? (
                    <Badge variant="gold">
                      Team: {stageWorkspace.workspace.assignedTeam}
                    </Badge>
                  ) : null}
                  {missingMandatoryFields.length > 0 || Boolean(stageDecisionValidationMessage) ? (
                    <Badge variant="rose">
                      {stageDecisionValidationMessage ??
                        `Missing ${missingMandatoryFields.length} mandatory field(s)`}
                    </Badge>
                  ) : (
                    <Badge variant="emerald">Mandatory fields satisfied</Badge>
                  )}
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Assigned Team</Label>
                    <div className="rounded-xl border border-border bg-muted/20 p-3 dark:bg-white/[0.02]">
                      <div className="text-sm font-medium text-foreground">
                        {stageWorkspace.workspace.assignedTeam ?? "Unassigned"}
                      </div>
                      <div className="mt-1 text-xs leading-relaxed text-muted-foreground">
                        Stage ownership is inherited from the workflow stage template. Reassignment is not part of the normal current-stage workspace.
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="blocker-status">Blocker Status</Label>
                    {autoBlockingDecisionField ? (
                      <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 p-3 dark:bg-amber-500/6">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="amber">Blocked</Badge>
                          <span className="text-sm font-medium text-foreground">
                            This stage is blocked because {autoBlockingDecisionLabel} is set to No.
                          </span>
                        </div>
                        <div className="mt-1 text-xs leading-relaxed text-muted-foreground">
                          Record the blocker reason below before saving. Normal stage advancement remains blocked until this decision is resolved.
                        </div>
                      </div>
                    ) : (
                      <select
                        className={selectClassName}
                        disabled={!canManageWorkspace}
                        id="blocker-status"
                        onChange={(event) => {
                          const nextStatus = event.target.value as "" | "Blocked" | "Resolved";
                          setError("");
                          setStageForm((current) => ({
                            ...current,
                            blockerReasonCode: nextStatus ? current.blockerReasonCode : "",
                            blockerStatus: nextStatus,
                          }));
                        }}
                        value={stageForm.blockerStatus}
                      >
                        <option value="">No blocker state</option>
                        <option value="Blocked">Blocked</option>
                        <option value="Resolved">Resolved</option>
                      </select>
                    )}
                    {!effectiveBlockerStatus ? (
                      <p className="text-xs text-muted-foreground">
                        No blocker reason is stored while the stage has no blocker state.
                      </p>
                    ) : null}
                  </div>

                  {effectiveBlockerStatus ? (
                    <div className="space-y-2">
                      <Label htmlFor="blocker-reason">Blocker Reason</Label>
                      <Input
                        disabled={!canManageWorkspace}
                        id="blocker-reason"
                        onChange={(event) => {
                          setError("");
                          setStageForm((current) => ({
                            ...current,
                            blockerReasonCode: event.target.value,
                          }));
                        }}
                        placeholder="waiting_client_input"
                        value={stageForm.blockerReasonCode}
                      />
                    </div>
                  ) : null}
                </div>

                {isTerminalOutcomeStage ? (
                  <div className="space-y-3 rounded-xl border border-gold-500/20 bg-gold-500/8 p-4 dark:bg-gold-500/6">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-foreground">
                          Terminal Outcome
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">
                          {getTerminalOutcomeHelpText()}
                        </p>
                      </div>
                      <Badge variant="gold">Final stage</Badge>
                    </div>

                    <div className="grid gap-4 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="terminal-outcome">Outcome</Label>
                        <select
                          className={selectClassName}
                          disabled={!canManageWorkspace}
                          id="terminal-outcome"
                          onChange={(event) => handleTerminalOutcomeChange(event.target.value)}
                          value={terminalOutcomeValue}
                        >
                          <option value="">Choose Awarded or Lost</option>
                          {TERMINAL_OUTCOME_OPTIONS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </select>
                      </div>

                      {terminalOutcomeValue === TERMINAL_OUTCOME_LOST ? (
                        <div className="space-y-2">
                          <Label htmlFor="terminal-lost-reason">Lost Reason</Label>
                          <select
                            className={selectClassName}
                            disabled={!canManageWorkspace}
                            id="terminal-lost-reason"
                            onChange={(event) => handleLostReasonChange(event.target.value)}
                            value={lostReasonCodeValue}
                          >
                            <option value="">Choose why the RFQ was lost</option>
                            {LOST_REASON_OPTIONS.map((option) => (
                              <option key={option.value} value={option.value}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                          <p className="text-xs text-muted-foreground">
                            {getLostReasonHelpText()}
                          </p>
                          {lostReasonCodeValue === LOST_REASON_OTHER_VALUE ? (
                            <div className="space-y-2">
                              <Label htmlFor="terminal-lost-reason-other">
                                Lost Reason Detail
                              </Label>
                              <Textarea
                                disabled={!canManageWorkspace}
                                id="terminal-lost-reason-other"
                                onChange={(event) =>
                                  handleLostReasonOtherChange(event.target.value)
                                }
                                placeholder="Explain why the RFQ was lost."
                                rows={3}
                                value={lostReasonOtherValue}
                              />
                            </div>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                  </div>
                ) : null}

                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-foreground">
                        Captured Data
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {mandatoryFieldKeys.length > 0
                          ? "Workflow-required fields are rendered directly here. Additional stage details stay optional and hidden unless this stage needs them."
                          : "This stage has no workflow-defined captured fields yet. Additional stage details are optional and only needed when the stage requires extra context."}
                      </p>
                    </div>
                    {canManageWorkspace ? (
                      <Button
                        onClick={handleAddAdditionalCapturedField}
                        size="sm"
                        type="button"
                        variant="secondary"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Add Additional Detail
                      </Button>
                    ) : null}
                  </div>

                  {mandatoryFieldKeys.length > 0 ? (
                    <div className="space-y-3">
                      {mandatoryCapturedFields.map((field) => (
                        <div
                          key={field.key}
                          className="grid gap-3 md:grid-cols-[1.1fr_auto]"
                        >
                          <div className="space-y-2">
                            <Label htmlFor={`captured-required-${field.key}`}>
                              {formatCapturedFieldLabel(field.key)}
                            </Label>
                            {isCommercialStageField(field.key) ? (
                              <div className="space-y-3">
                                <div className="grid gap-3 md:grid-cols-[1.3fr_minmax(0,0.9fr)]">
                                  <div className="space-y-2">
                                    <Label
                                      className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
                                      htmlFor={`captured-required-${field.key}-amount`}
                                    >
                                      Amount
                                    </Label>
                                    <Input
                                      disabled={!canManageWorkspace}
                                      id={`captured-required-${field.key}-amount`}
                                      inputMode="decimal"
                                      min="0"
                                      onChange={(event) =>
                                        handleCommercialFieldChange(
                                          field.key,
                                          event.target.value,
                                          getCommercialFieldCurrencyValue(
                                            capturedData,
                                            field.key,
                                          ),
                                        )
                                      }
                                      placeholder={getCommercialFieldAmountPlaceholder(
                                        field.key,
                                      )}
                                      step="0.01"
                                      type="number"
                                      value={getCommercialFieldAmountValue(
                                        capturedData,
                                        field.key,
                                      )}
                                    />
                                  </div>
                                  <div className="space-y-2">
                                    <Label
                                      className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"
                                      htmlFor={`captured-required-${field.key}-currency`}
                                    >
                                      Currency
                                    </Label>
                                    <select
                                      className={selectClassName}
                                      disabled={!canManageWorkspace}
                                      id={`captured-required-${field.key}-currency`}
                                      onChange={(event) =>
                                        handleCommercialFieldChange(
                                          field.key,
                                          getCommercialFieldAmountValue(
                                            capturedData,
                                            field.key,
                                          ),
                                          event.target.value || DEFAULT_CURRENCY_CODE,
                                        )
                                      }
                                      value={getCommercialFieldCurrencyValue(
                                        capturedData,
                                        field.key,
                                      )}
                                    >
                                      {CURRENCY_OPTIONS.map((option) => (
                                        <option key={option.code} value={option.code}>
                                          {option.code} - {option.label}
                                        </option>
                                      ))}
                                    </select>
                                  </div>
                                </div>
                                <p className="text-xs text-muted-foreground">
                                  {getCommercialFieldHelpText(field.key)}
                                </p>
                                {getCommercialFieldAmountValue(capturedData, field.key) ? (
                                  <div className="rounded-xl border border-border bg-background/70 px-3 py-2 text-xs text-muted-foreground">
                                    Read the stored amount as
                                    <span className="ml-1 font-semibold text-foreground">
                                      {formatCommercialAmountWithCurrency(
                                        getCommercialFieldAmountValue(capturedData, field.key),
                                        getCommercialFieldCurrencyValue(
                                          capturedData,
                                          field.key,
                                        ),
                                      )}
                                    </span>
                                  </div>
                                ) : null}
                              </div>
                            ) : isControlledStageDecisionField(field.key) ? (
                              <select
                                className={selectClassName}
                                disabled={!canManageWorkspace}
                                id={`captured-required-${field.key}`}
                                onChange={(event) =>
                                  handleMandatoryCapturedFieldChange(field.key, event.target.value)
                                }
                                value={field.value}
                              >
                                <option value="">
                                  {getControlledStageDecisionPlaceholder(field.key)}
                                </option>
                                {getControlledStageDecisionOptions(field.key)?.map((option) => (
                                  <option key={option.value} value={option.value}>
                                    {option.label}
                                  </option>
                                ))}
                              </select>
                            ) : isApprovalSignatureField(field.key) ? (
                              <div className="space-y-2">
                                <Input
                                  disabled={!canManageWorkspace}
                                  id={`captured-required-${field.key}`}
                                  onChange={(event) =>
                                    handleMandatoryCapturedFieldChange(
                                      field.key,
                                      event.target.value,
                                    )
                                  }
                                  placeholder={getApprovalSignaturePlaceholder()}
                                  value={field.value}
                                />
                                <p className="text-xs text-muted-foreground">
                                  {getApprovalSignatureHelpText()}
                                </p>
                              </div>
                            ) : (
                              <Input
                                disabled={!canManageWorkspace}
                                id={`captured-required-${field.key}`}
                                onChange={(event) =>
                                  handleMandatoryCapturedFieldChange(field.key, event.target.value)
                                }
                                value={field.value}
                              />
                            )}
                            {autoBlockingDecisionField === field.key ? (
                              <p className="text-xs text-amber-700 dark:text-amber-300">
                                Choosing No automatically opens blocker handling for this stage.
                              </p>
                            ) : null}
                          </div>
                          <div className="flex items-end">
                            <Badge variant="gold">Required by workflow</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground dark:bg-white/[0.02]">
                      No workflow-mandatory captured fields are defined for this stage.
                    </div>
                  )}

                  {shouldShowAdditionalCapturedData ? (
                    <div className="space-y-3 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <div className="text-sm font-semibold text-foreground">
                            Additional Stage Details
                          </div>
                          <p className="mt-1 text-sm text-muted-foreground">
                            Add extra stage context here when the workflow-defined fields do not capture the full picture. Saved details stay attached to this stage after refresh and navigation.
                          </p>
                        </div>
                        {canManageWorkspace ? (
                          <Button
                            onClick={handleAddAdditionalCapturedField}
                            size="sm"
                            type="button"
                            variant="ghost"
                          >
                            <Plus className="h-3.5 w-3.5" />
                            Add Another Detail
                          </Button>
                        ) : null}
                      </div>

                      {additionalCapturedFields.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No additional stage details are currently stored for this stage.
                        </p>
                      ) : (
                        additionalCapturedFields.map((field) => (
                          <div
                            key={field.id}
                            className="grid gap-3 md:grid-cols-[0.9fr_1.1fr_auto]"
                          >
                            <div className="space-y-2">
                              <Label htmlFor={`captured-key-${field.id}`}>Detail name</Label>
                              <Input
                                disabled={!canManageWorkspace}
                                id={`captured-key-${field.id}`}
                                onChange={(event) =>
                                  handleAdditionalCapturedFieldChange(
                                    field.id,
                                    "key",
                                    event.target.value,
                                  )
                                }
                                placeholder="clarification_topic"
                                value={field.key}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor={`captured-value-${field.id}`}>Detail value</Label>
                              <Input
                                disabled={!canManageWorkspace}
                                id={`captured-value-${field.id}`}
                                onChange={(event) =>
                                  handleAdditionalCapturedFieldChange(
                                    field.id,
                                    "value",
                                    event.target.value,
                                  )
                                }
                                placeholder="Enter the stage detail"
                                value={field.value}
                              />
                            </div>
                            <div className="flex items-end gap-2">
                              <Button
                                onClick={() => handleRemoveAdditionalCapturedField(field.id)}
                                size="icon"
                                type="button"
                                variant="ghost"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-dashed border-border bg-muted/10 p-4 text-sm text-muted-foreground">
                      Additional stage details stay hidden until the stage needs extra context beyond the workflow-defined fields.
                    </div>
                  )}
                </div>

                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                  <div className="stat-cell">
                    <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Planned Start
                    </div>
                    <div className="mt-1 text-sm text-foreground">
                      {stageWorkspace.workspace.plannedStartLabel ?? "Pending"}
                    </div>
                  </div>
                  <div className="stat-cell">
                    <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Planned End
                    </div>
                    <div className="mt-1 text-sm text-foreground">
                      {stageWorkspace.workspace.plannedEndLabel ?? "Pending"}
                    </div>
                  </div>
                  <div className="stat-cell">
                    <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Actual Start
                    </div>
                    <div className="mt-1 text-sm text-foreground">
                      {stageWorkspace.workspace.actualStartLabel ?? "Pending"}
                    </div>
                  </div>
                  <div className="stat-cell">
                    <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                      Actual End
                    </div>
                    <div className="mt-1 text-sm text-foreground">
                      {stageWorkspace.workspace.actualEndLabel ?? "Pending"}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap gap-2">
                  <Button
                    disabled={!canManageWorkspace || !currentStageId || busyAction === "save-stage"}
                    onClick={handleSaveStage}
                  >
                    <Save className="h-4 w-4" />
                    Save Stage
                  </Button>
                  <Button
                    disabled={!permissions.canAdvanceStage || !currentStageId || busyAction === "advance-stage"}
                    onClick={handleAdvanceStage}
                    variant="secondary"
                  >
                    <ArrowRight className="h-4 w-4" />
                    {isTerminalOutcomeStage ? "Finalize Outcome" : "Advance Stage"}
                  </Button>
                </div>
              </div>
            )}
          </div>

          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Lifecycle History</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Review persisted stage notes, captured data, blocker context, and key decisions
                  from earlier workflow steps here.
                </p>
              </div>
              <Badge variant="steel">{rfq.stageHistory.length} stage record(s)</Badge>
            </div>

            {rfq.stageHistory.length === 0 ? (
              <p className="mt-4 text-sm text-muted-foreground">
                No stage history has been recorded for this RFQ yet.
              </p>
            ) : (
              <div className="mt-4 space-y-4">
                <div className="flex flex-wrap gap-2">
                  {rfq.stageHistory.map((stage) => {
                    const isSelected = selectedHistoryStageId === stage.id;
                    const badgeVariant =
                      stage.state === "blocked"
                        ? "amber"
                        : stage.state === "skipped"
                          ? "rose"
                        : stage.state === "completed"
                          ? "emerald"
                          : stage.state === "active"
                            ? "steel"
                            : "pending";

                    return (
                      <button
                        key={stage.id}
                        className={`rounded-xl border px-3 py-2 text-left transition-colors ${
                          isSelected
                            ? "border-steel-500/40 bg-steel-500/10"
                            : "border-border bg-muted/20 hover:border-border/80 hover:bg-muted/30"
                        }`}
                        onClick={() => setSelectedHistoryStageId(stage.id)}
                        type="button"
                      >
                        <div className="text-sm font-medium text-foreground">
                          {stage.order}. {stage.label}
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant={badgeVariant}>{stage.statusLabel ?? stage.state}</Badge>
                          {stage.timestampLabel ? <span>{stage.timestampLabel}</span> : null}
                        </div>
                      </button>
                    );
                  })}
                </div>

                {historyStageLoading ? (
                  <SkeletonCard className="h-[220px]" lines={6} />
                ) : historyStageError ? (
                  <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-700 dark:text-rose-300">
                    {historyStageError}
                  </div>
                ) : !historyStageWorkspace ? (
                  <div className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                    Select a stage to review its persisted lifecycle detail.
                  </div>
                ) : (
                  <div className="space-y-4 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <div className="text-sm font-semibold text-foreground">
                          {historyStageWorkspace.label}
                        </div>
                        <p className="mt-1 text-sm text-muted-foreground">
                          Stage-owned history stays read-only here so prior notes, decisions, and
                          captured data remain inspectable during the RFQ lifecycle and after
                          completion without overloading the main history card.
                        </p>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant={getHistoryStageBadgeVariant(historyStageWorkspace.state)}>
                          {historyStageWorkspace.statusLabel ?? selectedHistoryStageSummary?.state ?? "Recorded"}
                        </Badge>
                        {historyStageWorkspace.blockerStatus ? (
                          <Badge variant="amber">{historyStageWorkspace.blockerStatus}</Badge>
                        ) : null}
                        <Button onClick={openHistoryDetailDialog} size="sm" type="button" variant="secondary">
                          View Full Stage Detail
                        </Button>
                      </div>
                    </div>

                    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                      <div className="stat-cell">
                        <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          Actual Start
                        </div>
                        <div className="mt-1 text-sm text-foreground">
                          {historyStageWorkspace.actualStartLabel ?? "Not started"}
                        </div>
                      </div>
                      <div className="stat-cell">
                        <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          Actual End
                        </div>
                        <div className="mt-1 text-sm text-foreground">
                          {historyStageWorkspace.actualEndLabel ?? "Not finished"}
                        </div>
                      </div>
                      <div className="stat-cell">
                        <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          Planned Window
                        </div>
                        <div className="mt-1 text-sm text-foreground">
                          {historyStageWorkspace.plannedStartLabel && historyStageWorkspace.plannedEndLabel
                            ? `${historyStageWorkspace.plannedStartLabel} -> ${historyStageWorkspace.plannedEndLabel}`
                            : "Not scheduled"}
                        </div>
                      </div>
                      <div className="stat-cell">
                        <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                          Recorded Activity
                        </div>
                        <div className="mt-1 text-sm text-foreground">
                          {historyLifecycleEvents.length} event(s) · {historyCapturedEntries.length} data point(s)
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          {historyStageCollections.notes.length} note(s) · {historyStageCollections.files.length} file(s) · {historyStageCollections.subtasks.length} task(s)
                        </div>
                      </div>
                    </div>

                    {historyStageWorkspace.blockerStatus || historyStageWorkspace.blockerReasonCode ? (
                      <div className="rounded-xl border border-amber-500/20 bg-amber-500/8 p-4 dark:bg-amber-500/6">
                        <div className="flex flex-wrap items-center gap-2">
                          <Badge variant="amber">
                            {historyStageWorkspace.blockerStatus ?? "Blocker"}
                          </Badge>
                          <span className="text-sm font-medium text-foreground">
                            {historyStageWorkspace.blockerReasonCode
                              ? `Latest blocker context: ${historyStageWorkspace.blockerReasonCode}`
                              : "This stage recorded blocker activity during the RFQ lifecycle."}
                          </span>
                        </div>
                      </div>
                    ) : null}

                    <div className="space-y-3">
                      <div className="flex items-center justify-between gap-3">
                        <div className="text-sm font-semibold text-foreground">
                          Recent Lifecycle Events
                        </div>
                        <Badge variant="steel">{recentHistoryEvents.length} shown</Badge>
                      </div>
                      {recentHistoryEvents.length === 0 ? (
                        <p className="text-sm text-muted-foreground">
                          No blocker or decision events were recorded for this stage.
                        </p>
                      ) : (
                        <div className="space-y-2">
                          {recentHistoryEvents.map((event) => (
                            <div key={event.id} className="stat-cell">
                              <div className="flex flex-wrap items-center justify-between gap-2">
                                <div>
                                  <div className="text-sm font-medium text-foreground">
                                    {event.title}
                                  </div>
                                  <div className="mt-1 text-xs text-muted-foreground">
                                    {event.summary}
                                  </div>
                                </div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <Badge variant={event.tone}>{event.timestampLabel}</Badge>
                                  {event.source ? (
                                    <Badge variant="steel">
                                      {event.source === "automatic" ? "Automatic" : "Manual"}
                                    </Badge>
                                  ) : null}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Stage Notes</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Notes stay attached to the current manager stage and refresh after each save.
                </p>
              </div>
              <Badge variant="steel">{rfq.stageNotes.length} note(s)</Badge>
            </div>

            {permissions.canManageStageNotes && currentStageId ? (
              <div className="mt-4 space-y-3 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <Textarea
                  onChange={(event) => setNoteText(event.target.value)}
                  placeholder="Add an operational note for this stage..."
                  value={noteText}
                />
                <div className="flex justify-end">
                  <Button
                    disabled={!noteText.trim() || busyAction === "add-note"}
                    onClick={handleAddNote}
                    size="sm"
                  >
                    <Send className="h-3.5 w-3.5" />
                    Add Note
                  </Button>
                </div>
              </div>
            ) : null}

            {rfq.stageNotes.length === 0 ? (
              <p className="mt-4 text-sm text-muted-foreground">
                No current-stage notes are available.
              </p>
            ) : (
              <div className="mt-4 space-y-2">
                {rfq.stageNotes.map((note) => (
                  <button
                    key={note.id}
                    className="stat-cell w-full text-left transition-colors hover:border-border/80 hover:bg-muted/30"
                    onClick={() => openStageNoteDetail(note)}
                    type="button"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-foreground">
                        {note.author}
                      </span>
                      <Badge
                        variant={
                          note.tone === "success"
                            ? "emerald"
                            : note.tone === "warning"
                              ? "gold"
                              : "steel"
                        }
                      >
                        {note.createdLabel}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-sm text-muted-foreground">
                      {truncateStageNotePreview(note.note)}
                    </p>
                    <div className="mt-2 text-xs font-medium uppercase tracking-[0.14em] text-steel-600 dark:text-steel-300">
                      Read more
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Files</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Upload directly into the current stage, then download or delete files from the manager service.
                </p>
              </div>
              <Badge variant="steel">{rfq.recentFiles.length} file(s)</Badge>
            </div>

            {rfq.uploads.length > 0 ? (
              <div className="mt-4 space-y-4">
                {rfq.uploads.map((upload) => (
                  <UploadZone
                    key={upload.kind}
                    description={upload.description}
                    fileName={upload.fileName}
                    initialStatus={upload.status}
                    title={upload.title}
                    uploadedLabel={upload.uploadedLabel}
                  />
                ))}
              </div>
            ) : canUploadFiles && currentStageId ? (
              <div className="mt-4 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="grid gap-3 md:grid-cols-[1fr_0.9fr]">
                  <div className="space-y-2">
                    <Label htmlFor="stage-file-upload">File</Label>
                    <Input
                      id="stage-file-upload"
                      onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
                      type="file"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="stage-file-type">File Type</Label>
                    <select
                      className={selectClassName}
                      id="stage-file-type"
                      onChange={(event) => setFileType(event.target.value)}
                      value={fileType}
                    >
                      {fileTypeOptions.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="mt-3 flex justify-end">
                  <Button
                    disabled={!selectedFile || busyAction === "upload-file"}
                    onClick={handleUploadFile}
                    size="sm"
                  >
                    <Upload className="h-3.5 w-3.5" />
                    Upload File
                  </Button>
                </div>
              </div>
            ) : null}

            {rfq.recentFiles.length === 0 ? (
              <p className="mt-4 text-sm text-muted-foreground">
                No current-stage files are available.
              </p>
            ) : (
              <div className="mt-4 space-y-2">
                {rfq.recentFiles.map((file) => (
                  <div
                    key={file.id}
                    className="stat-cell flex flex-wrap items-center justify-between gap-3"
                  >
                    <div>
                      <div className="text-sm font-medium text-foreground">{file.label}</div>
                      <div className="text-xs text-muted-foreground">
                        {file.type} · {file.uploadedLabel}
                        {file.uploadedBy ? ` · ${file.uploadedBy}` : ""}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {file.downloadUrl ? (
                        <Button asChild size="sm" variant="secondary">
                          <a href={file.downloadUrl} rel="noreferrer" target="_blank">
                            <Download className="h-3.5 w-3.5" />
                            Download
                          </a>
                        </Button>
                      ) : null}
                      {canDeleteStageFile(role, permissions, rfq, file, actorName) ? (
                        <Button
                          disabled={busyAction === `delete-file:${file.id}`}
                          onClick={() => handleDeleteFile(file)}
                          size="sm"
                          variant="ghost"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                          Delete
                        </Button>
                      ) : null}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div className="space-y-5">
          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">
                  RFQ Lifecycle Controls
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Edit shell metadata here. Workflow progression remains stage-driven, and cancellation stays the explicit safe terminal action.
                </p>
              </div>
              <Badge variant={role === "manager" && !isTerminalRfq ? "steel" : "pending"}>
                {role === "manager" && !isTerminalRfq ? "Editable" : "Read Only"}
              </Badge>
            </div>

            <div className="mt-4 space-y-4">
              {isTerminalRfq ? (
                <div className="rounded-xl border border-steel-500/20 bg-steel-500/10 p-4 text-sm text-steel-700 dark:text-steel-300">
                  Terminal RFQs are read-only through standard lifecycle controls.
                </div>
              ) : null}
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="rfq-title">RFQ Title</Label>
                  <Input
                    disabled={!canEditLifecycleControls}
                    id="rfq-title"
                    onChange={(event) =>
                      setRfqForm((current) => ({ ...current, title: event.target.value }))
                    }
                    value={rfqForm.title}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rfq-client">Client</Label>
                  <Input
                    disabled={!canEditLifecycleControls}
                    id="rfq-client"
                    onChange={(event) =>
                      setRfqForm((current) => ({ ...current, client: event.target.value }))
                    }
                    value={rfqForm.client}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rfq-industry">Industry</Label>
                  <select
                    className={selectClassName}
                    disabled={!canEditLifecycleControls}
                    id="rfq-industry"
                    onChange={(event) => {
                      setError("");
                      setSelectedIndustryOption(event.target.value as IndustryOption);
                    }}
                    value={selectedIndustryOption}
                  >
                    {industryOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rfq-owner">Owner</Label>
                  <Input
                    disabled={!canEditLifecycleControls}
                    id="rfq-owner"
                    onChange={(event) =>
                      setRfqForm((current) => ({ ...current, owner: event.target.value }))
                    }
                    value={rfqForm.owner}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rfq-deadline">Deadline</Label>
                  <Input
                    disabled={!canEditLifecycleControls}
                    id="rfq-deadline"
                    min={minimumFeasibleRfqDeadlineIso ?? todayIso}
                    onChange={(event) => {
                      setError("");
                      setRfqForm((current) => ({ ...current, deadline: event.target.value }));
                    }}
                    type="date"
                    value={rfqForm.deadline}
                  />
                  {minimumFeasibleRfqDeadlineIso ? (
                    <p
                      className={`text-xs ${
                        rfqDeadlineTooNarrow ? "text-rose-600 dark:text-rose-300" : "text-muted-foreground"
                      }`}
                    >
                      {rfqDeadlineTooNarrow
                        ? buildWorkflowDeadlineTooNarrowMessage(minimumFeasibleRfqDeadlineIso)
                        : `This workflow requires ${formatWorkflowDeadlineIso(minimumFeasibleRfqDeadlineIso)} or later.`}
                    </p>
                  ) : null}
                </div>
                <div className="space-y-2">
                  <Label htmlFor="rfq-priority">Priority</Label>
                  <select
                    className={selectClassName}
                    disabled={!canEditLifecycleControls}
                    id="rfq-priority"
                    onChange={(event) =>
                      setRfqForm((current) => ({
                        ...current,
                        priority: event.target.value as "normal" | "critical",
                      }))
                    }
                    value={rfqForm.priority}
                  >
                    <option value="normal">normal</option>
                    <option value="critical">critical</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <Label>Lifecycle Status</Label>
                  <div className="rounded-xl border border-border bg-muted/20 px-3 py-3 text-sm dark:bg-white/[0.02]">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge variant={getRfqStatusMeta(rfq.status).tone}>
                        {getRfqStatusMeta(rfq.status).label}
                      </Badge>
                      <span className="text-muted-foreground">
                        Status is derived by lifecycle truth. Use the dedicated cancel action for safe terminal invalidation.
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {selectedIndustryOption === OTHER_INDUSTRY_OPTION ? (
                <div className="space-y-2">
                  <Label htmlFor="rfq-custom-industry">Custom Industry</Label>
                  <Input
                    disabled={!canEditLifecycleControls}
                    id="rfq-custom-industry"
                    onChange={(event) => {
                      setError("");
                      setCustomIndustry(event.target.value);
                    }}
                    placeholder="Enter the industry"
                    value={customIndustry}
                  />
                </div>
              ) : null}

              <div className="space-y-2">
                <Label htmlFor="rfq-description">Description</Label>
                <Textarea
                  disabled={!canEditLifecycleControls}
                  id="rfq-description"
                  onChange={(event) =>
                    setRfqForm((current) => ({ ...current, description: event.target.value }))
                  }
                  value={rfqForm.description}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="rfq-outcome-reason">Outcome Reason</Label>
                <Textarea
                  disabled
                  id="rfq-outcome-reason"
                  onChange={(event) =>
                    setRfqForm((current) => ({
                      ...current,
                      outcomeReason: event.target.value,
                    }))
                  }
                  placeholder="Why the RFQ was awarded, lost, or cancelled..."
                  value={rfqForm.outcomeReason}
                />
                <p className="text-xs text-muted-foreground">
                  {isTerminalRfq
                    ? "Outcome reason stays visible here, but terminal RFQs are read-only in standard lifecycle controls."
                    : "Outcome reason is recorded when this RFQ reaches a terminal state."}
                </p>
              </div>

              <div className="flex justify-end">
                <div className="flex flex-wrap justify-end gap-2">
                  {permissions.canEditCoreRfq ? (
                  <Button
                    disabled={!canCancelRfq || busyAction === "cancel-rfq"}
                    onClick={openCancelRfqDialog}
                    variant="destructive"
                  >
                    <CircleSlash className="h-4 w-4" />
                    Cancel RFQ
                  </Button>
                  ) : null}
                  <Button
                    disabled={!canEditLifecycleControls || busyAction === "save-rfq"}
                    onClick={handleSaveRfq}
                  >
                    <Save className="h-4 w-4" />
                    Save RFQ
                  </Button>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground dark:bg-white/[0.02]">
                Hard delete is not part of the current RFQ contract. Use
                {" "}
                <span className="font-medium text-foreground">Cancel RFQ</span>
                {" "}
                to invalidate the record safely while preserving RFQ history and generated stages.
              </div>
            </div>
          </div>

          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Subtasks</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  Subtasks roll up directly into stage progress when they exist.
                </p>
              </div>
              <Badge variant="steel">{rfq.subtasks.length} task(s)</Badge>
            </div>

            {canManageSubtasks && currentStageId ? (
              <div className="mt-4 rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="grid gap-3 md:grid-cols-3">
                  <Input
                    onChange={(event) =>
                      setNewSubtask((current) => ({ ...current, name: event.target.value }))
                    }
                    placeholder="Subtask name"
                    value={newSubtask.name}
                  />
                  <Input
                    onChange={(event) =>
                      setNewSubtask((current) => ({
                        ...current,
                        assignedTo: event.target.value,
                      }))
                    }
                    placeholder="Assigned to"
                    value={newSubtask.assignedTo}
                  />
                  <Input
                    onChange={(event) =>
                      setNewSubtask((current) => ({ ...current, dueDate: event.target.value }))
                    }
                    max={stageWindowEndValue}
                    min={stageWindowStartValue}
                    type="date"
                    value={newSubtask.dueDate}
                  />
                </div>
                {stageWindowHint ? (
                  <p className="mt-3 text-xs text-muted-foreground">
                    {stageWindowHint}
                  </p>
                ) : null}
                {newSubtaskCreateError ? (
                  <div className="mt-3 rounded-xl border border-rose-500/20 bg-rose-500/8 p-3 text-sm text-rose-700 dark:text-rose-300">
                    {newSubtaskCreateError}
                  </div>
                ) : null}
                <div className="mt-3 flex justify-end">
                  <Button
                    disabled={
                      !newSubtask.name.trim() ||
                      !newSubtask.assignedTo.trim() ||
                      !newSubtask.dueDate ||
                      Boolean(newSubtaskCreateError) ||
                      busyAction === "create-subtask"
                    }
                    onClick={handleCreateSubtask}
                    size="sm"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Create Subtask
                  </Button>
                </div>
              </div>
            ) : null}

            {rfq.subtasks.length === 0 ? (
              <p className="mt-4 text-sm text-muted-foreground">
                No current-stage subtasks are available.
              </p>
            ) : (
              <div className="mt-4 space-y-3">
                {rfq.subtasks.map((task) => {
                  const draft = subtaskDrafts[task.id];
                  const draftDueDateError = draft
                    ? getSubtaskDueDateValidationMessage(
                        draft.dueDate,
                        stageWindowStartValue,
                        stageWindowEndValue,
                      )
                    : null;
                  const draftProgressError = draft
                    ? getSubtaskProgressValidationMessage(draft.progress, task.progress)
                    : null;

                  return (
                    <div key={task.id} className="stat-cell space-y-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div className="text-sm font-medium text-foreground">{task.label}</div>
                        <Badge
                          variant={
                            task.state === "done"
                              ? "emerald"
                              : task.state === "in_progress"
                                ? "steel"
                                : "pending"
                          }
                        >
                          {task.state.replace("_", " ")}
                        </Badge>
                      </div>

                      {draft ? (
                        <div className="grid gap-3 md:grid-cols-2">
                          <Input
                            onChange={(event) =>
                              setSubtaskDrafts((current) => ({
                                ...current,
                                [task.id]: {
                                  ...current[task.id],
                                  name: event.target.value,
                                },
                              }))
                            }
                            value={draft.name}
                          />
                          <Input
                            onChange={(event) =>
                              setSubtaskDrafts((current) => ({
                                ...current,
                                [task.id]: {
                                  ...current[task.id],
                                  assignedTo: event.target.value,
                                },
                              }))
                            }
                            placeholder="Assigned to"
                            value={draft.assignedTo}
                          />
                          <Input
                            max={100}
                            min={0}
                            onChange={(event) =>
                              setSubtaskDrafts((current) => ({
                                ...current,
                                [task.id]: normalizeSubtaskDraftState({
                                  ...current[task.id],
                                  progress: event.target.value,
                                }),
                              }))
                            }
                            type="number"
                            value={draft.progress}
                          />
                          <Input
                            onChange={(event) =>
                              setSubtaskDrafts((current) => ({
                                ...current,
                                [task.id]: {
                                  ...current[task.id],
                                  dueDate: event.target.value,
                                },
                              }))
                            }
                            max={stageWindowEndValue}
                            min={stageWindowStartValue}
                            type="date"
                            value={draft.dueDate}
                          />
                          <select
                            className={selectClassName}
                            onChange={(event) =>
                              setSubtaskDrafts((current) => ({
                                ...current,
                                [task.id]: normalizeSubtaskDraftState({
                                  ...current[task.id],
                                  status: event.target.value as SubtaskDraft["status"],
                                }),
                              }))
                            }
                            value={draft.status}
                          >
                            <option value="Open">Open</option>
                            <option value="In progress">In progress</option>
                            <option value="Done">Done</option>
                          </select>
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              disabled={
                                Boolean(draftDueDateError) ||
                                Boolean(draftProgressError) ||
                                busyAction === `update-subtask:${task.id}`
                              }
                              onClick={() => handleUpdateSubtask(task.id)}
                              size="sm"
                              variant="secondary"
                            >
                              <Save className="h-3.5 w-3.5" />
                              Save
                            </Button>
                            <Button
                              disabled={busyAction === `delete-subtask:${task.id}`}
                              onClick={() => handleDeleteSubtask(task.id)}
                              size="sm"
                              variant="ghost"
                            >
                              <Trash2 className="h-3.5 w-3.5" />
                              Delete
                            </Button>
                          </div>
                          {draftDueDateError || draftProgressError ? (
                            <div className="md:col-span-2">
                              <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-3 text-sm text-rose-700 dark:text-rose-300">
                                {draftDueDateError ?? draftProgressError}
                              </div>
                            </div>
                          ) : stageWindowHint ? (
                            <div className="md:col-span-2 text-xs text-muted-foreground">
                              {stageWindowHint}
                            </div>
                          ) : null}
                        </div>
                      ) : (
                        <div className="text-xs text-muted-foreground">
                          {task.owner} · due {task.dueLabel}
                          {typeof task.progress === "number" ? ` · ${task.progress}%` : ""}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="surface-panel p-5">
            <div className="flex items-start justify-between gap-3">
              <div>
                <h3 className="text-sm font-semibold text-foreground">Reminders</h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {canManageReminders
                    ? "Create and review reminders attached to this RFQ here. Service-wide reminder rules, batch controls, and portfolio visibility live in the Reminder Center. Manual reminders can be resolved directly; automatic reminders clear when their condition no longer applies."
                    : canReadReminderState
                      ? "Read-only reminder and escalation state attached to this RFQ. Service-wide reminder processing remains manager-owned in the Reminder Center."
                      : "Reminder state is not available for this RFQ under your current scope."}
                </p>
              </div>
              <Badge variant="steel">{sortedRfqReminders.length} RFQ reminder(s)</Badge>
            </div>

            {reminders.loading ? (
              <div className="mt-4">
                <SkeletonCard className="h-[180px]" lines={5} />
              </div>
            ) : reminders.error ? (
              <div className="mt-4 rounded-xl border border-rose-500/20 bg-rose-500/8 p-4 text-sm text-rose-700 dark:text-rose-300">
                {reminders.error}
              </div>
            ) : (
              <div className="mt-4 space-y-4">
                {canManageReminders ? (
                  <div className="rounded-xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                    <div className="grid gap-3 md:grid-cols-3">
                      <div className="space-y-2 md:col-span-3">
                        <Label htmlFor="reminder-scope">Reminder scope</Label>
                        <select
                          className={selectClassName}
                          id="reminder-scope"
                          onChange={(event) =>
                            setReminderForm((current) => ({
                              ...current,
                              scope: event.target.value as "rfq" | "stage",
                            }))
                          }
                          value={reminderForm.scope}
                        >
                          <option value="rfq">RFQ-level</option>
                          {hasStageLinkedReminderScope ? (
                            <option value="stage">Stage-linked to {currentStageLabel}</option>
                          ) : null}
                        </select>
                        <p className="text-xs text-muted-foreground">
                          {reminderForm.scope === "stage" && hasStageLinkedReminderScope
                            ? `This reminder will stay attached to ${currentStageLabel}.`
                            : "This reminder will follow the RFQ as a whole, not only the current stage."}
                        </p>
                      </div>
                      <select
                        className={selectClassName}
                        onChange={(event) =>
                          setReminderForm((current) => ({
                            ...current,
                            type: event.target.value as "internal" | "external",
                          }))
                        }
                        value={reminderForm.type}
                      >
                        <option value="internal">internal</option>
                        <option value="external">external</option>
                      </select>
                      <Input
                        onChange={(event) =>
                          setReminderForm((current) => ({
                            ...current,
                            assignedTo: event.target.value,
                          }))
                        }
                        placeholder="Assigned to"
                        value={reminderForm.assignedTo}
                      />
                      <Input
                        onChange={(event) =>
                          setReminderForm((current) => ({
                            ...current,
                            dueDate: event.target.value,
                          }))
                        }
                        max={reminderDateWindow.maxValue}
                        min={reminderDateWindow.minValue}
                        type="date"
                        value={reminderForm.dueDate}
                      />
                      <Input
                        onChange={(event) =>
                          setReminderForm((current) => ({
                            ...current,
                            message: event.target.value,
                          }))
                        }
                        placeholder="Reminder message"
                        value={reminderForm.message}
                      />
                    </div>
                    <div className="mt-3 space-y-2">
                      <p className="text-xs text-muted-foreground">{reminderDueDateHint}</p>
                      {reminderDueDateValidationMessage ? (
                        <div className="rounded-xl border border-rose-500/20 bg-rose-500/8 p-3 text-sm text-rose-700 dark:text-rose-300">
                          {reminderDueDateValidationMessage}
                        </div>
                      ) : null}
                    </div>
                    <div className="mt-3 flex justify-end">
                      <Button
                        disabled={
                          !reminderForm.message.trim() ||
                          !reminderForm.dueDate ||
                          Boolean(reminderDueDateValidationMessage) ||
                          busyAction === "create-reminder"
                        }
                        onClick={handleCreateReminder}
                        size="sm"
                      >
                        <BellRing className="h-3.5 w-3.5" />
                        Create Reminder
                      </Button>
                    </div>
                  </div>
                ) : null}

                <div className="space-y-2">
                  {sortedRfqReminders.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No reminders are currently attached to this RFQ.
                    </p>
                  ) : (
                    sortedRfqReminders.map((reminder) => (
                      <div key={reminder.id} className="stat-cell">
                        <div className="flex flex-wrap items-start justify-between gap-2">
                          <div>
                            <div className="text-sm font-medium text-foreground">
                              {reminder.message}
                            </div>
                            <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                              <Badge variant={reminderStatusTone[reminder.status] ?? "steel"}>
                                {reminder.status}
                              </Badge>
                              <Badge variant="outline">
                                {getReminderScopeLabel(reminder)}
                              </Badge>
                              <Badge variant="outline">{reminder.source}</Badge>
                              <Badge variant="outline">{getReminderTypeLabel(reminder.type)}</Badge>
                              <span>· due {reminder.dueLabel}</span>
                              {reminder.rfqStageName ? <span>· {reminder.rfqStageName}</span> : null}
                              {reminder.assignedTo ? ` · ${reminder.assignedTo}` : ""}
                              {reminder.delayDays > 0 ? ` · ${reminder.delayDays} day(s) late` : ""}
                              {reminder.sendCount > 0 ? ` · sent ${reminder.sendCount} time(s)` : ""}
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                              onClick={() => setSelectedReminder(reminder)}
                              size="sm"
                              variant="ghost"
                            >
                              View details
                            </Button>
                            {canManageReminders &&
                            reminder.status !== "resolved" &&
                            reminder.source === "manual" ? (
                              <Button
                                disabled={busyAction === `resolve-reminder:${reminder.id}`}
                                onClick={() => handleResolveReminder(reminder.id)}
                                size="sm"
                                variant="ghost"
                              >
                                Resolve
                              </Button>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
