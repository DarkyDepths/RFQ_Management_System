import Link from "next/link";
import { ArrowUpRight, Building2, MapPinned, User2 } from "lucide-react";
import { motion } from "framer-motion";

import { LifecycleProgressStageBox } from "@/components/rfq/LifecycleProgressStageBox";
import { RFQStageTimeline } from "@/components/rfq/RFQStageTimeline";
import { RFQStatusChip } from "@/components/rfq/RFQStatusChip";
import { Badge } from "@/components/ui/badge";
import type { RfqCardModel } from "@/models/manager/rfq";
import { getRfqBlockedSignal } from "@/utils/blocker-signal";

export function RFQCard({
  rfq,
  index = 0,
}: {
  rfq: RfqCardModel;
  index?: number;
}) {
  const blockedSignal = getRfqBlockedSignal(rfq);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        type: "spring",
        stiffness: 110,
        damping: 22,
        delay: index * 0.05,
      }}
    >
      <Link className="block group" href={`/rfqs/${rfq.id}`}>
        <div className="surface-panel surface-panel-hover relative overflow-hidden p-6">
          {/* Top hairline accent on hover */}
          <div className="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="font-mono text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                {rfq.rfqCode ?? rfq.id}
              </div>
              <h3 className="mt-1.5 text-display text-xl font-semibold leading-tight tracking-tight text-foreground">
                {rfq.title}
              </h3>
            </div>
            <div className="flex shrink-0 items-center gap-2">
              <RFQStatusChip status={rfq.status} />
              <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-transparent text-muted-foreground transition-all group-hover:border-border group-hover:bg-muted/50 group-hover:text-foreground">
                <ArrowUpRight className="h-4 w-4" strokeWidth={1.75} />
              </div>
            </div>
          </div>

          {rfq.summaryLine ? (
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground line-clamp-2">
              {rfq.summaryLine}
            </p>
          ) : null}

          <div className="mt-5 grid gap-3 text-sm sm:grid-cols-3">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Building2 className="h-3.5 w-3.5 shrink-0 text-gold-500 dark:text-gold-300" strokeWidth={1.75} />
              <span className="truncate text-foreground/80">{rfq.client}</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <User2 className="h-3.5 w-3.5 shrink-0 text-steel-500 dark:text-steel-300" strokeWidth={1.75} />
              <span className="truncate text-foreground/80">{rfq.owner}</span>
            </div>
            {rfq.region ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPinned className="h-3.5 w-3.5 shrink-0 text-emerald-500 dark:text-emerald-300" strokeWidth={1.75} />
                <span className="truncate text-foreground/80">{rfq.region}</span>
              </div>
            ) : null}
          </div>

          {(blockedSignal.isBlocked || blockedSignal.reasonLabel || rfq.intelligenceState || rfq.tags.length) ? (
            <div className="mt-4 flex flex-wrap gap-1.5">
              {blockedSignal.isBlocked ? (
                <Badge variant="rose">Blocked</Badge>
              ) : null}
              {blockedSignal.reasonLabel ? (
                <Badge variant="amber">{blockedSignal.reasonLabel}</Badge>
              ) : null}
              {rfq.intelligenceState ? (
                <Badge variant="steel">Intel · {rfq.intelligenceState}</Badge>
              ) : null}
              {rfq.tags.map((tag) => (
                <Badge key={`${rfq.id}-${tag}`} variant="pending">
                  {tag}
                </Badge>
              ))}
            </div>
          ) : null}

          <div className="mt-5 surface-quiet p-4">
            <LifecycleProgressStageBox
              blocked={blockedSignal.isBlocked}
              rfqProgress={rfq.rfqProgress}
              stageLabel={rfq.stageLabel}
              status={rfq.status}
            />
            {rfq.stageHistory.length > 0 ? (
              <div className="mt-3">
                <RFQStageTimeline compact stages={rfq.stageHistory} />
              </div>
            ) : blockedSignal.isBlocked ? (
              <div className="mt-2 text-xs font-medium text-rose-700 dark:text-rose-300">
                {blockedSignal.reasonLabel
                  ? `Blocked: ${blockedSignal.reasonLabel}`
                  : "Blocked: blocker reason required"}
              </div>
            ) : null}
          </div>

          <div className="mt-5 flex flex-wrap items-end justify-between gap-4 border-t border-border/60 pt-4">
            {rfq.valueLabel ? (
              <div>
                <div className="text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                  Bid Value
                </div>
                <div className="mt-1 font-mono tabular-nums text-base font-medium text-foreground">
                  {rfq.valueLabel}
                </div>
              </div>
            ) : null}
            <div>
              <div className="text-[0.62rem] font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                Due Date
              </div>
              <div className="mt-1 font-mono tabular-nums text-base font-medium text-foreground">
                {rfq.dueLabel}
              </div>
            </div>
            <div className="max-w-[12rem] text-right text-sm font-medium text-primary">
              {rfq.nextAction ?? `Lifecycle ${rfq.rfqProgress}%`}
            </div>
          </div>
        </div>
      </Link>
    </motion.div>
  );
}
