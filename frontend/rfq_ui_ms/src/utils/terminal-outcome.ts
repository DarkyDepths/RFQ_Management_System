export const TERMINAL_OUTCOME_FIELD_KEY = "rfq_terminal_outcome" as const;
export const TERMINAL_OUTCOME_AWARDED = "awarded" as const;
export const TERMINAL_OUTCOME_LOST = "lost" as const;
export const TERMINAL_OUTCOME_VALIDATION_MESSAGE =
  "Please choose Awarded or Lost before completing this RFQ.";
export const LOST_REASON_CODE_FIELD_KEY = "rfq_lost_reason_code" as const;
export const LOST_REASON_REQUIRED_MESSAGE =
  "Please choose a lost reason before completing this RFQ as Lost.";
export const LOST_REASON_OTHER_VALUE = "other" as const;
export const LOST_REASON_OTHER_DETAIL_FIELD_KEY = "rfq_lost_reason_other" as const;
export const LOST_REASON_OTHER_REQUIRED_MESSAGE =
  "Please enter the lost reason details when Other is selected.";

export const TERMINAL_OUTCOME_OPTIONS = [
  { label: "Awarded", value: TERMINAL_OUTCOME_AWARDED },
  { label: "Lost", value: TERMINAL_OUTCOME_LOST },
] as const;

export const LOST_REASON_OPTIONS = [
  { label: "Commercial competitiveness", value: "commercial_gap" },
  { label: "Technical non-compliance", value: "technical_gap" },
  { label: "Delivery / schedule", value: "delivery_schedule" },
  { label: "Scope misalignment", value: "scope_misalignment" },
  { label: "Client strategy change", value: "client_strategy_change" },
  { label: "No feedback received", value: "no_feedback" },
  { label: "Other", value: LOST_REASON_OTHER_VALUE },
] as const;

export type TerminalOutcomeValue =
  (typeof TERMINAL_OUTCOME_OPTIONS)[number]["value"];
export type LostReasonCode =
  (typeof LOST_REASON_OPTIONS)[number]["value"];

export function isTerminalOutcomeField(fieldKey: string) {
  return fieldKey.trim() === TERMINAL_OUTCOME_FIELD_KEY;
}

export function isLostReasonCodeField(fieldKey: string) {
  return fieldKey.trim() === LOST_REASON_CODE_FIELD_KEY;
}

export function isTerminalOutcomeSupportField(fieldKey: string) {
  return (
    isTerminalOutcomeField(fieldKey) ||
    isLostReasonCodeField(fieldKey) ||
    fieldKey.trim() === LOST_REASON_OTHER_DETAIL_FIELD_KEY
  );
}

export function normalizeTerminalOutcomeValue(
  value: string | null | undefined,
): TerminalOutcomeValue | "" {
  if (!value) {
    return "";
  }

  const normalized = value.trim().toLowerCase().replace(/—/g, "-");
  if (!normalized) {
    return "";
  }

  if (normalized === "awarded" || normalized === "award" || normalized === "won") {
    return TERMINAL_OUTCOME_AWARDED;
  }

  if (normalized === "lost" || normalized === "loss") {
    return TERMINAL_OUTCOME_LOST;
  }

  return "";
}

export function normalizeLostReasonCode(
  value: string | null | undefined,
): LostReasonCode | "" {
  if (!value) {
    return "";
  }

  const normalized = value.trim().toLowerCase().replace(/-/g, "_").replace(/\s+/g, "_");
  if (!normalized) {
    return "";
  }

  const directMatch = LOST_REASON_OPTIONS.find((option) => option.value === normalized);
  if (directMatch) {
    return directMatch.value;
  }

  const labelMatch = LOST_REASON_OPTIONS.find(
    (option) =>
      option.label.toLowerCase().replace(/\//g, " ").replace(/\s+/g, "_") ===
      normalized,
  );
  return labelMatch?.value ?? "";
}

export function getTerminalOutcomeLabel(
  value: string | null | undefined,
) {
  const normalizedValue = normalizeTerminalOutcomeValue(value);
  return (
    TERMINAL_OUTCOME_OPTIONS.find((option) => option.value === normalizedValue)?.label ??
    null
  );
}

export function getLostReasonLabel(value: string | null | undefined) {
  const normalizedValue = normalizeLostReasonCode(value);
  return (
    LOST_REASON_OPTIONS.find((option) => option.value === normalizedValue)?.label ??
    null
  );
}

export function getTerminalOutcomeHelpText() {
  return "Record the final business outcome here before closing the workflow stage.";
}

export function getLostReasonHelpText() {
  return "A lost RFQ must keep a clear reason for the final business outcome. Choose Other when the listed reasons do not fit.";
}

export function getTerminalOutcomeManagedFieldOwnerLabel() {
  return "Terminal outcome handling";
}
