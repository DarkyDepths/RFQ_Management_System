"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { ArrowRight, PlusSquare, Radar } from "lucide-react";

import { EstimatorWorkloadChart } from "@/components/charts/EstimatorWorkloadChart";
import { ManagerPipelineChart } from "@/components/charts/ManagerPipelineChart";
import { EmptyState } from "@/components/common/EmptyState";
import { KPICard } from "@/components/common/KPICard";
import { ReminderCenterSummaryCard } from "@/components/reminders/ReminderCenterSummaryCard";
import { SkeletonCard } from "@/components/common/SkeletonCard";
import { RFQCard } from "@/components/rfq/RFQCard";
import { RFQTable } from "@/components/rfq/RFQTable";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { apiConfig } from "@/config/api";
import { getPermissions } from "@/config/role-permissions";
import { useRole } from "@/context/role-context";
import { useOverviewData } from "@/hooks/use-overview-data";

export function RFQOverviewScreen() {
  const { role } = useRole();
  const permissions = getPermissions(role);
  const router = useRouter();
  const { activeRfqs, error, loading, metrics, rfqs } = useOverviewData(role, permissions);

  const displayRfqs = permissions.canViewAllRfqs ? rfqs : rfqs.slice(0, 3);
  const featuredCards = activeRfqs.slice(0, 3);

  if (role === "executive") {
    return (
      <EmptyState
        actionLabel="Open Dashboard"
        description="Executive access stays on the dashboard and strategic RFQ monitor rather than the operational overview."
        onAction={() => router.push("/dashboard")}
        title="Operational overview is manager-owned"
      />
    );
  }

  if (error) {
    return (
      <EmptyState
        description={error}
        title="Overview unavailable"
      />
    );
  }

  return (
    <div className="space-y-8">
      {/* ─── Page Header ─── */}
      <section className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-display text-3xl font-semibold text-foreground lg:text-4xl">
            {permissions.overviewTitle}
          </h1>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">
            {permissions.overviewSubtitle}
          </p>
        </div>
        <div className="flex gap-2">
          {permissions.primaryCta ? (
            <Button asChild size="lg" variant="default">
              <Link href={permissions.primaryCta.href}>
                <PlusSquare className="h-4 w-4" />
                {permissions.primaryCta.label}
              </Link>
            </Button>
          ) : null}
          {apiConfig.useMockData ? (
            <Button asChild size="lg" variant="secondary">
              <Link href="/rfqs/RFQ-2026-0142">
                <Radar className="h-4 w-4" />
                Featured RFQ
              </Link>
            </Button>
          ) : (
            <Button asChild size="lg" variant="secondary">
              <Link href="/rfqs">
                <Radar className="h-4 w-4" />
                {role === "manager" ? "Open Queue" : "Open Worklist"}
              </Link>
            </Button>
          )}
        </div>
      </section>

      {/* ─── KPI Strip ─── */}
      <section>
        {loading ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <SkeletonCard key={`kpi-sk-${i}`} className="h-[160px]" lines={4} />
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

      {/* ─── Role Summary Chart ─── */}
      <section>
        {loading ? (
          <SkeletonCard className="h-[420px]" lines={8} />
        ) : role === "manager" ? (
          <ManagerPipelineChart rfqs={rfqs} />
        ) : (
          <EstimatorWorkloadChart rfqs={rfqs} />
        )}
      </section>

      {/* ─── Two-Column: RFQ Cards + Intelligence Posture ─── */}
      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        {/* Left: Active RFQs */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-foreground">
              {permissions.canViewAllRfqs ? "Active RFQs" : "Assigned RFQs"}
            </h2>
            <Button asChild size="sm" variant="ghost">
              <Link href="/rfqs">
                View all
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </Button>
          </div>
          {loading ? (
            <div className="space-y-4">
              <SkeletonCard className="h-[220px]" lines={5} />
              <SkeletonCard className="h-[220px]" lines={5} />
            </div>
          ) : (
            <div className="space-y-4">
              {featuredCards.length > 0 ? (
                featuredCards.map((rfq, index) => (
                  <RFQCard key={rfq.id} index={index} rfq={rfq} />
                ))
              ) : (
                <div className="rounded-xl border border-border bg-muted/20 p-4 text-sm text-muted-foreground">
                  No active RFQs are currently available in this overview slice.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Intelligence Posture */}
        <AnimatePresence mode="wait">
          <motion.div
            key={role}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-4"
            exit={{ opacity: 0, y: -8 }}
            initial={{ opacity: 0, y: 12 }}
            transition={{ duration: 0.2 }}
          >
            {permissions.canViewPortfolio ? (
              <div className="surface-panel p-6">
                <div className="flex items-center justify-between">
                  <div>
                <div className="section-kicker">
                  <Radar className="h-3.5 w-3.5" />
                      {role === "manager" ? "Executive BI" : "Assignments Focus"}
                </div>
                <h2 className="mt-3 text-lg font-semibold text-foreground">
                      {role === "manager" ? "Dashboard Access" : "Contributor Focus"}
                </h2>
              </div>
            </div>

                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                  {role === "manager"
                    ? "The full intelligence posture, timeline tracking, and portfolio readiness overview have been moved to the primary Dashboard view."
                    : "Your overview stays centered on assigned RFQs and contributor actions. Portfolio analytics remain outside estimator scope."}
                </p>

                <div className="mt-6">
                  <Button asChild variant="secondary">
                    {role === "manager" ? (
                      <Link href="/dashboard">
                        Open Dashboard
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    ) : (
                      <Link href="/rfqs">
                        Open Worklist
                        <ArrowRight className="h-4 w-4" />
                      </Link>
                    )}
                  </Button>
                </div>
              </div>
            ) : (
              /* Worker view: action-focused card */
              <div className="surface-panel p-6">
                <div className="section-kicker">Next Actions</div>
                <h2 className="mt-3 text-lg font-semibold text-foreground">
                  Pending work items
                </h2>
                <p className="mt-3 text-sm text-muted-foreground">
                  Focus on uploads and workbook follow-up for your assigned RFQs.
                </p>
                <div className="mt-4 space-y-2">
                  <div className="stat-cell">
                    <div className="text-sm font-medium text-foreground">
                      Upload missing workbook for RFQ-2026-0138
                    </div>
                  </div>
                  <div className="stat-cell">
                    <div className="text-sm font-medium text-foreground">
                      Review parsed package for RFQ-2026-0142
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Role info card */}
            <div className="surface-panel p-5">
              <div className="flex items-center gap-2 text-xs font-medium text-muted-foreground">
                <Badge variant={role === "manager" ? "steel" : "gold"}>
                  {role === "manager" ? "Manager View" : "Estimator View"}
                </Badge>
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">
                {role === "manager"
                  ? "You see the operational portfolio queue and can create or advance RFQs. For macro intelligence, view the Dashboard."
                  : "You see assigned RFQs only. Stage truth, reminders, and portfolio controls remain manager-owned."}
              </p>
            </div>
          </motion.div>
        </AnimatePresence>
      </section>

      {/* ─── Full-Width Table ─── */}
      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">
            {permissions.canViewAllRfqs ? "All RFQs" : "Assigned Queue"}
          </h2>
        </div>
        {loading ? (
          <SkeletonCard className="h-[300px]" lines={7} />
        ) : (
          <RFQTable items={displayRfqs} />
        )}
      </section>

      {role === "manager" ? <ReminderCenterSummaryCard /> : null}
    </div>
  );
}
