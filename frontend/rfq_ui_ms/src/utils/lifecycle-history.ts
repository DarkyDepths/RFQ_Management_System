import type { StageLifecycleEventModel } from "@/models/manager/stage";
import {
  DEFAULT_CURRENCY_CODE,
  ESTIMATION_COMPLETED_FIELD_KEY,
  FINAL_PRICE_FIELD_KEY,
  getCommercialFieldAmountValue,
  getCommercialFieldCurrencyValue,
  isCommercialStageField,
  isManagedStageSupportField,
} from "@/utils/commercial-fields";
import {
  getCapturedFieldLabel,
  getControlledStageDecisionOptions,
  isAutoBlockerSupportField,
  isControlledStageDecisionField,
} from "@/utils/go-no-go";
import {
  getLostReasonLabel,
  getTerminalOutcomeLabel,
  isLostReasonCodeField,
  isTerminalOutcomeField,
} from "@/utils/terminal-outcome";
import {
  formatCommercialAmountWithCurrency,
  formatDateTime,
} from "@/utils/format";

export const LIFECYCLE_HISTORY_EVENTS_FIELD_KEY = "workflow_history_events" as const;

export type HistoryCapturedEntry = {
  key: string;
  label: string;
  value: string;
};

type LifecycleHistoryEventTone = StageLifecycleEventModel["tone"];

function normalizeLifecycleEventType(
  value: unknown,
): StageLifecycleEventModel["type"] | null {
  switch (value) {
    case "decision_recorded":
    case "blocker_created":
    case "blocker_updated":
    case "blocker_resolved":
    case "terminal_outcome_recorded":
      return value;
    default:
      return null;
  }
}

function normalizeLifecycleEventSource(
  value: unknown,
): StageLifecycleEventModel["source"] | undefined {
  if (value === "automatic" || value === "manual") {
    return value;
  }

  return undefined;
}

function getLifecycleEventFieldLabel(fieldKey: string | undefined) {
  return fieldKey ? getCapturedFieldLabel(fieldKey) : undefined;
}

function getLifecycleEventValueLabel(
  fieldKey: string | undefined,
  value: string | undefined,
) {
  if (!fieldKey || !value) {
    return undefined;
  }

  if (isControlledStageDecisionField(fieldKey)) {
    return (
      getControlledStageDecisionOptions(fieldKey)?.find(
        (option) => option.value === value,
      )?.label ?? value
    );
  }

  if (isTerminalOutcomeField(fieldKey)) {
    return getTerminalOutcomeLabel(value) ?? value;
  }

  if (isLostReasonCodeField(fieldKey)) {
    return getLostReasonLabel(value) ?? value;
  }

  return value;
}

function resolveLifecycleEventTone(
  eventType: StageLifecycleEventModel["type"],
  value?: string,
): LifecycleHistoryEventTone {
  switch (eventType) {
    case "blocker_created":
    case "blocker_updated":
      return "amber";
    case "blocker_resolved":
      return "emerald";
    case "terminal_outcome_recorded":
      return value === "lost" ? "rose" : "emerald";
    case "decision_recorded":
    default:
      return "steel";
  }
}

function buildLifecycleEventTitle(
  eventType: StageLifecycleEventModel["type"],
  fieldLabel?: string,
  source?: StageLifecycleEventModel["source"],
) {
  switch (eventType) {
    case "blocker_created":
      return fieldLabel
        ? `Blocker created from ${fieldLabel}`
        : `${source === "automatic" ? "Automatic" : "Manual"} blocker created`;
    case "blocker_updated":
      return "Blocker updated";
    case "blocker_resolved":
      return "Blocker resolved";
    case "terminal_outcome_recorded":
      return "Terminal outcome recorded";
    case "decision_recorded":
    default:
      return fieldLabel ? `${fieldLabel} recorded` : "Decision recorded";
  }
}

function buildLifecycleEventSummary(
  eventType: StageLifecycleEventModel["type"],
  {
    fieldLabel,
    valueLabel,
    reason,
    source,
    detail,
  }: {
    fieldLabel?: string;
    valueLabel?: string;
    reason?: string;
    source?: StageLifecycleEventModel["source"];
    detail?: string;
  },
) {
  switch (eventType) {
    case "blocker_created":
      return `${source === "automatic" ? "Automatic" : "Manual"} blocker${reason ? ` — ${reason}` : ""}`;
    case "blocker_updated":
      return reason ? `Blocker reason updated to ${reason}` : "Blocker reason updated.";
    case "blocker_resolved":
      return reason ? `Resolved after ${reason}` : "Blocker resolved.";
    case "terminal_outcome_recorded":
      return reason
        ? `${valueLabel ?? "Outcome recorded"} — ${reason}`
        : `${valueLabel ?? "Outcome recorded"}`;
    case "decision_recorded":
    default: {
      const detailSuffix = detail ? ` — ${detail}` : "";
      if (fieldLabel && valueLabel) {
        return `${fieldLabel}: ${valueLabel}${detailSuffix}`;
      }
      if (valueLabel) {
        return `${valueLabel}${detailSuffix}`;
      }
      return detail ? `Recorded — ${detail}` : "Recorded.";
    }
  }
}

