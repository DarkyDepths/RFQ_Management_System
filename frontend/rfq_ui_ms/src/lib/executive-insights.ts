import type { LeadershipNoteThreadModel } from "@/models/manager/leadership-note";
import type { RfqCardModel } from "@/models/manager/rfq";
import { getTerminalRfqOutcome, getRfqStatusLabel } from "@/lib/rfq-status-display";
import { formatBlockerReasonLabel, getRfqBlockedSignal } from "@/utils/blocker-signal";
import { isTerminalRfqStatus } from "@/utils/status";

export type ExecutiveVisualTone = "steel" | "gold" | "emerald" | "rose" | "amber";
export type RfqMonitorSignalFilter = "active" | "blocked" | "overdue";
export type RfqMonitorLeadershipFilter = "awaiting_response";

export interface RfqMonitorDrilldownFilters {
  driver?: string | null;
  leadership?: RfqMonitorLeadershipFilter | null;
  lossReason?: string | null;
  signal?: RfqMonitorSignalFilter | null;
  stage?: string | null;
}

export interface ExecutiveAggregateEntry {
  count: number;
  label: string;
  tone?: ExecutiveVisualTone;
}

export function buildRfqMonitorHref(
  filters: Partial<
    RfqMonitorDrilldownFilters & {
      source?: "dashboard";
      status?: "all" | RfqCardModel["status"];
    }
  >,
) {
  const params = new URLSearchParams();

  if (filters.status && filters.status !== "all") {
    params.set("status", filters.status);
  }

  if (filters.signal) {
    params.set("signal", filters.signal);
  }

  if (filters.stage) {
    params.set("stage", filters.stage);
  }

  if (filters.driver) {
    params.set("driver", filters.driver);
  }

  if (filters.lossReason) {
    params.set("loss_reason", filters.lossReason);
  }

  if (filters.leadership) {
    params.set("leadership", filters.leadership);
  }

  if (filters.source) {
    params.set("source", filters.source);
  }

  const query = params.toString();
  return query ? `/rfqs?${query}` : "/rfqs";
}

export function isTerminalRfq(rfq: RfqCardModel) {
  return isTerminalRfqStatus(rfq.status);
}

export function isOverdueRfq(rfq: RfqCardModel) {
  if (isTerminalRfq(rfq)) {
    return false;
  }

  const dueAt = Date.parse(rfq.dueDateValue);
  return !Number.isNaN(dueAt) && dueAt < Date.now();
}

export function getAwaitingLeadershipThreads(threads: LeadershipNoteThreadModel[]) {
  return threads.filter((thread) => thread.waitingOnManager);
}

export function getCurrentLeadershipThread(
  rfqId: string,
  threads: LeadershipNoteThreadModel[],
) {
  return threads.find((thread) => thread.rfqId === rfqId && thread.state !== "closed") ?? null;
}

export function getPrimaryDelayDriver(rfq: RfqCardModel): {
  label: string;
  tone: ExecutiveVisualTone;
} | null {
  if (isTerminalRfq(rfq)) {
    return null;
  }

  const blockedSignal = getRfqBlockedSignal(rfq);
  if (blockedSignal.isBlocked && rfq.blockerReasonCode) {
    return {
      label: formatBlockerReasonLabel(rfq.blockerReasonCode) ?? "Blocked",
      tone: "rose",
    };
  }

  if (blockedSignal.isBlocked) {
    return {
      label: `Blocked in ${blockedSignal.stageLabel ?? rfq.stageLabel}`,
      tone: "rose",
    };
  }

  if (isOverdueRfq(rfq)) {
    return {
      label: "Overdue Without Captured Blocker",
      tone: "rose",
    };
  }

  if (rfq.intelligenceState === "failed") {
    return {
      label: "Intelligence Failed",
      tone: "amber",
    };
  }

  if (rfq.intelligenceState === "partial") {
    return {
      label: "Partial Intelligence",
      tone: "gold",
    };
  }

  return null;
}

