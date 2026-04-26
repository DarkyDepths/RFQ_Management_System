"use client";

import { useEffect, useState } from "react";

import { listLeadershipNotes } from "@/connectors/manager/leadership-notes";
import {
  getDashboardAnalytics,
  getDashboardMetrics,
  listRfqs,
} from "@/connectors/manager/rfqs";
import type { LeadershipNoteThreadModel } from "@/models/manager/leadership-note";
import type { RfqCardModel } from "@/models/manager/rfq";
import type { AppRole } from "@/models/ui/role";
import type {
  KPIMetricModel,
  ManagerDashboardAnalyticsModel,
} from "@/models/ui/dashboard";
import {
  buildDelayDriverDistribution,
  buildLifecycleDistribution,
  buildLossReasonDistribution,
  getAwaitingLeadershipThreads,
  getCurrentLeadershipThread,
  getLossReasonLabel,
  isOverdueRfq,
  isTerminalRfq,
  type ExecutiveAggregateEntry,
} from "@/lib/executive-insights";
import { getBlockedStageHeadline, getRfqBlockedSignal } from "@/utils/blocker-signal";

export interface ExecutiveAttentionItem {
  leadershipThreadStateLabel?: LeadershipNoteThreadModel["stateLabel"];
  leadershipThreadTone?: LeadershipNoteThreadModel["stateTone"];
  reason: string;
  rfq: RfqCardModel;
  signalLabel: string;
  tone: "steel" | "gold" | "emerald" | "rose" | "amber";
}

interface DashboardState {
  analytics: ManagerDashboardAnalyticsModel | null;
  attentionItems: ExecutiveAttentionItem[];
  delayDrivers: ExecutiveAggregateEntry[];
  error: string | null;
  lifecycleDistribution: ExecutiveAggregateEntry[];
  leadershipNotes: LeadershipNoteThreadModel[];
  leadershipNotesError: string | null;
  lossReasons: ExecutiveAggregateEntry[];
  loading: boolean;
  metrics: KPIMetricModel[];
  rfqs: RfqCardModel[];
}

function buildExecutiveMetrics(
  rfqs: RfqCardModel[],
  leadershipNotes: LeadershipNoteThreadModel[],
  leadershipNotesError: string | null,
): KPIMetricModel[] {
  const activeCount = rfqs.filter((rfq) => !isTerminalRfq(rfq)).length;
  const blockedCount = rfqs.filter((rfq) => getRfqBlockedSignal(rfq).isBlocked).length;
  const overdueCount = rfqs.filter(isOverdueRfq).length;
  const lossesCount = rfqs.filter((rfq) => getLossReasonLabel(rfq) !== null).length;
  const awaitingManagerCount = getAwaitingLeadershipThreads(leadershipNotes).length;

  return [
    {
      helper: "Open pursuits currently visible in the executive portfolio monitor.",
      id: "active-rfqs",
      label: "Active RFQs",
      tone: "steel",
      trendDirection: "steady",
      trendLabel: `${blockedCount} blocked`,
      value: `${activeCount}`,
    },
    {
      helper: "RFQs with a blocked workflow stage requiring department attention.",
      id: "blocked-rfqs",
      label: "Blocked RFQs",
      tone: "amber",
      trendDirection: blockedCount > 0 ? "up" : "steady",
      trendLabel: `${overdueCount} overdue`,
      value: `${blockedCount}`,
    },
    {
      helper: "Active RFQs past the current due date.",
      id: "overdue-rfqs",
      label: "Overdue RFQs",
      tone: "gold",
      trendDirection: overdueCount > 0 ? "up" : "steady",
      trendLabel: `${awaitingManagerCount} leadership follow-up`,
      value: `${overdueCount}`,
    },
    {
      helper: "Lost RFQs with rationale ready for executive review.",
      id: "recent-losses",
      label: "Recent Losses",
      tone: "steel",
      trendDirection: lossesCount > 0 ? "up" : "steady",
      trendLabel: "Outcome reasoning captured in detail view",
      value: `${lossesCount}`,
    },
    {
      helper: "Open leadership threads still waiting for manager response.",
      id: "leadership-notes",
      label: "Awaiting Response",
      tone: leadershipNotesError ? "amber" : "emerald",
      trendDirection: awaitingManagerCount > 0 ? "up" : "steady",
      trendLabel: leadershipNotesError
        ? "Demo-only for now"
        : `${leadershipNotes.length} total thread(s)`,
      value: `${awaitingManagerCount}`,
    },
  ];
}

