"use client";

import { ArrowDownRight, ArrowRight, ArrowUpRight } from "lucide-react";
import { motion } from "framer-motion";

import { Card, CardContent } from "@/components/ui/card";
import type { KPIMetricModel } from "@/models/ui/dashboard";
import { cn } from "@/lib/utils";

const toneStyles: Record<KPIMetricModel["tone"], string> = {
  steel: "from-steel-500/15 to-transparent text-steel-500 dark:text-steel-300",
  gold: "from-gold-500/15 to-transparent text-gold-600 dark:text-gold-300",
  emerald: "from-emerald-500/15 to-transparent text-emerald-600 dark:text-emerald-300",
  amber: "from-amber-500/15 to-transparent text-amber-600 dark:text-amber-300",
};

function TrendIcon({
  direction,
}: {
  direction: KPIMetricModel["trendDirection"];
}) {
  if (direction === "up") {
    return <ArrowUpRight className="h-4 w-4" />;
  }

  if (direction === "down") {
    return <ArrowDownRight className="h-4 w-4" />;
  }

  return <ArrowRight className="h-4 w-4" />;
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
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, delay: index * 0.08 }}
    >
      <Card className="surface-panel-hover h-full overflow-hidden">
        <CardContent className="relative p-5">
          <div
            className={cn(
              "absolute inset-x-0 top-0 h-20 bg-gradient-to-b opacity-50 dark:opacity-100",
              toneStyles[metric.tone],
            )}
          />
          <div className="relative">
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">
              {metric.label}
            </div>
            <div className="mt-3 font-mono text-3xl font-semibold tracking-tight text-foreground">
              {metric.value}
            </div>
            <p className="mt-1.5 text-[0.8rem] text-muted-foreground">{metric.helper}</p>
            <div className="mt-4 inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/30 px-2.5 py-1 text-xs font-medium text-foreground dark:bg-white/[0.03]">
              <TrendIcon direction={metric.trendDirection} />
              {metric.trendLabel}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
