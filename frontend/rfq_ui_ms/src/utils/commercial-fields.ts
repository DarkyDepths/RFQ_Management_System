export const ESTIMATION_COMPLETED_FIELD_KEY = "estimation_completed" as const;
export const ESTIMATION_AMOUNT_FIELD_KEY = "estimation_amount" as const;
export const ESTIMATION_CURRENCY_FIELD_KEY = "estimation_currency" as const;
export const FINAL_PRICE_FIELD_KEY = "final_price" as const;
export const FINAL_PRICE_CURRENCY_FIELD_KEY = "final_price_currency" as const;
export const APPROVAL_SIGNATURE_FIELD_KEY = "approval_signature" as const;
export const DEFAULT_CURRENCY_CODE = "SAR" as const;

export const ESTIMATION_AMOUNT_VALIDATION_MESSAGE =
  "Please enter a valid numeric estimation amount before continuing.";
export const FINAL_PRICE_VALIDATION_MESSAGE =
  "Please enter a valid numeric final price before continuing.";
export const APPROVAL_SIGNATURE_VALIDATION_MESSAGE =
  "Please enter the internal approval reference or sign-off code before continuing.";

export const CURRENCY_OPTIONS = [
  { code: "SAR", label: "Saudi Riyal" },
  { code: "USD", label: "US Dollar" },
  { code: "EUR", label: "Euro" },
  { code: "AED", label: "UAE Dirham" },
  { code: "GBP", label: "British Pound" },
] as const;

type CommercialFieldKey =
  | typeof ESTIMATION_COMPLETED_FIELD_KEY
  | typeof FINAL_PRICE_FIELD_KEY;

const COMMERCIAL_FIELD_CONFIG = {
  [ESTIMATION_COMPLETED_FIELD_KEY]: {
    amountKey: ESTIMATION_AMOUNT_FIELD_KEY,
    currencyKey: ESTIMATION_CURRENCY_FIELD_KEY,
    label: "Estimation Amount",
    helpText:
      "Record the structured commercial estimate for this stage with an amount and currency.",
    amountPlaceholder: "Enter estimation amount",
    validationMessage: ESTIMATION_AMOUNT_VALIDATION_MESSAGE,
  },
  [FINAL_PRICE_FIELD_KEY]: {
    amountKey: FINAL_PRICE_FIELD_KEY,
    currencyKey: FINAL_PRICE_CURRENCY_FIELD_KEY,
    label: "Final Price",
    helpText:
      "Record the final submitted commercial amount for this stage with an amount and currency.",
    amountPlaceholder: "Enter final price",
    validationMessage: FINAL_PRICE_VALIDATION_MESSAGE,
  },
} as const satisfies Record<
  CommercialFieldKey,
  {
    amountKey: string;
    currencyKey: string;
    label: string;
    helpText: string;
    amountPlaceholder: string;
    validationMessage: string;
  }
>;

export function isCommercialStageField(
  fieldKey: string,
): fieldKey is CommercialFieldKey {
  const normalized = fieldKey.trim();
  return (
    normalized === ESTIMATION_COMPLETED_FIELD_KEY ||
    normalized === FINAL_PRICE_FIELD_KEY
  );
}

export function isApprovalSignatureField(fieldKey: string) {
  return fieldKey.trim() === APPROVAL_SIGNATURE_FIELD_KEY;
}

export function isManagedStageSupportField(fieldKey: string) {
  const normalized = fieldKey.trim();
  return (
    normalized === ESTIMATION_AMOUNT_FIELD_KEY ||
    normalized === ESTIMATION_CURRENCY_FIELD_KEY ||
    normalized === FINAL_PRICE_CURRENCY_FIELD_KEY
  );
}

export function getManagedStageSupportFieldOwnerLabel(fieldKey: string) {
  const normalized = fieldKey.trim();
  if (
    normalized === ESTIMATION_AMOUNT_FIELD_KEY ||
    normalized === ESTIMATION_CURRENCY_FIELD_KEY
  ) {
    return COMMERCIAL_FIELD_CONFIG[ESTIMATION_COMPLETED_FIELD_KEY].label;
  }

  if (normalized === FINAL_PRICE_CURRENCY_FIELD_KEY) {
    return COMMERCIAL_FIELD_CONFIG[FINAL_PRICE_FIELD_KEY].label;
  }

  return "this workflow field";
}

export function getCommercialFieldLabel(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return null;
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey].label;
}

export function getCommercialFieldHelpText(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return null;
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey].helpText;
}

export function getCommercialFieldAmountPlaceholder(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return "Enter amount";
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey]
    .amountPlaceholder;
}

export function getCommercialFieldValidationMessage(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return null;
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey]
    .validationMessage;
}

export function getCommercialFieldAmountKey(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return fieldKey.trim();
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey].amountKey;
}

export function getCommercialFieldCurrencyKey(fieldKey: string) {
  if (!isCommercialStageField(fieldKey)) {
    return null;
  }

  return COMMERCIAL_FIELD_CONFIG[fieldKey.trim() as CommercialFieldKey]
    .currencyKey;
}

export function getCommercialFieldAmountValue(
  capturedData: Record<string, string>,
  fieldKey: string,
) {
  if (!isCommercialStageField(fieldKey)) {
    return "";
  }

  const amountKey = getCommercialFieldAmountKey(fieldKey);
  return capturedData[amountKey]?.trim() ?? "";
}

export function getCommercialFieldCurrencyValue(
  capturedData: Record<string, string>,
  fieldKey: string,
) {
  if (!isCommercialStageField(fieldKey)) {
    return DEFAULT_CURRENCY_CODE;
  }

  const currencyKey = getCommercialFieldCurrencyKey(fieldKey);
  const normalized = currencyKey
    ? capturedData[currencyKey]?.trim().toUpperCase() ?? ""
    : "";

  if (!normalized) {
    return DEFAULT_CURRENCY_CODE;
  }

  return CURRENCY_OPTIONS.some((option) => option.code === normalized)
    ? normalized
    : DEFAULT_CURRENCY_CODE;
}

export function isCommercialFieldSatisfied(
  capturedData: Record<string, string>,
  fieldKey: string,
) {
  return Boolean(getCommercialFieldAmountValue(capturedData, fieldKey));
}

export function getCommercialFieldNumericValidationError(
  capturedData: Record<string, string>,
  fieldKey: string,
) {
  if (!isCommercialStageField(fieldKey)) {
    return null;
  }

  const amount = getCommercialFieldAmountValue(capturedData, fieldKey);
  if (!amount) {
    return getCommercialFieldValidationMessage(fieldKey);
  }

  const normalized = amount.replace(/,/g, "").trim();
  const numeric = Number(normalized);
  if (!Number.isFinite(numeric) || numeric < 0) {
    return getCommercialFieldValidationMessage(fieldKey);
  }

  return null;
}

export function getApprovalSignatureLabel() {
  return "Approval Reference";
}

export function getApprovalSignatureHelpText() {
  return "Enter the internal approval sign-off or reference code used to record commercial approval, for example APP-4481.";
}

export function getApprovalSignaturePlaceholder() {
  return "Enter approval sign-off code";
}
