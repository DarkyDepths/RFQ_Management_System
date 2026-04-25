const useMockData = process.env.NEXT_PUBLIC_USE_MOCK_DATA === "true";

export const apiConfig = {
  useMockData,
  managerDebugHeadersEnabled:
    process.env.NEXT_PUBLIC_MANAGER_DEBUG_HEADERS_ENABLED === "true",
  demoLatencyMs: Number(process.env.NEXT_PUBLIC_DEMO_LATENCY_MS ?? 650),
  managerBaseUrl:
    process.env.NEXT_PUBLIC_MANAGER_API_URL ?? "http://localhost:8000",
  managerApiPath: "/rfq-manager/v1",
  managerAuthToken: process.env.NEXT_PUBLIC_MANAGER_API_TOKEN,
  intelligenceBaseUrl:
    process.env.NEXT_PUBLIC_INTELLIGENCE_API_URL ?? "http://localhost:8001",
  intelligenceApiPath: "/intelligence/v1",
} as const;
