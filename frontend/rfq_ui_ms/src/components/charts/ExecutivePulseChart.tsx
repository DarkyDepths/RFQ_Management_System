"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { Activity, ShieldAlert } from "lucide-react";

import { SummaryChart } from "@/components/charts/SummaryChart";
import { Badge } from "@/components/ui/badge";
import { buildExecutivePulseSeries } from "@/lib/chart-aggregations";
import type { RfqCardModel } from "@/models/manager/rfq";

export function ExecutivePulseChart({ rfqs }: { rfqs: RfqCardModel[] }) {
  const data = useMemo(() => buildExecutivePulseSeries(rfqs), [rfqs]);

  const riskShare =
    data.totals.total === 0
      ? 0
      : Math.round((data.totals.atRisk / data.totals.total) * 100);

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 110, damping: 22 }}
      className="surface-panel relative overflow-hidden p-6 lg:p-8"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-primary/[0.06] to-transparent" />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="section-kicker">
            <Activity className="h-3.5 w-3.5" strokeWidth={1.75} />
            Portfolio Pulse
          </div>
          <h2 className="mt-2 text-display text-2xl font-semibold tracking-tight text-foreground">
            Risk distribution across lifecycle
          </h2>
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-muted-foreground">
            Each RFQ scored by{" "}
            <code className="rounded bg-muted px-1 font-mono text-[0.7rem] text-foreground/80 dark:bg-white/[0.04]">
              R = 3·blocked + 2·overdue + intel_failed + critical
            </code>
            , then bucketed by lifecycle progress. R≥1 marks an at-risk pursuit.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <PulseStat
            label="Healthy"
            value={data.totals.healthy}
            tone="emerald"
          />
          <PulseStat label="At Risk" value={data.totals.atRisk} tone="rose" />
          <PulseStat
            label="Risk Share"
            value={`${riskShare}%`}
            tone={riskShare > 30 ? "rose" : riskShare > 15 ? "amber" : "steel"}
            icon={<ShieldAlert className="h-3 w-3" strokeWidth={2} />}
          />
        </div>
      </div>

      <div className="relative mt-6">
        <SummaryChart
          series={data.series}
          xLabels={data.xLabels}
          height={260}
          variant="area"
          emptyHint="No portfolio data yet."
        />
      </div>
    </motion.section>
  );
}

function PulseStat({
  label,
  value,
  tone,
  icon,
}: {
  label: string;
  value: number | string;
  tone: "emerald" | "rose" | "amber" | "steel";
  icon?: React.ReactNode;
}) {
  return (
    <div className="surface-quiet min-w-[112px] px-3.5 py-2.5">
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
          {tone === "emerald"
            ? "Stable"
            : tone === "rose"
              ? "Watch"
              : tone === "amber"
                ? "Elevated"
                : "Tracked"}
        </Badge>
      </div>
    </div>
  );
}
