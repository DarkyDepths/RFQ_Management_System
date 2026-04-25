import { apiConfig } from "@/config/api";
import { requestManagerJson } from "@/connectors/manager/base";
import { isDemoActiveRfqStatus } from "@/demo/manager/status";
import {
  cancelDemoRfq,
  createDemoRfq,
  managerRfqDetailResponses,
  managerRfqListResponse,
  updateDemoRfq,
} from "@/demo/manager/rfqs";
import type {
  ManagerApiCancelRfqInput,
  ManagerApiCreateRfqInput,
  ManagerApiRfqAnalytics,
  ManagerApiRfqDetail,
  ManagerApiRfqListResponse,
  ManagerApiRfqStats,
  ManagerApiUpdateRfqInput,
} from "@/models/manager/api-rfq";
import type {
  ManagerApiStageDetail,
  ManagerApiStageListResponse,
} from "@/models/manager/api-stage";
import type {
  CancelRfqInput,
  CreateRfqInput,
  DashboardMetricModel,
  LiveManagerRfqStatus,
  ManagerRfqStatus,
  ManagerRfqDetailResponse,
  ManagerRfqListItemResponse,
  RfqCardModel,
  RfqDetailModel,
  RfqMutationResult,
  UpdateRfqInput,
} from "@/models/manager/rfq";
import {
  translateManagerAnalytics,
  translateManagerRfqCard,
  translateManagerRfqDetail,
  translateManagerStats,
  translateDashboardMetric,
  translateRfqCard,
  translateRfqDetail,
} from "@/translators/manager/rfqs";
import type { ManagerDashboardAnalyticsModel } from "@/models/ui/dashboard";
import { sleep } from "@/utils/async";

export interface ListRfqsOptions {
  page?: number;
  search?: string;
  size?: number;
  sort?: "client" | "deadline" | "status";
  status?: "all" | ManagerRfqStatus;
}

const liveStatusQueryMap: Record<LiveManagerRfqStatus, string> = {
  in_preparation: "In preparation",
  awarded: "Awarded",
  lost: "Lost",
  cancelled: "Cancelled",
};

function buildUnavailableAnalyticsMetric(
  id: string,
  label: string,
  helper: string,
  tone: "steel" | "gold" | "emerald" | "amber",
) {
  return {
    displayValue: "Unavailable",
    helper,
    id,
    isAvailable: false,
    label,
    tone,
    value: null,
  } as const;
}

function applyDemoListFilters(
  items: ManagerRfqListItemResponse[],
  options: ListRfqsOptions,
) {
  const normalizedSearch = options.search?.trim().toLowerCase() ?? "";
  const filtered = items.filter((rfq) => {
    const matchesSearch =
      normalizedSearch.length === 0 ||
      [rfq.id, rfq.title, rfq.client, rfq.owner, rfq.region]
        .join(" ")
        .toLowerCase()
        .includes(normalizedSearch);

    const matchesStatus =
      !options.status || options.status === "all" || rfq.status === options.status;

    return matchesSearch && matchesStatus;
  });

  const sorted = [...filtered];

  if (options.sort === "client") {
    sorted.sort((left, right) => left.client.localeCompare(right.client));
  } else if (options.sort === "status") {
    sorted.sort((left, right) => left.status.localeCompare(right.status));
  } else if (options.sort === "deadline") {
    sorted.sort((left, right) => left.dueDate.localeCompare(right.dueDate));
  }

  const page = options.page ?? 1;
  const size = options.size ?? sorted.length;
  const start = (page - 1) * size;

  return sorted.slice(start, start + size);
}