export function getLossReasonLabel(rfq: RfqCardModel) {
  if (getTerminalRfqOutcome(rfq.status) !== "lost") {
    return null;
  }

  return rfq.outcomeReason?.trim() || "Reason Not Captured";
}

export function getLifecycleDistributionLabel(rfq: RfqCardModel) {
  const terminalOutcome = getTerminalRfqOutcome(rfq.status);
  if (terminalOutcome) {
    return getRfqStatusLabel(terminalOutcome);
  }

  return rfq.stageLabel;
}

function getCurrentStageOrder(rfq: RfqCardModel) {
  return rfq.stageHistory.find((stage) => stage.label === rfq.stageLabel)?.order ?? 999;
}

export function buildLifecycleDistribution(rfqs: RfqCardModel[]): ExecutiveAggregateEntry[] {
  const stageMap = new Map<
    string,
    {
      count: number;
      order: number;
    }
  >();

  rfqs.forEach((rfq) => {
    const label = getLifecycleDistributionLabel(rfq);
    const current = stageMap.get(label);
    const order = getCurrentStageOrder(rfq);

    if (current) {
      current.count += 1;
      current.order = Math.min(current.order, order);
      return;
    }

    stageMap.set(label, {
      count: 1,
      order,
    });
  });

  return [...stageMap.entries()]
    .map(([label, value]) => ({
      count: value.count,
      label,
      order: value.order,
    }))
    .sort((left, right) => left.order - right.order || left.label.localeCompare(right.label))
    .map(({ count, label }) => ({
      count,
      label,
    }));
}

export function buildDelayDriverDistribution(rfqs: RfqCardModel[]): ExecutiveAggregateEntry[] {
  const driverMap = new Map<string, ExecutiveAggregateEntry>();

  rfqs.forEach((rfq) => {
    const driver = getPrimaryDelayDriver(rfq);
    if (!driver) {
      return;
    }

    const current = driverMap.get(driver.label);
    if (current) {
      current.count += 1;
      return;
    }

    driverMap.set(driver.label, {
      count: 1,
      label: driver.label,
      tone: driver.tone,
    });
  });

  return [...driverMap.values()].sort((left, right) => right.count - left.count);
}

export function buildLossReasonDistribution(rfqs: RfqCardModel[]): ExecutiveAggregateEntry[] {
  const reasonMap = new Map<string, ExecutiveAggregateEntry>();

  rfqs.forEach((rfq) => {
    const reason = getLossReasonLabel(rfq);
    if (!reason) {
      return;
    }

    const current = reasonMap.get(reason);
    if (current) {
      current.count += 1;
      return;
    }

    reasonMap.set(reason, {
      count: 1,
      label: reason,
      tone: "steel",
    });
  });

  return [...reasonMap.values()].sort((left, right) => right.count - left.count);
}

export function applyRfqMonitorDrilldown(
  rfqs: RfqCardModel[],
  filters: RfqMonitorDrilldownFilters,
  leadershipThreads: LeadershipNoteThreadModel[] = [],
) {
  const awaitingLeadershipIds = new Set(
    getAwaitingLeadershipThreads(leadershipThreads).map((thread) => thread.rfqId),
  );

  return rfqs.filter((rfq) => {
    if (filters.signal === "active" && isTerminalRfq(rfq)) {
      return false;
    }

    if (filters.signal === "blocked" && !getRfqBlockedSignal(rfq).isBlocked) {
      return false;
    }

    if (filters.signal === "overdue" && !isOverdueRfq(rfq)) {
      return false;
    }

    if (filters.stage && getLifecycleDistributionLabel(rfq) !== filters.stage) {
      return false;
    }

    if (filters.driver && getPrimaryDelayDriver(rfq)?.label !== filters.driver) {
      return false;
    }

    if (filters.lossReason && getLossReasonLabel(rfq) !== filters.lossReason) {
      return false;
    }

    if (filters.leadership === "awaiting_response" && !awaitingLeadershipIds.has(rfq.id)) {
      return false;
    }

    return true;
  });
}
