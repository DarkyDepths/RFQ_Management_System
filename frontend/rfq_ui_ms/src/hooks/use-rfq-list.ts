"use client";

import { useDeferredValue, useEffect, useState } from "react";

import type { RolePermissions } from "@/config/role-permissions";
import { apiConfig } from "@/config/api";
import { listLeadershipNotes } from "@/connectors/manager/leadership-notes";
import { listRfqs } from "@/connectors/manager/rfqs";
import { demoStatusOptions } from "@/demo/manager/status";
import {
  applyRfqMonitorDrilldown,
  type RfqMonitorDrilldownFilters,
} from "@/lib/executive-insights";
import { getRoleActorProfile } from "@/lib/manager-actor";
import { filterRfqsForRole } from "@/lib/rfq-access";
import type { RfqCardModel } from "@/models/manager/rfq";
import type { AppRole } from "@/models/ui/role";

type ViewMode = "table" | "cards";

interface UseRfqListOptions extends Partial<RfqMonitorDrilldownFilters> {
  initialStatusFilter?: "all" | RfqCardModel["status"];
}

export function useRfqList(
  role: AppRole,
  permissions: RolePermissions,
  options: UseRfqListOptions = {},
) {
  const {
    driver = null,
    initialStatusFilter = "all",
    leadership = null,
    lossReason = null,
    signal = null,
    stage = null,
  } = options;
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [rfqs, setRfqs] = useState<RfqCardModel[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<"all" | RfqCardModel["status"]>(initialStatusFilter);
  const [viewMode, setViewMode] = useState<ViewMode>("table");
  const deferredSearch = useDeferredValue(search);
  const actorName = getRoleActorProfile(role).userName;

  useEffect(() => {
    setStatusFilter(initialStatusFilter);
  }, [initialStatusFilter]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);

      try {
        const items = await listRfqs({
          search: deferredSearch,
          size: 100,
          status: statusFilter,
        });
        const scopedItems = filterRfqsForRole(role, permissions, items, actorName);

        if (leadership === "awaiting_response") {
          const leadershipThreads = await listLeadershipNotes();

          if (!active) {
            return;
          }

          setError(null);
          setRfqs(
            applyRfqMonitorDrilldown(
              scopedItems,
              {
                driver,
                leadership,
                lossReason,
                signal,
                stage,
              },
              leadershipThreads,
            ),
          );
          setLoading(false);
          return;
        }

        if (!active) {
          return;
        }

        setError(null);
        setRfqs(
          applyRfqMonitorDrilldown(scopedItems, {
            driver,
            leadership,
            lossReason,
            signal,
            stage,
          }),
        );
        setLoading(false);
      } catch (error) {
        if (!active) {
          return;
        }

        setError(
          error instanceof Error ? error.message : "RFQ list could not be loaded.",
        );
        setRfqs([]);
        setLoading(false);
      }
    }

    load();

    return () => {
      active = false;
    };
  }, [
    actorName,
    deferredSearch,
    driver,
    leadership,
    lossReason,
    permissions,
    role,
    signal,
    stage,
    statusFilter,
  ]);

  const statusOptions: Array<{
    label: string;
    value: "all" | RfqCardModel["status"];
  }> = apiConfig.useMockData
    ? demoStatusOptions
    : [
        { label: "All", value: "all" },
        { label: "In Preparation", value: "in_preparation" },
        { label: "Awarded", value: "awarded" },
        { label: "Lost", value: "lost" },
        { label: "Cancelled", value: "cancelled" },
      ];

  return {
    error,
    loading,
    rfqs,
    filteredRfqs: rfqs,
    search,
    setSearch,
    statusFilter,
    statusOptions,
    setStatusFilter,
    viewMode,
    setViewMode,
  };
}