export async function listRfqs(
  options: ListRfqsOptions = {},
): Promise<RfqCardModel[]> {
  if (apiConfig.useMockData) {
    await sleep(apiConfig.demoLatencyMs);
    return applyDemoListFilters(managerRfqListResponse.items, options).map(
      translateRfqCard,
    );
  }

  const liveStatus =
    options.status && options.status !== "all"
      ? options.status
      : undefined;

  if (
    liveStatus
    && !(liveStatus in liveStatusQueryMap)
  ) {
    throw new Error(
      `Unsupported live RFQ status filter '${liveStatus}'.`,
    );
  }

  const response = await requestManagerJson<ManagerApiRfqListResponse>(
    "/rfqs",
    undefined,
    {
      page: options.page ?? 1,
      search: options.search,
      size: options.size ?? 20,
      sort:
        options.sort === "deadline"
          ? "deadline"
          : options.sort === "client"
            ? "client"
            : options.sort === "status"
              ? "status"
              : undefined,
      status: liveStatus
        ? liveStatusQueryMap[liveStatus as LiveManagerRfqStatus]
        : undefined,
    },
  );

  return response.data.map(translateManagerRfqCard);
}

export async function getDashboardMetrics(): Promise<DashboardMetricModel[]> {
  if (apiConfig.useMockData) {
    await sleep(apiConfig.demoLatencyMs);

    const totalRfqs = managerRfqListResponse.items.length;
    const openRfqs = managerRfqListResponse.items.filter((rfq) =>
      isDemoActiveRfqStatus(rfq.status),
    ).length;
    const criticalRfqs = managerRfqListResponse.items.filter(
      (rfq) => isDemoActiveRfqStatus(rfq.status) && rfq.priority === "critical",
    ).length;
    const avgCycleDays = 0;
    const metrics = translateManagerStats({
      avg_cycle_days: avgCycleDays,
      critical_rfqs: criticalRfqs,
      open_rfqs: openRfqs,
      total_rfqs_12m: totalRfqs,
    });

    return metrics.map((metric) =>
      metric.id === "avg-cycle-days"
        ? {
            ...metric,
            helper: "Cycle time is intentionally withheld in demo mode until a truthful source is wired.",
            trendLabel: "Demo baseline withheld",
            value: "Unavailable",
          }
        : metric,
    );
  }

  const response = await requestManagerJson<ManagerApiRfqStats>(
    "/rfqs/stats",
  );

  return translateManagerStats(response);
}

export async function getDashboardAnalytics(): Promise<ManagerDashboardAnalyticsModel> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.8));

    const awardedCount = managerRfqListResponse.items.filter(
      (rfq) => rfq.status === "awarded",
    ).length;
    const lostCount = managerRfqListResponse.items.filter(
      (rfq) => rfq.status === "lost",
    ).length;
    const decidedCount = awardedCount + lostCount;
    const winRate = decidedCount
      ? Math.round((awardedCount / decidedCount) * 1000) / 10
      : 0;

    const byClientCounts = new Map<
      string,
      {
        client: string;
        rfqCount: number;
      }
    >();
    managerRfqListResponse.items.forEach((rfq) => {
      const current = byClientCounts.get(rfq.client);
      if (current) {
        current.rfqCount += 1;
        return;
      }

      byClientCounts.set(rfq.client, {
        client: rfq.client,
        rfqCount: 1,
      });
    });

    return {
      metrics: [
        {
          id: "win-rate",
          label: "Win Rate",
          value: winRate,
          displayValue: `${winRate}%`,
          helper: "Computed from awarded versus lost demo RFQs.",
          isAvailable: true,
          tone: "emerald",
        },
        buildUnavailableAnalyticsMetric(
          "estimation-accuracy",
          "Estimation Accuracy",
          "Not captured truthfully in demo mode yet.",
          "steel",
        ),
        buildUnavailableAnalyticsMetric(
          "avg-margin-submitted",
          "Avg Margin Submitted",
          "Margin analytics are intentionally withheld until a reliable source exists.",
          "gold",
        ),
        buildUnavailableAnalyticsMetric(
          "avg-margin-awarded",
          "Avg Margin Awarded",
          "Margin analytics are intentionally withheld until a reliable source exists.",
          "amber",
        ),
      ],
      byClient: [...byClientCounts.values()]
        .sort((left, right) => right.rfqCount - left.rfqCount)
        .slice(0, 20)
        .map((entry) => ({
          avgMarginLabel: "Unavailable",
          avgMarginValue: null,
          client: entry.client,
          isMarginAvailable: false,
          rfqCount: entry.rfqCount,
        })),
    };
  }

  const response = await requestManagerJson<ManagerApiRfqAnalytics>(
    "/rfqs/analytics",
  );

  return translateManagerAnalytics(response);
}

