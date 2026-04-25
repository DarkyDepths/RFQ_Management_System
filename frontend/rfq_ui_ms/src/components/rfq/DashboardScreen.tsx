"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  BarChart2,
  LineChart,
  NotebookPen,
  Radar,
  Settings2,
  Workflow,
} from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { KPICard } from "@/components/common/KPICard";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import {
  ExecutiveDistributionCard,
  ExecutiveRankedBarsCard,
  LeadershipAttentionQueueCard,
} from "@/components/rfq/ExecutiveDashboardVisuals";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiConfig } from "@/config/api";
import { getPermissions } from "@/config/role-permissions";
import { useRole } from "@/context/role-context";
import { useDashboardData } from "@/hooks/use-dashboard-data";
import { buildRfqMonitorHref } from "@/lib/executive-insights";

export function DashboardScreen() {
  const { role } = useRole();
  const permissions = getPermissions(role);
  const router = useRouter();
  const {
    analytics,
    attentionItems,
    delayDrivers,
    error,
    leadershipNotesError,
    lifecycleDistribution,
    loading,
    lossReasons,
    metrics,
  } = useDashboardData(role, permissions.canViewAnalytics);

  if (!permissions.canViewAnalytics) {
    return (
      <EmptyState
        actionLabel="Open My Assignments"
        description="Analytics stay with executive and manager roles. Estimator work remains centered on scoped RFQ assignments."
        onAction={() => router.push("/overview")}
        title="Dashboard not available for this role"
      />
    );
  }

  if (error) {
    return (
      <EmptyState
        description={error}
        title="Dashboard unavailable"
      />
    );
  }

  if (role === "executive") {
    const buildDashboardHref = (
      filters: Parameters<typeof buildRfqMonitorHref>[0],
    ) => buildRfqMonitorHref({ ...filters, source: "dashboard" });

    const executiveMetrics = metrics.map((metric) => {
      if (metric.id === "active-rfqs") {
        return { ...metric, href: buildDashboardHref({ signal: "active" }) };
      }

      if (metric.id === "blocked-rfqs") {
        return { ...metric, href: buildDashboardHref({ signal: "blocked" }) };
      }

      if (metric.id === "overdue-rfqs") {
        return { ...metric, href: buildDashboardHref({ signal: "overdue" }) };
      }

      if (metric.id === "recent-losses") {
        return { ...metric, href: buildDashboardHref({ status: "lost" }) };
      }

      if (metric.id === "leadership-notes") {
        return {
          ...metric,
          href: buildDashboardHref({ leadership: "awaiting_response" }),
        };
      }

      return { ...metric, href: "/rfqs" };
    });

    const lifecycleEntries = lifecycleDistribution.map((entry) => {
      if (entry.label === "Awarded") {
        return { ...entry, href: buildDashboardHref({ status: "awarded" }) };
      }

      if (entry.label === "Lost") {
        return { ...entry, href: buildDashboardHref({ status: "lost" }) };
      }

      if (entry.label === "Cancelled") {
        return { ...entry, href: buildDashboardHref({ status: "cancelled" }) };
      }

      return { ...entry, href: buildDashboardHref({ stage: entry.label }) };
    });

    const delayDriverEntries = delayDrivers.slice(0, 5).map((entry) => ({
      ...entry,
      href: buildDashboardHref({ driver: entry.label }),
    }));

    const lossReasonEntries = lossReasons.slice(0, 5).map((entry) => ({
      ...entry,
      href: buildDashboardHref({ lossReason: entry.label, status: "lost" }),
    }));

    return (
      <div className="space-y-8 pb-12">
        <section className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h1 className="text-display text-3xl font-semibold text-foreground lg:text-4xl">
              {permissions.dashboardTitle}
            </h1>
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
              {permissions.dashboardSubtitle}
            </p>
          </div>
          <div className="flex gap-2">
            <Button asChild size="lg" variant="default">
              <Link href="/rfqs">
                Open RFQ Monitor
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </section>

        <section>
          {loading ? (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
              {Array.from({ length: 5 }).map((_, index) => (
                <SkeletonCard key={`kpi-sk-${index}`} className="h-[160px]" lines={4} />
              ))}
            </div>
          ) : (
            <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-5">
              {executiveMetrics.map((metric, index) => (
                <Link key={metric.id} className="block h-full" href={metric.href}>
                  <KPICard index={index} metric={metric} />
                </Link>
              ))}
            </div>
          )}
        </section>

        <div className="grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
          {loading ? (
            <>
              <SkeletonCard className="h-[420px]" lines={7} />
              <SkeletonCard className="h-[420px]" lines={8} />
            </>
          ) : (
            <>
              <ExecutiveDistributionCard
                entries={lifecycleEntries}
                icon={Workflow}
                subtitle="Current portfolio distribution across lifecycle stages, with direct drilldown to the RFQ monitor."
                title="Where RFQs Sit Now"
              />
              <LeadershipAttentionQueueCard
                items={attentionItems}
                leadershipNotesError={leadershipNotesError}
                title="Leadership Attention Queue"
              />
            </>
          )}
        </div>

        <div className="grid gap-6 xl:grid-cols-2">
          {loading ? (
            <>
              <SkeletonCard className="h-[360px]" lines={7} />
              <SkeletonCard className="h-[360px]" lines={7} />
            </>
          ) : (
            <>
              <ExecutiveRankedBarsCard
                emptyDescription="Delay and blocker drivers will appear here as soon as RFQs start carrying risk signals."
                emptyTitle="No delay drivers captured"
                entries={delayDriverEntries}
                icon={AlertTriangle}
                subtitle="Primary blocker and delay drivers across the visible executive portfolio."
                title="Top Delay / Blocker Drivers"
              />
              <ExecutiveRankedBarsCard
                emptyDescription="Loss reasons will populate once RFQs close with a captured rationale."
                emptyTitle="No loss reasons captured"
                entries={lossReasonEntries}
                icon={NotebookPen}
                subtitle="Recorded rationale behind recent closed-lost RFQs, with traceable drilldown to source records."
                title="Loss Reason Distribution"
              />
            </>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-display text-3xl font-semibold text-foreground lg:text-4xl">
            {permissions.dashboardTitle}
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {permissions.dashboardSubtitle}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" size="lg">
            <Settings2 className="mr-2 h-4 w-4" />
            Customize View
          </Button>
        </div>
      </section>

      <section>
        {loading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, index) => (
              <SkeletonCard key={`kpi-sk-${index}`} className="h-[160px]" lines={4} />
            ))}
          </div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {metrics.map((metric, index) => (
              <KPICard key={metric.id} index={index} metric={metric} />
            ))}
          </div>
        )}
      </section>

      <div className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="space-y-6">
          <div className="surface-panel p-6 h-[420px] flex flex-col">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <div className="section-kicker">
                  <BarChart2 className="h-3.5 w-3.5" />
                  Manager Analytics
                </div>
                <h2 className="mt-2 text-lg font-semibold text-foreground">
                  Operational Conversion Metrics
                </h2>
              </div>
            </div>

            {loading || !analytics ? (
              <div className="grid flex-1 gap-4 md:grid-cols-2">
                <SkeletonCard className="h-full" lines={4} />
                <SkeletonCard className="h-full" lines={4} />
                <SkeletonCard className="h-full" lines={4} />
                <SkeletonCard className="h-full" lines={4} />
              </div>
            ) : (
              <div className="grid flex-1 gap-4 md:grid-cols-2">
                {analytics.metrics.map((metric, index) => (
                  <div
                    key={metric.id}
                    className="rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]"
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-semibold text-foreground">
                        {metric.label}
                      </div>
                      <Badge variant={metric.isAvailable ? metric.tone : "pending"}>
                        {metric.displayValue}
                      </Badge>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                      {metric.helper}
                    </p>
                    {metric.isAvailable && metric.value !== null ? (
                      <div className="mt-4 h-2 overflow-hidden rounded-full bg-muted/50">
                        <motion.div
                          animate={{ width: `${Math.max(6, Math.min(metric.value, 100))}%` }}
                          className="h-full rounded-full bg-primary"
                          initial={{ width: 0 }}
                          transition={{ delay: index * 0.08, duration: 0.5 }}
                        />
                      </div>
                    ) : (
                      <div className="mt-4 rounded-xl border border-dashed border-border px-3 py-2 text-xs text-muted-foreground">
                        Awaiting truthful source data.
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="surface-panel p-6">
            <div className="mb-6 flex items-center justify-between">
              <div>
                <div className="section-kicker">
                  <LineChart className="h-3.5 w-3.5" />
                  Client Breakdown
                </div>
                <h2 className="mt-2 text-lg font-semibold text-foreground">
                  RFQ Volume by Client
                </h2>
              </div>
            </div>

            {loading || !analytics ? (
              <SkeletonCard className="h-[240px]" lines={6} />
            ) : analytics.byClient.length === 0 ? (
              <EmptyState
                description="The manager analytics endpoint did not return any client breakdown rows."
                title="No client analytics available"
              />
            ) : (
              <div className="space-y-3">
                {analytics.byClient.map((entry, index) => (
                  <div
                    key={`${entry.client}-${index}`}
                    className="rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]"
                  >
                    <div className="flex items-center justify-between text-xs font-medium">
                      <span className="text-foreground">{entry.client}</span>
                      <span className="text-muted-foreground">
                        {entry.rfqCount} RFQs
                      </span>
                    </div>
                    <div className="mt-3 flex items-center justify-between gap-3">
                      <div className="h-3 flex-1 overflow-hidden rounded-full bg-muted/40">
                        {entry.isMarginAvailable && entry.avgMarginValue !== null ? (
                          <motion.div
                            animate={{
                              width: `${Math.max(8, Math.min(entry.avgMarginValue, 100))}%`,
                            }}
                            className="h-full rounded-full bg-amber-500"
                            initial={{ width: 0 }}
                            transition={{ delay: index * 0.08, duration: 0.45 }}
                          />
                        ) : null}
                      </div>
                      <Badge variant={entry.isMarginAvailable ? "gold" : "pending"}>
                        {entry.avgMarginLabel}
                        {entry.isMarginAvailable ? " margin" : ""}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <div>
          <motion.div
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
            initial={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.2 }}
          >
            <div className="surface-panel p-6 h-full flex flex-col">
              <div className="flex items-center justify-between">
                <div>
                  <div className="section-kicker">
                    <Radar className="h-3.5 w-3.5" />
                    Intelligence Status
                  </div>
                  <h2 className="mt-3 text-lg font-semibold text-foreground">
                    Portfolio Intelligence
                  </h2>
                </div>
                <Badge variant={apiConfig.useMockData ? "gold" : "pending"}>
                  {apiConfig.useMockData ? "Demo Only" : "Unavailable"}
                </Badge>
              </div>

              <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
                {apiConfig.useMockData
                  ? "Portfolio intelligence remains demo-driven in this phase so the dashboard stays non-breaking while manager analytics are wired live."
                  : "Live portfolio intelligence is intentionally not connected in Phase 1. This dashboard now shows manager-owned analytics only."}
              </p>

              <div className="mt-6 rounded-2xl border border-border bg-muted/20 p-4 dark:bg-white/[0.02]">
                <div className="text-sm font-medium text-foreground">
                  Current phase boundary
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
                  Intelligence readiness, confidence, and portfolio posture stay out of live mode until the intelligence contracts are wired truthfully.
                </p>
              </div>

              <div className="mt-auto pt-8 flex flex-col gap-3">
                <Button asChild variant="default" className="w-full">
                  <Link href="/rfqs">
                    Open RFQ Queue
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Link>
                </Button>
                {role === "manager" ? (
                  <Button asChild variant="secondary" className="w-full">
                    <Link href="/overview">Go to Operational Manager Queue</Link>
                  </Button>
                ) : null}
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
