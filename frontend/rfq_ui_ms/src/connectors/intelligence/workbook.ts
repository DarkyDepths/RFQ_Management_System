import { apiConfig } from "@/config/api";
import {
  workbookProfileResponses,
  workbookReviewResponses,
} from "@/demo/intelligence/workbook";
import { requestIntelligenceJson } from "@/connectors/intelligence/base";
import { HttpError } from "@/lib/http-client";
import type {
  IntelligenceArtifactEnvelope,
  IntelligenceWorkbookProfileContent,
  IntelligenceWorkbookReviewContent,
} from "@/models/intelligence/api";
import type {
  WorkbookProfileModel,
  WorkbookReviewModel,
} from "@/models/intelligence/workbook";
import {
  translateLiveWorkbookProfile,
  translateLiveWorkbookReview,
  translateWorkbookProfile,
  translateWorkbookReview,
} from "@/translators/intelligence/workbook";
import { sleep } from "@/utils/async";

export async function getWorkbookProfile(
  rfqId: string,
): Promise<WorkbookProfileModel | null> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.72));
    const response = workbookProfileResponses[rfqId];
    return response ? translateWorkbookProfile(response) : null;
  }

  try {
    const response = await requestIntelligenceJson<
      IntelligenceArtifactEnvelope<IntelligenceWorkbookProfileContent>
    >(`/rfqs/${rfqId}/workbook-profile`);

    return translateLiveWorkbookProfile(response);
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }

    throw error;
  }
}

export async function getWorkbookReview(
  rfqId: string,
): Promise<WorkbookReviewModel | null> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.9));
    const response = workbookReviewResponses[rfqId];
    return response ? translateWorkbookReview(response) : null;
  }

  try {
    const response = await requestIntelligenceJson<
      IntelligenceArtifactEnvelope<IntelligenceWorkbookReviewContent>
    >(`/rfqs/${rfqId}/workbook-review`);

    return translateLiveWorkbookReview(response);
  } catch (error) {
    if (error instanceof HttpError && error.status === 404) {
      return null;
    }

    throw error;
  }
}
