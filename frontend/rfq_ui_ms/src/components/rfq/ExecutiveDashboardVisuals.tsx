"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";
import { ArrowRight, ListChecks } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type {
  ExecutiveAggregateEntry,
  ExecutiveVisualTone,
} from "@/lib/executive-insights";
import type { ExecutiveAttentionItem } from "@/hooks/use-dashboard-data";

interface DrilldownEntry extends ExecutiveAggregateEntry {
  href: string;
}

const fallbackTones: ExecutiveVisualTone[] = ["steel", "gold", "amber", "emerald", "rose"];

const barToneClasses: Record<ExecutiveVisualTone, string> = {
  amber: "bg-amber-500/80",
  emerald: "bg-emerald-500/80",
  gold: "bg-gold-500/80",
  rose: "bg-rose-500/80",
  steel: "bg-steel-500/80",
};

const rowToneClasses: Record<ExecutiveVisualTone, string> = {
  amber: "border-amber-500/25 bg-amber-500/8",
  emerald: "border-emerald-500/25 bg-emerald-500/8",
  gold: "border-gold-500/25 bg-gold-500/8",
  rose: "border-rose-500/25 bg-rose-500/8",
  steel: "border-steel-500/25 bg-steel-500/8",
};

function resolveTone(
  tone: ExecutiveVisualTone | undefined,
  index: number,
) {
  return tone ?? fallbackTones[index % fallbackTones.length];
}

function formatShare(count: number, total: number) {
  if (total <= 0) {
    return "0%";
  }

  const share = (count / total) * 100;
  return `${Math.round(share)}%`;
}

function SectionHeader({
  badge,
  icon: Icon,
  subtitle,
  title,
}: {
  badge?: ReactNode;
  icon: LucideIcon;
  subtitle: string;
  title: string;
}) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div>
        <div className="section-kicker">
          <Icon className="h-3.5 w-3.5" />
          Executive Visual
        </div>
        <h2 className="mt-2 text-lg font-semibold text-foreground">{title}</h2>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted-foreground">
          {subtitle}
        </p>
      </div>
      {badge}
    </div>
  );
}

export function ExecutiveDistributionCard({
  entries,
  icon,
  subtitle,
  title,
}: {
  entries: DrilldownEntry[];
  icon: LucideIcon;
  subtitle: string;
  title: string;
}) {
  const total = entries.reduce((sum, entry) => sum + entry.count, 0);

  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="surface-panel p-6"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.2, delay: 0.03 }}
    >
      <SectionHeader icon={icon} subtitle={subtitle} title={title} />

      {entries.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            description="No RFQs are available yet for this executive portfolio view."
            title="No lifecycle distribution available"
          />
        </div>
      ) : (
        <>
          <div className="mt-6 overflow-hidden rounded-full border border-border bg-muted/30">
            <div className="flex h-5">
              {entries.map((entry, index) => {
                const tone = resolveTone(entry.tone, index);
                const width = `${(entry.count / total) * 100}%`;

                return (
                  <Link
                    key={`${entry.label}-${index}`}
                    aria-label={`Open ${entry.label} RFQs`}
                    className="relative block h-full"
                    href={entry.href}
                    style={{ width }}
                    title={`${entry.label}: ${entry.count}`}
                  >
                    <motion.div
                      animate={{ width: "100%" }}
                      className={cn("h-full", barToneClasses[tone])}
                      initial={{ width: 0 }}
                      transition={{ delay: index * 0.06, duration: 0.35 }}
                    />
                  </Link>
                );
              })}
            </div>
          </div>

          <div className="mt-6 space-y-3">
            {entries.map((entry, index) => {
              const tone = resolveTone(entry.tone, index);

              return (
                <Link
                  key={`${entry.label}-${index}`}
                  className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-muted/15 px-4 py-3 transition-colors hover:bg-muted/25 dark:bg-white/[0.02]"
                  href={entry.href}
                >
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-foreground">{entry.label}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      {formatShare(entry.count, total)} of visible RFQs
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={tone}>{entry.count}</Badge>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </Link>
              );
            })}
          </div>
        </>
      )}
    </motion.section>
  );
}

