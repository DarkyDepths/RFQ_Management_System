export type CapturedFieldEntry = {
  id: string;
  key: string;
  value: string;
};

export type CapturedFieldState = {
  entries: CapturedFieldEntry[];
  showAdditionalSection: boolean;
};

function isManagedStageSupportField(fieldKey: string) {
  const normalized = fieldKey.trim();
  return (
    normalized === "estimation_amount" ||
    normalized === "estimation_currency" ||
    normalized === "final_price_currency"
  );
}

let nextCapturedFieldDraftId = 0;

function buildPersistedCapturedFieldId(key: string) {
  return `captured:${key}`;
}

export function createEmptyCapturedFieldEntry(): CapturedFieldEntry {
  nextCapturedFieldDraftId += 1;
  return {
    id: `draft:${nextCapturedFieldDraftId}`,
    key: "",
    value: "",
  };
}

export function buildCapturedFieldEntries(
  capturedData: Record<string, string>,
  mandatoryFields: string[],
): CapturedFieldEntry[] {
  const keys = Array.from(new Set([...mandatoryFields, ...Object.keys(capturedData)]));
  return keys.map((key) => ({
    id: buildPersistedCapturedFieldId(key),
    key,
    value: capturedData[key] ?? "",
  }));
}

export function buildCapturedData(entries: CapturedFieldEntry[]) {
  return entries.reduce<Record<string, string>>((accumulator, entry) => {
    const key = entry.key.trim();
    if (!key) {
      return accumulator;
    }

    accumulator[key] = entry.value;
    return accumulator;
  }, {});
}

export function hasVisibleCapturedFieldEntries(entries: CapturedFieldEntry[]) {
  return entries.some((entry) => entry.key.trim() || entry.value.trim());
}

export function buildCapturedFieldState(
  capturedData: Record<string, string>,
  mandatoryFields: string[],
): CapturedFieldState {
  const entries = buildCapturedFieldEntries(capturedData, mandatoryFields);
  const mandatoryFieldSet = new Set(mandatoryFields);
  const additionalEntries = entries.filter((entry) => {
    const trimmedKey = entry.key.trim();
    return (
      (!trimmedKey || !mandatoryFieldSet.has(trimmedKey)) &&
      !isManagedStageSupportField(trimmedKey)
    );
  });

  return {
    entries,
    showAdditionalSection:
      additionalEntries.length > 0 || hasVisibleCapturedFieldEntries(additionalEntries),
  };
}
