import { apiConfig } from "@/config/api";
import { artifactResponses } from "@/demo/intelligence/artifacts";
import { requestIntelligenceJson } from "@/connectors/intelligence/base";
import type {
  IntelligenceArtifactIndexResponse,
  IntelligenceReprocessResponse,
} from "@/models/intelligence/api";
import type {
  ArtifactModel,
  ReprocessKind,
  ReprocessResult,
} from "@/models/intelligence/artifacts";
import {
  translateArtifact,
  translateLiveArtifactSummary,
} from "@/translators/intelligence/artifacts";
import { sleep } from "@/utils/async";

export async function getArtifactCatalog(
  rfqId: string,
): Promise<ArtifactModel[]> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.65));
    return (artifactResponses[rfqId] ?? []).map(translateArtifact);
  }

  const response = await requestIntelligenceJson<IntelligenceArtifactIndexResponse>(
    `/rfqs/${rfqId}/artifacts`,
  );

  return response.artifacts.map(translateLiveArtifactSummary);
}

export async function requestArtifactReprocess(
  rfqId: string,
  kind: ReprocessKind,
): Promise<ReprocessResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.5));
    return {
      kind,
      accepted: true,
      message: `${kind} reprocess queued in demo mode.`,
      status: "accepted",
    };
  }

  const response = await requestIntelligenceJson<IntelligenceReprocessResponse>(
    `/rfqs/${rfqId}/reprocess/${kind}`,
    {
      method: "POST",
    },
  );

  return {
    kind,
    accepted: response.status === "accepted",
    message:
      response.message ??
      "Reprocess request accepted by the intelligence service.",
    status: response.status ?? "accepted",
  };
}
