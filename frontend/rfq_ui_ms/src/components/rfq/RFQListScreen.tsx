"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { LayoutGrid, ListFilter, PlusSquare, Search, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import { RFQCard } from "@/components/rfq/RFQCard";
import { RFQTable } from "@/components/rfq/RFQTable";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiConfig } from "@/config/api";
import { getPermissions } from "@/config/role-permissions";
import { useRole } from "@/context/role-context";
import { parseDemoStatusFilter } from "@/demo/manager/status";
import { useRfqList } from "@/hooks/use-rfq-list";
import { getRfqStatusLabel } from "@/lib/rfq-status-display";
import type { RfqCardModel } from "@/models/manager/rfq";
import type {
  RfqMonitorLeadershipFilter,
  RfqMonitorSignalFilter,
} from "@/lib/executive-insights";

function parseStatusFilter(value: string | null): "all" | RfqCardModel["status"] {
  if (apiConfig.useMockData) {
    return parseDemoStatusFilter(value);
  }

  switch (value) {
    case "in_preparation":
    case "awarded":
    case "lost":
    case "cancelled":
      return value;
    default:
      return "all";
  }
}

function parseSignalFilter(value: string | null): RfqMonitorSignalFilter | null {
  return value === "active" || value === "blocked" || value === "overdue" ? value : null;
}

function parseLeadershipFilter(value: string | null): RfqMonitorLeadershipFilter | null {
  return value === "awaiting_response" ? value : null;
}

function buildDrilldownBadges({
  driver,
  leadership,
  lossReason,
  signal,
  stage,
  status,
}: {
  driver: string | null;
  leadership: RfqMonitorLeadershipFilter | null;
  lossReason: string | null;
  signal: RfqMonitorSignalFilter | null;
  stage: string | null;
  status: "all" | RfqCardModel["status"];
}) {
  const badges: Array<{
    label: string;
    value: string;
    variant: "outline" | "steel" | "gold" | "rose" | "amber";
  }> = [];

  if (signal === "active") {
    badges.push({ label: "Signal", value: "Active RFQs", variant: "steel" });
  } else if (signal === "blocked") {
    badges.push({ label: "Signal", value: "Blocked RFQs", variant: "rose" });
  } else if (signal === "overdue") {
    badges.push({ label: "Signal", value: "Overdue RFQs", variant: "rose" });
  }

  if (stage) {
    badges.push({ label: "Stage", value: stage, variant: "outline" });
  }

  if (driver) {
    badges.push({ label: "Delay Driver", value: driver, variant: "gold" });
  }

  if (lossReason) {
    badges.push({ label: "Loss Reason", value: lossReason, variant: "gold" });
  }

  if (leadership === "awaiting_response") {
    badges.push({
      label: "Leadership",
      value: "Awaiting Response",
      variant: "amber",
    });
  }

  if (status !== "all") {
    badges.push({
      label: "Status",
      value: getRfqStatusLabel(status),
      variant: "steel",
    });
  }

  return badges;
}