function buildExecutiveAttentionItems(
  rfqs: RfqCardModel[],
  leadershipNotes: LeadershipNoteThreadModel[],
): ExecutiveAttentionItem[] {
  return rfqs
    .map((rfq) => {
      const blockedSignal = getRfqBlockedSignal(rfq);
      const overdue = isOverdueRfq(rfq);
      const currentThread = getCurrentLeadershipThread(rfq.id, leadershipNotes);
      const waitingOnManager = Boolean(currentThread?.waitingOnManager);
      const leadershipMeta = currentThread
        ? {
            leadershipThreadStateLabel: currentThread.stateLabel,
            leadershipThreadTone: currentThread.stateTone,
          }
        : {};

      if (blockedSignal.isBlocked) {
        const blockedHeadline = getBlockedStageHeadline(rfq) ?? rfq.stageLabel;
        return {
          ...leadershipMeta,
          reason:
            rfq.summaryLine ??
            `${blockedHeadline}. Review the RFQ detail for blocker diagnosis and escalation context.`,
          rfq,
          score: 420 + rfq.rfqProgress + (waitingOnManager ? 60 : 0),
          signalLabel: blockedHeadline,
          tone: "rose" as const,
        };
      }

      if (overdue) {
        return {
          ...leadershipMeta,
          reason: `Due ${rfq.dueLabel}. ${rfq.summaryLine ?? "Leadership attention is recommended to understand the delay driver."}`,
          rfq,
          score: 340 + (waitingOnManager ? 50 : 0),
          signalLabel: "Overdue",
          tone: "rose" as const,
        };
      }

      if (rfq.status === "lost") {
        return {
          ...leadershipMeta,
          reason:
            rfq.outcomeReason ??
            rfq.summaryLine ??
            "Outcome reasoning is available in the RFQ detail for leadership review.",
          rfq,
          score: 280 + (waitingOnManager ? 30 : 0),
          signalLabel: "Loss review",
          tone: "gold" as const,
        };
      }

      if (rfq.intelligenceState === "failed") {
        return {
          ...leadershipMeta,
          reason:
            rfq.summaryLine ??
            "Partial or failed intelligence posture merits a strategic check-in.",
          rfq,
          score: 240 + (waitingOnManager ? 30 : 0),
          signalLabel: "At risk",
          tone: "gold" as const,
        };
      }

      if (waitingOnManager && currentThread) {
        return {
          ...leadershipMeta,
          reason:
            currentThread.latestExecutiveMessage ??
            "Leadership has requested a manager response on this RFQ.",
          rfq,
          score: 210,
          signalLabel: "Awaiting response",
          tone: "amber" as const,
        };
      }

      if (rfq.priority === "critical") {
        return {
          ...leadershipMeta,
          reason:
            rfq.nextAction ??
            "Critical RFQ. Keep it on leadership watch while the team advances the next step.",
          rfq,
          score: 180,
          signalLabel: "Critical watch",
          tone: "steel" as const,
        };
      }

      return {
        reason: rfq.nextAction ?? rfq.summaryLine ?? "No strategic attention signal.",
        rfq,
        score: 0,
        signalLabel: rfq.stageLabel,
        tone: "emerald" as const,
      };
    })
    .filter((item) => item.score > 0)
    .sort((left, right) => right.score - left.score)
    .slice(0, 5)
    .map((item) => ({
      leadershipThreadStateLabel:
        "leadershipThreadStateLabel" in item
          ? item.leadershipThreadStateLabel
          : undefined,
      leadershipThreadTone:
        "leadershipThreadTone" in item ? item.leadershipThreadTone : undefined,
      reason: item.reason,
      rfq: item.rfq,
      signalLabel: item.signalLabel,
      tone: item.tone,
    }));
}

