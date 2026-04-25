import { apiConfig } from "@/config/api";
import { requestJson, type RequestOptions } from "@/lib/http-client";

function buildIntelligenceUrl(path: string) {
  return new URL(
    `${apiConfig.intelligenceApiPath}${path}`,
    apiConfig.intelligenceBaseUrl,
  ).toString();
}

export function requestIntelligenceJson<T>(
  path: string,
  init?: RequestOptions,
) {
  return requestJson<T>(buildIntelligenceUrl(path), init);
}