export function ExecutiveRankedBarsCard({
  entries,
  emptyDescription,
  emptyTitle,
  icon,
  subtitle,
  title,
}: {
  entries: DrilldownEntry[];
  emptyDescription: string;
  emptyTitle: string;
  icon: LucideIcon;
  subtitle: string;
  title: string;
}) {
  const maxCount = Math.max(...entries.map((entry) => entry.count), 0);

  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="surface-panel p-6"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.2, delay: 0.08 }}
    >
      <SectionHeader icon={icon} subtitle={subtitle} title={title} />

      {entries.length === 0 ? (
        <div className="mt-6">
          <EmptyState description={emptyDescription} title={emptyTitle} />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          {entries.map((entry, index) => {
            const tone = resolveTone(entry.tone, index);
            const width =
              maxCount > 0 ? `${Math.max(12, (entry.count / maxCount) * 100)}%` : "0%";

            return (
              <Link
                key={`${entry.label}-${index}`}
                className={cn(
                  "block rounded-2xl border px-4 py-3 transition-colors hover:bg-muted/20 dark:bg-white/[0.02]",
                  rowToneClasses[tone],
                )}
                href={entry.href}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="text-sm font-semibold text-foreground">{entry.label}</div>
                    <div className="mt-1 text-xs text-muted-foreground">
                      Drill into the RFQ monitor for source records.
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={tone}>{entry.count}</Badge>
                    <ArrowRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </div>
                <div className="mt-3 h-2 overflow-hidden rounded-full bg-muted/40">
                  <motion.div
                    animate={{ width }}
                    className={cn("h-full rounded-full", barToneClasses[tone])}
                    initial={{ width: 0 }}
                    transition={{ delay: index * 0.07, duration: 0.38 }}
                  />
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </motion.section>
  );
}

export function LeadershipAttentionQueueCard({
  items,
  leadershipNotesError,
  title,
}: {
  items: ExecutiveAttentionItem[];
  leadershipNotesError?: string | null;
  title: string;
}) {
  return (
    <motion.section
      animate={{ opacity: 1, y: 0 }}
      className="surface-panel p-6"
      initial={{ opacity: 0, y: 14 }}
      transition={{ duration: 0.2, delay: 0.05 }}
    >
      <SectionHeader
        badge={<Badge variant="steel">{items.length} shown</Badge>}
        icon={ListChecks}
        subtitle="Blocked, overdue, lost, or escalated RFQs that merit strategic review now."
        title={title}
      />

      {leadershipNotesError ? (
        <div className="mt-5 rounded-2xl border border-amber-500/25 bg-amber-500/10 p-4 text-sm text-amber-700 dark:text-amber-300">
          {leadershipNotesError}
        </div>
      ) : null}

      {items.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            description="No RFQs are currently signaling blocked, overdue, loss-review, or leadership-attention posture."
            title="Nothing needs immediate leadership review"
          />
        </div>
      ) : (
        <div className="mt-6 space-y-3">
          <div className="hidden rounded-2xl border border-border bg-muted/20 px-4 py-3 text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground lg:grid lg:grid-cols-[1.6fr_0.8fr_0.8fr_0.8fr_0.9fr] lg:gap-3 dark:bg-white/[0.02]">
            <span>RFQ</span>
            <span>Signal</span>
            <span>Stage</span>
            <span>Due</span>
            <span>Leadership Note</span>
          </div>

          {items.map((item) => (
            <Link
              key={item.rfq.id}
              className="grid gap-4 rounded-2xl border border-border bg-muted/15 px-4 py-4 transition-colors hover:bg-muted/25 lg:grid-cols-[1.6fr_0.8fr_0.8fr_0.8fr_0.9fr] lg:items-center lg:gap-3 dark:bg-white/[0.02]"
              href={`/rfqs/${item.rfq.id}`}
            >
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold text-foreground">{item.rfq.title}</div>
                <div className="mt-1 text-xs text-muted-foreground">
                  {item.rfq.client} · {item.rfq.rfqCode ?? item.rfq.id}
                </div>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground lg:hidden">
                  {item.reason}
                </p>
              </div>

              <div>
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground lg:hidden">
                  Signal
                </div>
                <Badge variant={item.tone}>{item.signalLabel}</Badge>
              </div>

              <div>
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground lg:hidden">
                  Stage
                </div>
                <div className="text-sm font-medium text-foreground">{item.rfq.stageLabel}</div>
              </div>

              <div>
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground lg:hidden">
                  Due
                </div>
                <div className="text-sm font-mono text-foreground">{item.rfq.dueLabel}</div>
              </div>

              <div className="space-y-2">
                <div className="text-[0.68rem] font-semibold uppercase tracking-[0.16em] text-muted-foreground lg:hidden">
                  Leadership Note
                </div>
                {item.leadershipThreadStateLabel ? (
                  <Badge variant={item.leadershipThreadTone ?? "steel"}>
                    {item.leadershipThreadStateLabel}
                  </Badge>
                ) : (
                  <Badge variant="outline">No open note</Badge>
                )}
                <div className="hidden text-xs text-muted-foreground lg:block">{item.reason}</div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </motion.section>
  );
}