export function useDashboardData(role: AppRole, enabled: boolean) {
  const [state, setState] = useState<DashboardState>({
    analytics: null,
    attentionItems: [],
    delayDrivers: [],
    error: null,
    lifecycleDistribution: [],
    leadershipNotes: [],
    leadershipNotesError: null,
    lossReasons: [],
    loading: true,
    metrics: [],
    rfqs: [],
  });

  useEffect(() => {
    if (!enabled) {
      setState({
        analytics: null,
        attentionItems: [],
        delayDrivers: [],
        error: null,
        lifecycleDistribution: [],
        leadershipNotes: [],
        leadershipNotesError: null,
        lossReasons: [],
        loading: false,
        metrics: [],
        rfqs: [],
      });
      return;
    }

    let active = true;

    async function loadExecutiveDashboard() {
      try {
        const [rfqs, leadershipResult] = await Promise.all([
          listRfqs({ size: 100 }),
          listLeadershipNotes()
            .then((threads) => ({
              error: null,
              threads,
            }))
            .catch((error) => ({
              error:
                error instanceof Error
                  ? error.message
                  : "Leadership Notes could not be loaded.",
              threads: [] as LeadershipNoteThreadModel[],
            })),
        ]);

        if (!active) {
          return;
        }

        setState({
          analytics: null,
          attentionItems: buildExecutiveAttentionItems(rfqs, leadershipResult.threads),
          delayDrivers: buildDelayDriverDistribution(rfqs),
          error: null,
          lifecycleDistribution: buildLifecycleDistribution(rfqs),
          leadershipNotes: leadershipResult.threads,
          leadershipNotesError: leadershipResult.error,
          lossReasons: buildLossReasonDistribution(rfqs),
          loading: false,
          metrics: buildExecutiveMetrics(
            rfqs,
            leadershipResult.threads,
            leadershipResult.error,
          ),
          rfqs,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          analytics: null,
          attentionItems: [],
          delayDrivers: [],
          error:
            error instanceof Error
              ? error.message
              : "Dashboard data could not be loaded.",
          lifecycleDistribution: [],
          leadershipNotes: [],
          leadershipNotesError: null,
          lossReasons: [],
          loading: false,
          metrics: [],
          rfqs: [],
        });
      }
    }

    async function loadManagerDashboard() {
      try {
        const [metrics, analytics, rfqs] = await Promise.all([
          getDashboardMetrics(),
          getDashboardAnalytics(),
          listRfqs({ size: 100 }),
        ]);

        if (!active) {
          return;
        }

        setState({
          analytics,
          attentionItems: [],
          delayDrivers: [],
          error: null,
          lifecycleDistribution: [],
          leadershipNotes: [],
          leadershipNotesError: null,
          lossReasons: [],
          loading: false,
          metrics,
          rfqs,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          analytics: null,
          attentionItems: [],
          delayDrivers: [],
          error:
            error instanceof Error
              ? error.message
              : "Dashboard data could not be loaded.",
          lifecycleDistribution: [],
          leadershipNotes: [],
          leadershipNotesError: null,
          lossReasons: [],
          loading: false,
          metrics: [],
          rfqs: [],
        });
      }
    }

    if (role === "executive") {
      void loadExecutiveDashboard();
    } else {
      void loadManagerDashboard();
    }

    return () => {
      active = false;
    };
  }, [enabled, role]);

  return state;
}
