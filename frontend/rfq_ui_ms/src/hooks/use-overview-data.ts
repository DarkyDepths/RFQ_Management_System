"use client";

import { useEffect, useState } from "react";

import { apiConfig } from "@/config/api";
import { getDashboardMetrics, listRfqs } from "@/connectors/manager/rfqs";
import { isDemoActiveRfqStatus } from "@/demo/manager/status";
import type { RolePermissions } from "@/config/role-permissions";
import { getRoleActorProfile } from "@/lib/manager-actor";
import { filterRfqsForRole } from "@/lib/rfq-access";
import type { RfqCardModel } from "@/models/manager/rfq";
import type { AppRole } from "@/models/ui/role";
import type { KPIMetricModel } from "@/models/ui/dashboard";
import { isLiveActiveRfqStatus } from "@/utils/status";

interface OverviewState {
  activeRfqs: RfqCardModel[];
  error: string | null;
  loading: boolean;
  metrics: KPIMetricModel[];
  rfqs: RfqCardModel[];
}

function buildEstimatorMetrics(rfqs: RfqCardModel[]): KPIMetricModel[] {
  const today = Date.now();
  const dueSoonCount = rfqs.filter((rfq) => {
    const dueAt = Date.parse(rfq.dueDateValue);
    if (Number.isNaN(dueAt)) {
      return false;
    }

    const diffDays = Math.ceil((dueAt - today) / (1000 * 60 * 60 * 24));
    return diffDays <= 7 && diffDays >= 0;
  }).length;

  const criticalCount = rfqs.filter((rfq) => rfq.priority === "critical").length;
  const attentionCount = rfqs.filter(
    (rfq) =>
      rfq.intelligenceState === "failed"
      || rfq.intelligenceState === "partial"
      || (apiConfig.useMockData && rfq.status === "attention_required"),
  ).length;

  return [
    {
      helper: "RFQs currently within your scoped contributor view.",
      id: "assigned-rfqs",
      label: "Assigned RFQs",
      tone: "steel",
      trendDirection: "steady",
      trendLabel: "Scoped by ownership",
      value: `${rfqs.length}`,
    },
    {
      helper: "Assigned RFQs due within the next 7 days.",
      id: "due-soon",
      label: "Due Soon",
      tone: "gold",
      trendDirection: "steady",
      trendLabel: "Next 7 days",
      value: `${dueSoonCount}`,
    },
    {
      helper: "Critical RFQs currently assigned to you.",
      id: "critical-assigned",
      label: "Critical",
      tone: "amber",
      trendDirection: "steady",
      trendLabel: "Priority signal",
      value: `${criticalCount}`,
    },
    {
      helper: "Assigned RFQs with partial, failed, or attention-required intelligence posture.",
      id: "attention-needed",
      label: "Needs Attention",
      tone: "emerald",
      trendDirection: "steady",
      trendLabel: "Contributor focus",
      value: `${attentionCount}`,
    },
  ];
}

export function useOverviewData(role: AppRole, permissions: RolePermissions) {
  const [state, setState] = useState<OverviewState>({
    activeRfqs: [],
    error: null,
    loading: true,
    metrics: [],
    rfqs: [],
  });
  const actorName = getRoleActorProfile(role).userName;

  useEffect(() => {
    if (role === "executive") {
      setState({
        activeRfqs: [],
        error: null,
        loading: false,
        metrics: [],
        rfqs: [],
      });
      return;
    }

    let active = true;

    async function load() {
      try {
        const rfqs = await listRfqs({ size: 20 });
        const scopedRfqs = filterRfqsForRole(role, permissions, rfqs, actorName);
        const activeRfqs = scopedRfqs.filter((rfq) =>
          apiConfig.useMockData
            ? isDemoActiveRfqStatus(rfq.status)
            : isLiveActiveRfqStatus(rfq.status),
        );
        const metrics = permissions.canViewAnalytics
          ? await getDashboardMetrics()
          : buildEstimatorMetrics(scopedRfqs);

        if (!active) {
          return;
        }

        setState({
          activeRfqs,
          error: null,
          loading: false,
          metrics,
          rfqs: scopedRfqs,
        });
      } catch (error) {
        if (!active) {
          return;
        }

        setState({
          activeRfqs: [],
          error:
            error instanceof Error
              ? error.message
              : "Overview data could not be loaded.",
          loading: false,
          metrics: [],
          rfqs: [],
        });
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [actorName, permissions, role]);

  return state;
}
