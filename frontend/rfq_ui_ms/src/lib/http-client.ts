type HttpMethod = "GET" | "POST" | "PATCH" | "DELETE";

export class HttpError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "HttpError";
    this.status = status;
  }
}

export interface RequestOptions extends RequestInit {
  method?: HttpMethod;
  authToken?: string;
}

async function resolveErrorMessage(response: Response) {
  const contentType = response.headers.get("Content-Type") ?? "";
  const responseText = (await response.text()).trim();

  if (contentType.includes("application/json")) {
    const payload = responseText
      ? (() => {
          try {
            return JSON.parse(responseText);
          } catch {
            return null;
          }
        })()
      : null;
    if (payload && typeof payload === "object") {
      if (
        "message" in payload &&
        typeof payload.message === "string" &&
        payload.message.trim().length > 0
      ) {
        return payload.message;
      }

      if (
        "detail" in payload &&
        typeof payload.detail === "string" &&
        payload.detail.trim().length > 0
      ) {
        return payload.detail;
      }
    }
  }

  return responseText || `Request failed with status ${response.status}`;
}

export async function requestJson<T>(
  input: string,
  init?: RequestOptions,
): Promise<T> {
  const { authToken, headers: rawHeaders, ...requestInit } = init ?? {};
  const headers = new Headers(rawHeaders ?? {});

  if (
    requestInit.body !== undefined &&
    !headers.has("Content-Type") &&
    !(requestInit.body instanceof FormData)
  ) {
    headers.set("Content-Type", "application/json");
  }

  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }

  const response = await fetch(input, {
    cache: "no-store",
    ...requestInit,
    headers,
  });

  if (!response.ok) {
    const message = await resolveErrorMessage(response);
    throw new HttpError(response.status, message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
