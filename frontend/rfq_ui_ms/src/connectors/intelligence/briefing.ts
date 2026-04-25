import { apiConfig } from "@/config/api";
import { briefingResponses } from "@/demo/intelligence/briefing";
import { requestIntelligenceJson } from "@/connectors/intelligence/base";
import { HttpError } from "@/lib/http-client";
import type {
  IntelligenceArtifactEnvelope,
  IntelligenceBriefingContent,
} from "@/models/intelligence/api";
import type {
  BriefingArtifactModel,
} from "@/models/intelligence/briefing";
import {
  translateBriefing,
  translateLiveBriefing,
} from "@/translators/intelligence/briefing";
import { sleep } from "@/utils/async";

export async function getBriefingArtifact(
  rfqId: string,
): Promise<BriefingArtifactModel | null> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.7));
    const response = briefingResponses[rfqId];
    return response ? translateBriefing(response) : null;
  }

  try {
    const response = await requestIntelligenceJson<
      IntelligenceArtifactEnvelope<IntelligenceBriefingContent>
    >(`/rfqs/${rfqId}/briefing`);

    return translateLiveBriefing(response);
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }

    throw error;
  }
}
