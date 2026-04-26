"use client";

import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { TrendingUp, Layers, Hash } from "lucide-react";

import { SummaryChart } from "@/components/charts/SummaryChart";
import { Badge } from "@/components/ui/badge";
import { buildManagerPipelineSeries } from "@/lib/chart-aggregations";
import { cn } from "@/lib/utils";
import type { RfqCardModel } from "@/models/manager/rfq";

type View = "value" | "count";

function formatSarShort(value: number): string {
  if (value >= 1_000_000_000)
    return `${(value / 1_000_000_000).toFixed(2)}B`;
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(0)}K`;
  return `${Math.round(value)}`;
}

export function ManagerPipelineChart({ rfqs }: { rfqs: RfqCardModel[] }) {
  const [view, setView] = useState<View>("value");
  const data = useMemo(() => buildManagerPipelineSeries(rfqs), [rfqs]);

  const effectiveView = !data.hasValueData ? "count" : view;
  const series = effectiveView === "value" ? [data.valueSeries] : [data.countSeries];
  const yFormatter =
    effectiveView === "value"
      ? (v: number) => formatSarShort(v)
      : (v: number) => `${Math.round(v)}`;

  return (
    <motion.section
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: "spring", stiffness: 110, damping: 22 }}
      className="surface-panel relative overflow-hidden p-6 lg:p-8"
    >
      <div className="pointer-events-none absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-steel-500/[0.05] to-transparent" />

      <div className="relative flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="section-kicker">
            <Layers className="h-3.5 w-3.5" strokeWidth={1.75} />
            Pipeline Funnel
          </div>
          <h2 className="mt-2 text-display text-2xl font-semibold tracking-tight text-foreground">
            Bid value across lifecycle states
          </h2>
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-muted-foreground">
            Aggregating <code className="rounded bg-muted px-1 font-mono text-[0.7rem] text-foreground/80 dark:bg-white/[0.04]">Σ valueSar</code>{" "}
            grouped by lifecycle status, with win rate computed as{" "}
            <code className="rounded bg-muted px-1 font-mono text-[0.7rem] text-foreground/80 dark:bg-white/[0.04]">
              awarded / (awarded + lost)
            </code>
            .
          </p>
        </div>

        <div className="flex items-center gap-2">
          <ViewToggle
            value={view}
            disabled={!data.hasValueData}
            onChange={setView}
          />
        </div>
      </div>

      <div className="relative mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <PipelineStat
          label="Pipeline Value"
          value={`SAR ${formatSarShort(data.totals.pipelineValue)}`}
          tone="steel"
        />
        <PipelineStat
          label="Awarded"
          value={`SAR ${formatSarShort(data.totals.awardedValue)}`}
          tone="emerald"
        />
        <PipelineStat
          label="Lost"
          value={`SAR ${formatSarShort(data.totals.lostValue)}`}
          tone="rose"
        />
        <PipelineStat
          label="Win Rate"
          value={`${data.totals.winRate.toFixed(1)}%`}
          tone={
            data.totals.winRate >= 50
              ? "emerald"
              : data.totals.winRate >= 25
                ? "amber"
                : "rose"
          }
        />
      </div>

      <div className="relative mt-6">
        <SummaryChart
          series={series}
          xLabels={data.valueSeries.points.map((p) => p.xLabel)}
          height={260}
          variant="bars"
          yFormatter={yFormatter}
          emptyHint={
            effectiveView === "value"
              ? "No bid-value data in current scope."
              : "No RFQs in current scope."
          }
        />
      </div>
    </motion.section>
  );
}

function ViewToggle({
  value,
  disabled,
  onChange,
}: {
  value: View;
  disabled: boolean;
  onChange: (next: View) => void;
}) {
  return (
    <div className="flex rounded-xl border border-border bg-muted/40 p-1 dark:bg-white/[0.025]">
      <ToggleButton
        active={value === "value" && !disabled}
        disabled={disabled}
        onClick={() => onChange("value")}
        icon={<TrendingUp className="h-3.5 w-3.5" strokeWidth={2} />}
        label="Value"
      />
      <ToggleButton
        active={value === "count" || disabled}
        onClick={() => onChange("count")}
        icon={<Hash className="h-3.5 w-3.5" strokeWidth={2} />}
        label="Count"
      />
    </div>
  );
}

function ToggleButton({
  active,
  disabled,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  disabled?: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        "relative flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs font-medium transition-colors",
        active
          ? "bg-card text-foreground shadow-[0_1px_0_hsl(0_0%_100%/0.06)_inset,0_4px_12px_-4px_hsl(220_30%_20%/0.12)] dark:bg-white/[0.08]"
          : "text-muted-foreground hover:text-foreground",
        disabled && "cursor-not-allowed opacity-50",
      )}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function PipelineStat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone: "steel" | "emerald" | "rose" | "amber";
}) {
  return (
    <div className="surface-quiet px-3.5 py-2.5">
      <div className="text-[0.62rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {label}
      </div>
      <div className="mt-1 flex items-baseline justify-between gap-2">
        <span className="font-mono tabular-nums text-base font-semibold text-foreground">
          {value}
        </span>
        <Badge variant={tone} className="text-[0.6rem]">
          {tone === "emerald"
            ? "Won"
            : tone === "rose"
              ? "Lost"
              : tone === "amber"
                ? "Mixed"
                : "Total"}
        </Badge>
      </div>
    </div>
  );
}