export function RFQListScreen() {
  const { role } = useRole();
  const pathname = usePathname();
  const permissions = getPermissions(role);
  const router = useRouter();
  const searchParams = useSearchParams();
  const statusFromQuery = parseStatusFilter(searchParams.get("status"));
  const signal = parseSignalFilter(searchParams.get("signal"));
  const stage = searchParams.get("stage");
  const driver = searchParams.get("driver");
  const leadership = parseLeadershipFilter(searchParams.get("leadership"));
  const lossReason = searchParams.get("loss_reason");
  const source = searchParams.get("source");
  const hasDashboardDrilldown =
    source === "dashboard" ||
    Boolean(signal || stage || driver || leadership || lossReason);
  const drilldownBadges = buildDrilldownBadges({
    driver,
    leadership,
    lossReason,
    signal,
    stage,
    status: statusFromQuery,
  });
  const {
    error,
    filteredRfqs,
    loading,
    search,
    setSearch,
    setStatusFilter,
    statusFilter,
    statusOptions,
    viewMode,
    setViewMode,
  } = useRfqList(role, permissions, {
    driver,
    initialStatusFilter: statusFromQuery,
    leadership,
    lossReason,
    signal,
    stage,
  });

  function pushQuery(nextParams: URLSearchParams) {
    const query = nextParams.toString();
    router.replace(query ? `${pathname}?${query}` : pathname);
  }

  function handleStatusChange(nextStatus: "all" | RfqCardModel["status"]) {
    setStatusFilter(nextStatus);

    const params = new URLSearchParams(searchParams.toString());
    if (nextStatus === "all") {
      params.delete("status");
    } else {
      params.set("status", nextStatus);
    }

    pushQuery(params);
  }

  function clearDashboardDrilldown() {
    setSearch("");
    setStatusFilter("all");
    router.replace(pathname);
  }

  return (
    <div className="space-y-6">
      <section className="surface-panel p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="section-kicker">
              <ListFilter className="h-3.5 w-3.5" />
              {role === "executive" ? "Strategic RFQ monitor" : "RFQ queue shell"}
            </div>
            <h1 className="mt-4 text-display text-3xl font-semibold text-foreground lg:text-4xl">
              {permissions.listTitle}
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
              {permissions.listSubtitle}
            </p>
          </div>
          {permissions.canCreateRfq ? (
            <Button asChild size="lg" variant="default">
              <Link href="/rfqs/new">
                <PlusSquare className="h-4 w-4" />
                Create RFQ
              </Link>
            </Button>
          ) : null}
        </div>

        {hasDashboardDrilldown ? (
          <div className="mt-6 rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="section-kicker">
                  <Sparkles className="h-3.5 w-3.5" />
                  Dashboard Drilldown
                </div>
                <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">
                  This monitor view was opened from an executive dashboard visual. The results stay narrowed to the selected portfolio slice until you clear the drilldown.
                </p>
              </div>
              <Button onClick={clearDashboardDrilldown} size="sm" variant="secondary">
                Clear Drilldown
              </Button>
            </div>

            {drilldownBadges.length > 0 ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {drilldownBadges.map((badge) => (
                  <Badge
                    key={`${badge.label}-${badge.value}`}
                    variant={badge.variant}
                  >
                    {badge.label}: {badge.value}
                  </Badge>
                ))}
              </div>
            ) : null}
          </div>
        ) : null}

        <div className="mt-8 grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="relative">
            <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-11 h-11"
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search RFQ ID, title, client, owner, or region"
              value={search}
            />
          </div>
          <div className="flex flex-wrap gap-2">
            <Button
              className="h-11"
              onClick={() => setViewMode("table")}
              variant={viewMode === "table" ? "default" : "secondary"}
            >
              Table
            </Button>
            <Button
              className="h-11"
              onClick={() => setViewMode("cards")}
              variant={viewMode === "cards" ? "default" : "secondary"}
            >
              <LayoutGrid className="h-4 w-4" />
              Cards
            </Button>
          </div>
        </div>

        <div className="mt-6 flex flex-wrap gap-2">
          {statusOptions.map((option) => (
            <Button
              key={option.value}
              onClick={() => handleStatusChange(option.value)}
              size="sm"
              variant={statusFilter === option.value ? "outline" : "secondary"}
            >
              {option.label}
            </Button>
          ))}
        </div>
      </section>

      {loading ? (
        <div className="grid gap-5 xl:grid-cols-3">
          <SkeletonCard className="h-[280px]" lines={6} />
          <SkeletonCard className="h-[280px]" lines={6} />
          <SkeletonCard className="h-[280px]" lines={6} />
        </div>
      ) : error ? (
        <EmptyState
          description={error}
          title="RFQ queue unavailable"
        />
      ) : filteredRfqs.length === 0 ? (
        <EmptyState
          actionLabel="Reset Filters"
          description={
            role === "executive"
              ? "No RFQs matched the current strategic monitor filters."
              : "No RFQs matched the current search and filter combination. Reset the controls to bring the worklist back."
          }
          onAction={() => {
            if (hasDashboardDrilldown) {
              clearDashboardDrilldown();
              return;
            }

            setSearch("");
            handleStatusChange("all");
          }}
          title={role === "executive" ? "No RFQs in the monitor" : "No RFQs in the current view"}
        />
      ) : viewMode === "cards" ? (
        <div className="grid gap-5 lg:grid-cols-2">
          {filteredRfqs.map((rfq, index) => (
            <RFQCard key={rfq.id} index={index} rfq={rfq} />
          ))}
        </div>
      ) : (
        <RFQTable items={filteredRfqs} />
      )}
    </div>
  );
}
