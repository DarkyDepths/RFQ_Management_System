import { apiConfig } from "@/config/api";
import { requestIntelligenceJson } from "@/connectors/intelligence/base";
import type {
  IntelligenceLifecycleTriggerResult,
  TriggerOutcomeInput,
  TriggerWorkbookInput,
} from "@/models/intelligence/triggers";
import { sleep } from "@/utils/async";

function buildDemoTriggerResult(
  eventType: string,
  rfqId: string,
): IntelligenceLifecycleTriggerResult {
  return {
    status: "processed",
    eventId: `demo:${eventType}:${rfqId}`,
    eventType,
    rfqId,
  };
}

export async function triggerIntelligenceIntake(
  rfqId: string,
): Promise<IntelligenceLifecycleTriggerResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.45));
    return buildDemoTriggerResult("rfq.created", rfqId);
  }

  const response = await requestIntelligenceJson<{
    status: string;
    event_id?: string;
    event_type?: string;
    rfq_id?: string;
    reason?: string;
    artifacts?: Record<string, { id?: string | null; status?: string | null; version?: number | null }>;
  }>(`/rfqs/${rfqId}/trigger/intake`, {
    method: "POST",
  });

  return {
    status: response.status,
    eventId: response.event_id,
    eventType: response.event_type,
    rfqId: response.rfq_id,
    reason: response.reason,
    artifacts: response.artifacts,
  };
}

export async function triggerIntelligenceWorkbook(
  rfqId: string,
  input?: TriggerWorkbookInput,
): Promise<IntelligenceLifecycleTriggerResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.5));
    return buildDemoTriggerResult("workbook.uploaded", rfqId);
  }

  const response = await requestIntelligenceJson<{
    status: string;
    event_id?: string;
    event_type?: string;
    rfq_id?: string;
    reason?: string;
    artifacts?: Record<string, { id?: string | null; status?: string | null; version?: number | null }>;
  }>(`/rfqs/${rfqId}/trigger/workbook`, {
    method: "POST",
    body: JSON.stringify({
      workbook_ref: input?.workbookRef,
      workbook_filename: input?.workbookFilename,
      uploaded_at: input?.uploadedAt,
    }),
  });

  return {
    status: response.status,
    eventId: response.event_id,
    eventType: response.event_type,
    rfqId: response.rfq_id,
    reason: response.reason,
    artifacts: response.artifacts,
  };
}

export async function triggerIntelligenceOutcome(
  rfqId: string,
  input: TriggerOutcomeInput,
): Promise<IntelligenceLifecycleTriggerResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.5));
    return buildDemoTriggerResult("outcome.recorded", rfqId);
  }

  const response = await requestIntelligenceJson<{
    status: string;
    event_id?: string;
    event_type?: string;
    rfq_id?: string;
    reason?: string;
    artifacts?: Record<string, { id?: string | null; status?: string | null; version?: number | null }>;
  }>(`/rfqs/${rfqId}/trigger/outcome`, {
    method: "POST",
    body: JSON.stringify({
      outcome: input.outcome,
      outcome_reason: input.outcomeReason,
      recorded_at: input.recordedAt,
    }),
  });

  return {
    status: response.status,
    eventId: response.event_id,
    eventType: response.event_type,
    rfqId: response.rfq_id,
    reason: response.reason,
    artifacts: response.artifacts,
  };
}
