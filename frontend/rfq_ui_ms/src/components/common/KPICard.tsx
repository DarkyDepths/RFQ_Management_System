"use client";

import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

import type { KPIMetricModel } from "@/models/ui/dashboard";
import { cn } from "@/lib/utils";

const toneAccent: Record<KPIMetricModel["tone"], string> = {
  steel: "from-steel-500/20 via-steel-500/5",
  gold: "from-gold-500/22 via-gold-500/5",
  emerald: "from-emerald-500/22 via-emerald-500/5",
  amber: "from-amber-500/22 via-amber-500/5",
};

const toneText: Record<KPIMetricModel["tone"], string> = {
  steel: "text-steel-600 dark:text-steel-300",
  gold: "text-gold-600 dark:text-gold-300",
  emerald: "text-emerald-600 dark:text-emerald-300",
  amber: "text-amber-600 dark:text-amber-300",
};

const toneTrend: Record<KPIMetricModel["trendDirection"], string> = {
  up: "text-emerald-600 dark:text-emerald-300",
  down: "text-rose-600 dark:text-rose-300",
  steady: "text-muted-foreground",
};

function TrendIcon({
  direction,
}: {
  direction: KPIMetricModel["trendDirection"];
}) {
  const Icon =
    direction === "up"
      ? ArrowUpRight
      : direction === "down"
        ? ArrowDownRight
        : ArrowRight;
  return <Icon className="h-3.5 w-3.5" strokeWidth={2} />;
}

export function KPICard({
  metric,
  index = 0,
}: {
  metric: KPIMetricModel;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 120,
        damping: 22,
        delay: index * 0.06,
      }}
      whileHover={{ y: -2 }}
      className="surface-panel surface-panel-hover group relative h-full overflow-hidden"
    >
      {/* Top accent wash */}
      <div
        className={cn(
          "pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b to-transparent opacity-80 dark:opacity-100",
          toneAccent[metric.tone],
        )}
      />
      {/* Hover halo */}
      <div className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition-opacity duration-300 group-hover:opacity-100 dark:bg-[radial-gradient(circle_at_top,hsl(var(--primary)/0.06),transparent_60%)]" />

      <div className="relative p-6">
        <div className="flex items-start justify-between gap-3">
          <div className={cn("section-kicker", toneText[metric.tone])}>
            {metric.label}
          </div>
        </div>

        <div className="mt-4 flex items-baseline gap-2">
          <div className="font-mono tabular-nums text-[2rem] font-semibold leading-none tracking-tight text-foreground">
            {metric.value}
          </div>
        </div>

        <p className="mt-2 text-[0.8rem] leading-relaxed text-muted-foreground">
          {metric.helper}
        </p>

        <div
          className={cn(
            "mt-5 inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/40 px-2.5 py-1 text-[0.7rem] font-medium dark:bg-white/[0.03]",
            toneTrend[metric.trendDirection],
          )}
        >
          <TrendIcon direction={metric.trendDirection} />
          <span className="text-foreground/90">{metric.trendLabel}</span>
        </div>
      </div>
    </motion.div>
  );
}
