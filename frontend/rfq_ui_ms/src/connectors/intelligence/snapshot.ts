import { apiConfig } from "@/config/api";
import { intelligencePortfolioResponse, snapshotResponses } from "@/demo/intelligence/snapshot";
import { requestIntelligenceJson } from "@/connectors/intelligence/base";
import { HttpError } from "@/lib/http-client";
import type {
  IntelligenceArtifactEnvelope,
  IntelligenceSnapshotContent,
} from "@/models/intelligence/api";
import type {
  IntelligenceSnapshotModel,
} from "@/models/intelligence/snapshot";
import type { IntelligencePortfolioModel } from "@/models/ui/dashboard";
import {
  translateLiveSnapshot,
  translatePortfolioSummary,
  translateSnapshot,
} from "@/translators/intelligence/snapshot";
import { sleep } from "@/utils/async";

export async function getIntelligencePortfolioSummary(): Promise<IntelligencePortfolioModel> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.6));
    return translatePortfolioSummary(intelligencePortfolioResponse);
  }

  throw new Error(
    "Portfolio intelligence is not connected in live mode for this phase.",
  );
}

export async function getIntelligenceSnapshot(
  rfqId: string,
): Promise<IntelligenceSnapshotModel | null> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.85));
    const response = snapshotResponses[rfqId];
    return response ? translateSnapshot(response) : null;
  }

  try {
    const response = await requestIntelligenceJson<
      IntelligenceArtifactEnvelope<IntelligenceSnapshotContent>
    >(`/rfqs/${rfqId}/snapshot`);

    return translateLiveSnapshot(response);
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }

    throw error;
  }
}
