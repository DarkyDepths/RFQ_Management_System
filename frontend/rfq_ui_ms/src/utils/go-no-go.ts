export const GO_NO_GO_FIELD_KEY = "go_nogo_decision" as const;
export const GO_NO_GO_VALUE_GO = "go" as const;
export const GO_NO_GO_VALUE_NO_GO = "no_go" as const;
export const DESIGN_APPROVED_FIELD_KEY = "design_approved" as const;
export const BOQ_COMPLETED_FIELD_KEY = "boq_completed" as const;
export const AUTO_BLOCKER_SOURCE_FIELD_KEY = "workflow_auto_blocker_source" as const;
export const YES_NO_VALUE_YES = "yes" as const;
export const YES_NO_VALUE_NO = "no" as const;

export const GO_NO_GO_OPTIONS = [
  { label: "Go", value: GO_NO_GO_VALUE_GO },
  { label: "No-Go", value: GO_NO_GO_VALUE_NO_GO },
] as const;
export const YES_NO_OPTIONS = [
  { label: "Yes", value: YES_NO_VALUE_YES },
  { label: "No", value: YES_NO_VALUE_NO },
] as const;

export type GoNoGoDecisionValue = (typeof GO_NO_GO_OPTIONS)[number]["value"];
export type YesNoDecisionValue = (typeof YES_NO_OPTIONS)[number]["value"];

export const GO_NO_GO_VALIDATION_MESSAGE =
  "Please choose Go or No-Go before continuing.";
export const DESIGN_APPROVED_VALIDATION_MESSAGE =
  "Please choose Yes or No for Design Approved before continuing.";
export const BOQ_COMPLETED_VALIDATION_MESSAGE =
  "Please choose Yes or No for BOQ Completed before continuing.";

export function isGoNoGoDecisionField(fieldKey: string) {
  return fieldKey.trim() === GO_NO_GO_FIELD_KEY;
}

export function isYesNoDecisionField(fieldKey: string) {
  const normalized = fieldKey.trim();
  return (
    normalized === DESIGN_APPROVED_FIELD_KEY ||
    normalized === BOQ_COMPLETED_FIELD_KEY
  );
}

export function isControlledStageDecisionField(fieldKey: string) {
  return isGoNoGoDecisionField(fieldKey) || isYesNoDecisionField(fieldKey);
}

export function normalizeAutoBlockerSourceField(
  value: string | null | undefined,
) {
  if (!value) {
    return "";
  }

  const normalized = value.trim();
  return isYesNoDecisionField(normalized) ? normalized : "";
}

export function isAutoBlockerSupportField(fieldKey: string) {
  return fieldKey.trim() === AUTO_BLOCKER_SOURCE_FIELD_KEY;
}

export function normalizeGoNoGoDecisionValue(
  value: string | null | undefined,
): GoNoGoDecisionValue | "" {
  if (!value) {
    return "";
  }

  const normalized = value.trim().toLowerCase().replace(/—/g, "-");
  if (!normalized) {
    return "";
  }

  if (normalized === "proceed" || normalized.startsWith("go")) {
    return GO_NO_GO_VALUE_GO;
  }

  if (
    normalized === "no_go" ||
    normalized === "no-go" ||
    normalized === "no go" ||
    normalized === "nogo" ||
    normalized.startsWith("no-go") ||
    normalized.startsWith("no go") ||
    normalized.startsWith("no_go")
  ) {
    return GO_NO_GO_VALUE_NO_GO;
  }

  return "";
}

export function normalizeYesNoDecisionValue(
  value: string | boolean | null | undefined,
): YesNoDecisionValue | "" {
  if (typeof value === "boolean") {
    return value ? YES_NO_VALUE_YES : YES_NO_VALUE_NO;
  }

  if (!value) {
    return "";
  }

  const normalized = value.trim().toLowerCase().replace(/—/g, "-");
  if (!normalized) {
    return "";
  }

  if (
    normalized === "yes" ||
    normalized === "y" ||
    normalized === "true" ||
    normalized.startsWith("yes") ||
    normalized.startsWith("approved") ||
    normalized.startsWith("completed")
  ) {
    return YES_NO_VALUE_YES;
  }

  if (
    normalized === "no" ||
    normalized === "n" ||
    normalized === "false" ||
    normalized.startsWith("no") ||
    normalized.startsWith("not approved") ||
    normalized.startsWith("not completed")
  ) {
    return YES_NO_VALUE_NO;
  }

  return YES_NO_VALUE_YES;
}

