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
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.06 }}
    >
      <Link className="block" href={`/rfqs/${rfq.id}`}>
        <div className="surface-panel surface-panel-hover p-5">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                {rfq.rfqCode ?? rfq.id}
              </div>
              <h3 className="mt-1 text-xl font-semibold text-foreground">
                {rfq.title}
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <RFQStatusChip status={rfq.status} />
              {blockedSignal.isBlocked ? (
                <Badge variant="rose">Blocked</Badge>
              ) : null}
              <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
            </div>
          </div>

          {rfq.summaryLine ? (
            <p className="mt-2 text-sm leading-relaxed text-muted-foreground line-clamp-2">
              {rfq.summaryLine}
            </p>
          ) : null}

          <div className="mt-4 grid gap-3 text-sm text-muted-foreground sm:grid-cols-3">
            <div className="flex items-center gap-2">
              <Building2 className="h-4 w-4 text-gold-500" />
              <span className="truncate">{rfq.client}</span>
            </div>
            <div className="flex items-center gap-2">
              <User2 className="h-4 w-4 text-steel-500" />
              <span className="truncate">{rfq.owner}</span>
            </div>
            {rfq.region ? (
              <div className="flex items-center gap-2">
                <MapPinned className="h-4 w-4 text-emerald-500" />
                <span className="truncate">{rfq.region}</span>
              </div>
            ) : null}
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {blockedSignal.isBlocked ? (
              <Badge variant="rose" className="border-transparent">
                Blocked
              </Badge>
            ) : null}
            {blockedSignal.reasonLabel ? (
              <Badge variant="gold" className="border-transparent">
                {blockedSignal.reasonLabel}
              </Badge>
            ) : null}
            {rfq.intelligenceState ? (
              <Badge variant="steel" className="opacity-80 border-transparent">
                Intel: {rfq.intelligenceState}
              </Badge>
            ) : null}
            {rfq.tags.map((tag) => (
              <Badge key={`${rfq.id}-${tag}`} variant="default">
                {tag}
              </Badge>
            ))}
          </div>

          {rfq.stageHistory.length > 0 ? (
            <div className="mt-4 rounded-xl border border-border bg-muted/30 p-4 dark:bg-white/[0.02]">
              <LifecycleProgressStageBox
                blocked={blockedSignal.isBlocked}
                rfqProgress={rfq.rfqProgress}
                stageLabel={rfq.stageLabel}
                status={rfq.status}
              />
              <div className="mt-3">
                <RFQStageTimeline compact stages={rfq.stageHistory} />
              </div>
            </div>
          ) : (
            <div className="mt-4 rounded-xl border border-border bg-muted/30 p-4 dark:bg-white/[0.02]">
              <LifecycleProgressStageBox
                blocked={blockedSignal.isBlocked}
                rfqProgress={rfq.rfqProgress}
                stageLabel={rfq.stageLabel}
                status={rfq.status}
              />
              {blockedSignal.isBlocked ? (
                <div className="mt-2 text-xs font-medium text-rose-700 dark:text-rose-300">
                  {blockedSignal.reasonLabel
                    ? `Blocked: ${blockedSignal.reasonLabel}`
                    : "Blocked: blocker reason required"}
                </div>
              ) : null}
            </div>
          )}

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4">
            {rfq.valueLabel ? (
              <div>
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                  Bid Value
                </div>
                <div className="mt-0.5 font-mono text-base font-medium text-foreground">
                  {rfq.valueLabel}
                </div>
              </div>
            ) : null}
            <div>
              <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                Due Date
              </div>
              <div className="mt-0.5 font-mono text-base font-medium text-foreground">
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