function formatHistoryCapturedValue(
  key: string,
  value: string,
  capturedData: Record<string, string>,
) {
  if (isControlledStageDecisionField(key)) {
    return (
      getControlledStageDecisionOptions(key)?.find((option) => option.value === value)
        ?.label ?? value
    );
  }

  if (isTerminalOutcomeField(key)) {
    return getTerminalOutcomeLabel(value) ?? value;
  }

  if (isLostReasonCodeField(key)) {
    return getLostReasonLabel(value) ?? value;
  }

  if (isCommercialStageField(key)) {
    const amount = getCommercialFieldAmountValue(capturedData, key);
    if (!amount) {
      return value;
    }

    return formatCommercialAmountWithCurrency(
      amount,
      getCommercialFieldCurrencyValue(capturedData, key) || DEFAULT_CURRENCY_CODE,
    );
  }

  return value;
}

function isHiddenHistoryCapturedField(fieldKey: string) {
  return (
    isLifecycleHistorySupportField(fieldKey) ||
    isAutoBlockerSupportField(fieldKey) ||
    isManagedStageSupportField(fieldKey)
  );
}

export function isLifecycleHistorySupportField(fieldKey: string) {
  return fieldKey.trim() === LIFECYCLE_HISTORY_EVENTS_FIELD_KEY;
}

export function buildLifecycleHistoryCapturedEntries(
  capturedData: Record<string, string>,
): HistoryCapturedEntry[] {
  const entries: HistoryCapturedEntry[] = [];

  const estimationAmount = getCommercialFieldAmountValue(
    capturedData,
    ESTIMATION_COMPLETED_FIELD_KEY,
  );
  if (estimationAmount) {
    entries.push({
      key: ESTIMATION_COMPLETED_FIELD_KEY,
      label: getCapturedFieldLabel(ESTIMATION_COMPLETED_FIELD_KEY),
      value: formatCommercialAmountWithCurrency(
        estimationAmount,
        getCommercialFieldCurrencyValue(
          capturedData,
          ESTIMATION_COMPLETED_FIELD_KEY,
        ),
      ),
    });
  }

  const finalPriceAmount = getCommercialFieldAmountValue(
    capturedData,
    FINAL_PRICE_FIELD_KEY,
  );
  if (finalPriceAmount) {
    entries.push({
      key: FINAL_PRICE_FIELD_KEY,
      label: getCapturedFieldLabel(FINAL_PRICE_FIELD_KEY),
      value: formatCommercialAmountWithCurrency(
        finalPriceAmount,
        getCommercialFieldCurrencyValue(capturedData, FINAL_PRICE_FIELD_KEY),
      ),
    });
  }

  Object.entries(capturedData).forEach(([key, value]) => {
    const trimmedValue = value.trim();
    if (!trimmedValue) {
      return;
    }

    if (
      isHiddenHistoryCapturedField(key) ||
      key === ESTIMATION_COMPLETED_FIELD_KEY ||
      key === FINAL_PRICE_FIELD_KEY
    ) {
      return;
    }

    entries.push({
      key,
      label: getCapturedFieldLabel(key),
      value: formatHistoryCapturedValue(key, trimmedValue, capturedData),
    });
  });

  return entries;
}

export function parseLifecycleHistoryEvents(
  raw: unknown,
): StageLifecycleEventModel[] {
  if (!Array.isArray(raw)) {
    return [];
  }

  const parsedEvents: Array<StageLifecycleEventModel | null> = raw.map((item, index) => {
      if (!item || typeof item !== "object") {
        return null;
      }

      const event = item as Record<string, unknown>;
      const type = normalizeLifecycleEventType(event.type);
      if (!type) {
        return null;
      }

      const fieldKey =
        typeof event.field_key === "string" ? event.field_key : undefined;
      const value = typeof event.value === "string" ? event.value : undefined;
      const reason = typeof event.reason === "string" ? event.reason : undefined;
      const detail = typeof event.detail === "string" ? event.detail : undefined;
      const fieldLabel = getLifecycleEventFieldLabel(fieldKey);
      const valueLabel = getLifecycleEventValueLabel(fieldKey, value);
      const source = normalizeLifecycleEventSource(event.source);

      return {
        id:
          typeof event.id === "string" && event.id.trim()
            ? event.id
            : `history-event:${index}`,
        type,
        timestampValue:
          typeof event.at === "string" && event.at.trim() ? event.at : undefined,
        timestampLabel:
          typeof event.at === "string" && event.at.trim()
            ? formatDateTime(event.at)
            : "Pending",
        actorName:
          typeof event.actor_name === "string" ? event.actor_name : undefined,
        fieldKey,
        fieldLabel,
        value,
        valueLabel,
        reason,
        detail,
        source,
        title: buildLifecycleEventTitle(type, fieldLabel, source),
        summary: buildLifecycleEventSummary(type, {
          detail,
          fieldLabel,
          reason,
          source,
          valueLabel,
        }),
        tone: resolveLifecycleEventTone(type, value),
      };
    });

  return parsedEvents
    .filter((event): event is StageLifecycleEventModel => event !== null)
    .sort((left, right) => {
      const leftTimestamp = left.timestampValue ?? "";
      const rightTimestamp = right.timestampValue ?? "";
      return leftTimestamp.localeCompare(rightTimestamp);
    });
}
