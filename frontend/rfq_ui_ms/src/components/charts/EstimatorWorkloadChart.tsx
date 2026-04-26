"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { CalendarClock, Flame } from "lucide-react";

import { SummaryChart } from "@/components/charts/SummaryChart";
import { Badge } from "@/components/ui/badge";
import { buildEstimatorWorkloadSeries } from "@/lib/chart-aggregations";
import type { RfqCardModel } from "@/models/manager/rfq";

export function EstimatorWorkloadChart({ rfqs }: { rfqs: RfqCardModel[] }) {
  const data = useMemo(() => buildEstimatorWorkloadSeries(rfqs, 14), [rfqs]);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 110, damping: 22 }}
      className="surface-panel relative overflow-hidden p-6 lg:p-8"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-amber-500/[0.05] to-transparent" />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="section-kicker">
            <CalendarClock className="h-3.5 w-3.5" strokeWidth={1.75} />
            Workload Density
          </div>
          <h2 className="mt-2 text-display text-2xl font-semibold tracking-tight text-foreground">
            Next 14 days, weighted by priority
          </h2>
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-muted-foreground">
            Daily load{" "}
            <code className="rounded bg-muted px-1 font-mono text-[0.7rem] text-foreground/80 dark:bg-white/[0.04]">
              L(d) = Σ w(rfq)
            </code>{" "}
            where{" "}
            <code className="rounded bg-muted px-1 font-mono text-[0.7rem] text-foreground/80 dark:bg-white/[0.04]">
              w = critical·3 + high·2 + normal·1
            </code>
            . Overdue items pile onto today.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <WorkloadStat label="Assigned" value={data.totals.total} tone="steel" />
          <WorkloadStat
            label="Critical"
            value={data.totals.critical}
            tone="rose"
            icon={<Flame className="h-3 w-3" strokeWidth={2} />}
          />
          <WorkloadStat
            label="Overdue"
            value={data.totals.overdue}
            tone={data.totals.overdue > 0 ? "rose" : "emerald"}
          />
        </div>
      </div>

      <div className="relative mt-6">
        <SummaryChart
          series={data.series}
          xLabels={data.xLabels}
          height={240}
          variant="area"
          emptyHint="No assigned RFQs in the 14-day window."
        />
      </div>
    </motion.section>
  );
}

function WorkloadStat({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: number;
  tone: "rose" | "emerald" | "steel";
  icon?: React.ReactNode;
}) {
  return (
    <div className="surface-quiet min-w-[100px] px-3.5 py-2.5">
      <div className="flex items-center gap-1.5">
        {icon ? <span className="text-muted-foreground">{icon}</span> : null}
        <span className="text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          {label}
        </span>
      </div>
      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="font-mono tabular-nums text-xl font-semibold text-foreground">
          {value}
        </span>
        <Badge variant={tone} className="hidden sm:inline-flex">
          {tone === "rose" ? "Hot" : tone === "emerald" ? "Clear" : "All"}
        </Badge>
      </div>
    </div>
  );
}