export function normalizeControlledStageDecisionValue(
  fieldKey: string,
  value: string | boolean | null | undefined,
) {
  if (isGoNoGoDecisionField(fieldKey)) {
    return normalizeGoNoGoDecisionValue(
      typeof value === "string" ? value : value == null ? value : String(value),
    );
  }

  if (isYesNoDecisionField(fieldKey)) {
    return normalizeYesNoDecisionValue(value);
  }

  return typeof value === "string" ? value : value == null ? "" : String(value);
}

export function getControlledStageDecisionOptions(fieldKey: string) {
  if (isGoNoGoDecisionField(fieldKey)) {
    return GO_NO_GO_OPTIONS;
  }

  if (isYesNoDecisionField(fieldKey)) {
    return YES_NO_OPTIONS;
  }

  return null;
}

export function getControlledStageDecisionPlaceholder(fieldKey: string) {
  if (isGoNoGoDecisionField(fieldKey)) {
    return "Choose Go or No-Go";
  }

  if (isYesNoDecisionField(fieldKey)) {
    return "Choose Yes or No";
  }

  return "Choose an option";
}

export function isNegativeAutoBlockingDecision(
  fieldKey: string,
  value: string | null | undefined,
) {
  const trimmedFieldKey = fieldKey.trim();
  if (trimmedFieldKey === GO_NO_GO_FIELD_KEY) {
    return false;
  }

  if (!isYesNoDecisionField(trimmedFieldKey)) {
    return false;
  }

  return normalizeYesNoDecisionValue(value) === YES_NO_VALUE_NO;
}

export function getGoNoGoValidationMessage(missingMandatoryFields: string[]) {
  return missingMandatoryFields.includes(GO_NO_GO_FIELD_KEY)
    ? GO_NO_GO_VALIDATION_MESSAGE
    : null;
}

export function getControlledStageDecisionValidationMessage(
  missingMandatoryFields: string[],
) {
  if (missingMandatoryFields.includes(GO_NO_GO_FIELD_KEY)) {
    return GO_NO_GO_VALIDATION_MESSAGE;
  }

  if (missingMandatoryFields.includes(DESIGN_APPROVED_FIELD_KEY)) {
    return DESIGN_APPROVED_VALIDATION_MESSAGE;
  }

  if (missingMandatoryFields.includes(BOQ_COMPLETED_FIELD_KEY)) {
    return BOQ_COMPLETED_VALIDATION_MESSAGE;
  }

  return null;
}

export function getNegativeDecisionBlockerReasonMessage(fieldKey: string) {
  if (fieldKey.trim() === DESIGN_APPROVED_FIELD_KEY) {
    return "Please choose a blocker reason when Design Approved is set to No.";
  }

  if (fieldKey.trim() === BOQ_COMPLETED_FIELD_KEY) {
    return "Please choose a blocker reason when BOQ Completed is set to No.";
  }

  return "Please choose a blocker reason when this stage decision is set to No.";
}

export function getAutoBlockingDecisionSource(
  capturedData: Record<string, string> | null | undefined,
) {
  if (!capturedData) {
    return "";
  }

  return normalizeAutoBlockerSourceField(capturedData[AUTO_BLOCKER_SOURCE_FIELD_KEY]);
}

export function getCapturedFieldLabel(fieldKey: string) {
  if (isGoNoGoDecisionField(fieldKey)) {
    return "Go / No-Go";
  }

  if (fieldKey.trim() === "rfq_terminal_outcome") {
    return "Terminal Outcome";
  }

  if (fieldKey.trim() === "rfq_lost_reason_code") {
    return "Lost Reason";
  }

  if (fieldKey.trim() === "rfq_lost_reason_other") {
    return "Lost Reason Detail";
  }

  if (fieldKey.trim() === "estimation_completed") {
    return "Estimation Amount";
  }

  if (fieldKey.trim() === "final_price") {
    return "Final Price";
  }

  if (fieldKey.trim() === "approval_signature") {
    return "Approval Reference";
  }

  if (fieldKey.trim() === DESIGN_APPROVED_FIELD_KEY) {
    return "Design Approved";
  }

  if (fieldKey.trim() === BOQ_COMPLETED_FIELD_KEY) {
    return "BOQ Completed";
  }

  return fieldKey
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}