async function getLiveStageCollections(
  rfqId: string,
  currentStageId?: string | null,
) {
  const stagesResponse = await requestManagerJson<ManagerApiStageListResponse>(
    `/rfqs/${rfqId}/stages`,
  );

  const currentStage = currentStageId
    ? await requestManagerJson<ManagerApiStageDetail>(
        `/rfqs/${rfqId}/stages/${currentStageId}`,
      )
    : null;

  return {
    currentStage,
    stages: stagesResponse.data,
  };
}

export async function getRfqDetail(
  rfqId: string,
): Promise<RfqDetailModel | null> {
  if (apiConfig.useMockData) {
    await sleep(apiConfig.demoLatencyMs);
    const detail = managerRfqDetailResponses[rfqId];
    return detail ? translateRfqDetail(detail) : null;
  }

  const response = await requestManagerJson<ManagerApiRfqDetail>(
    `/rfqs/${rfqId}`,
  );

  const { stages, currentStage } = await getLiveStageCollections(
    rfqId,
    response.current_stage_id,
  );

  return translateManagerRfqDetail(response, stages, currentStage);
}

export async function createRfq(
  input: CreateRfqInput,
): Promise<RfqMutationResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.75));
    const detail = createDemoRfq(input);
    return {
      id: detail.id,
      message: "RFQ created in demo mode with generated workflow stages.",
      status: "created",
    };
  }

  const response = await requestManagerJson<ManagerApiRfqDetail>("/rfqs", {
    method: "POST",
    body: JSON.stringify({
      client: input.client,
      country: input.country,
      deadline: input.deadline,
      description: input.description,
      industry: input.industry,
      name: input.name,
      owner: input.owner,
      priority: input.priority,
      skip_stages: input.skipStageIds,
      workflow_id: input.workflowId,
    } satisfies ManagerApiCreateRfqInput),
  });

  return {
    id: response.id,
    message: "RFQ created through the manager service.",
    status: "created",
  };
}

export const createRfqDraft = createRfq;

export async function updateRfqRecord(
  rfqId: string,
  input: UpdateRfqInput,
): Promise<RfqMutationResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.65));
    updateDemoRfq(rfqId, input);
    return {
      id: rfqId,
      message: "RFQ updated in demo mode.",
      status: "updated",
    };
  }

  const response = await requestManagerJson<ManagerApiRfqDetail>(
    `/rfqs/${rfqId}`,
    {
      method: "PATCH",
      body: JSON.stringify({
        client: input.client,
        country: input.country,
        deadline: input.deadline,
        description: input.description,
        industry: input.industry,
        name: input.name,
        outcome_reason: input.outcomeReason,
        owner: input.owner,
        priority: input.priority,
      } satisfies ManagerApiUpdateRfqInput),
    },
  );

  return {
    id: response.id,
    message: "RFQ updated through the manager service.",
    status: "updated",
  };
}

export async function cancelRfqRecord(
  rfqId: string,
  input: CancelRfqInput,
): Promise<RfqMutationResult> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.65));
    cancelDemoRfq(rfqId, input);
    return {
      id: rfqId,
      message: "RFQ cancelled in demo mode.",
      status: "updated",
    };
  }

  const response = await requestManagerJson<ManagerApiRfqDetail>(
    `/rfqs/${rfqId}/cancel`,
    {
      method: "POST",
      body: JSON.stringify({
        outcome_reason: input.outcomeReason,
      } satisfies ManagerApiCancelRfqInput),
    },
  );

  return {
    id: response.id,
    message: "RFQ cancelled through the manager service.",
    status: "updated",
  };
}
