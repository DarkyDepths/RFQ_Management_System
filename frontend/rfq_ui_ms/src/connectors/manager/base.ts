import { apiConfig } from "@/config/api";
import { requestJson, type RequestOptions } from "@/lib/http-client";
import { buildManagerActorHeaders } from "@/lib/manager-actor";

type QueryValue =
  | string
  | number
  | boolean
  | null
  | undefined
  | Array<string | number | boolean>;

function buildManagerUrl(
  path: string,
  query?: Record<string, QueryValue>,
) {
  const url = new URL(`${apiConfig.managerApiPath}${path}`, apiConfig.managerBaseUrl);

  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value === undefined || value === null || value === "") {
        continue;
      }

      if (Array.isArray(value)) {
        value.forEach((entry) => {
          url.searchParams.append(key, String(entry));
        });
        continue;
      }

      url.searchParams.set(key, String(value));
    }
  }

  return url.toString();
}

export interface ManagerRequestOptions extends RequestOptions {
  actorPermissions?: string[];
  actorTeam?: string;
  actorUserId?: string;
  actorUserName?: string;
}

export function requestManagerJson<T>(
  path: string,
  init?: ManagerRequestOptions,
  query?: Record<string, QueryValue>,
) {
  const {
    actorPermissions,
    actorTeam,
    actorUserId,
    actorUserName,
    headers,
    ...requestOptions
  } = init ?? {};

  const mergedHeaders = new Headers(headers ?? {});
  const actorHeaders = buildManagerActorHeaders({
    permissions: actorPermissions,
    team: actorTeam,
    userId: actorUserId,
    userName: actorUserName,
  });

  Object.entries(actorHeaders).forEach(([key, value]) => {
    if (!mergedHeaders.has(key)) {
      mergedHeaders.set(key, value);
    }
  });

  return requestJson<T>(buildManagerUrl(path, query), {
    ...requestOptions,
    headers: mergedHeaders,
    authToken: requestOptions.authToken ?? apiConfig.managerAuthToken,
  });
}
