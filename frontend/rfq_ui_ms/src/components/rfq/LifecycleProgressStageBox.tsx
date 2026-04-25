"use client";

import { cn } from "@/lib/utils";
import type { ManagerRfqStatus } from "@/models/manager/rfq";
import {
  getLifecycleProgressBaseClasses,
  getLifecycleProgressFillClasses,
  getLifecycleProgressFillPercent,
} from "@/utils/lifecycle-progress-visual";

export function LifecycleProgressStageBox({
  stageLabel,
  rfqProgress,
  status,
  blocked = false,
  compact = false,
}: {
  stageLabel: string;
  rfqProgress: number;
  status: ManagerRfqStatus;
  blocked?: boolean;
  compact?: boolean;
}) {
  const fillPercent = getLifecycleProgressFillPercent(rfqProgress, status);
  const baseClasses = getLifecycleProgressBaseClasses();
  const fillClasses = getLifecycleProgressFillClasses(rfqProgress, status);
  const fillCoversAll = fillPercent >= 100;

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl border shadow-[inset_0_1px_0_rgba(255,255,255,0.72)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]",
        baseClasses,
        blocked || status === "lost" || status === "cancelled"
          ? "border-rose-300/90 dark:border-rose-500/45"
          : "border-emerald-200/80 dark:border-emerald-900/60",
      )}
    >
      {fillPercent > 0 ? (
        <div
          aria-hidden="true"
          className={cn(
            "absolute inset-y-0 left-0 transition-[width] duration-300 ease-out",
            fillClasses,
            fillCoversAll ? "rounded-[inherit]" : "rounded-l-[inherit]",
          )}
          style={{ width: `${fillPercent}%` }}
        />
      ) : null}
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(180deg,rgba(255,255,255,0.28)_0%,rgba(255,255,255,0.08)_36%,rgba(255,255,255,0)_100%)] dark:bg-[linear-gradient(180deg,rgba(255,255,255,0.05)_0%,rgba(255,255,255,0.015)_36%,rgba(255,255,255,0)_100%)]"
      />
      <div
        className={cn(
          "relative flex items-center justify-between gap-3",
          compact ? "px-3 py-2.5" : "px-4 py-3.5",
        )}
      >
        <div className="min-w-0">
          <div className="text-[0.62rem] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            Current Stage
          </div>
          <div
            className={cn(
              "mt-1 truncate font-semibold text-slate-900 dark:text-slate-50",
              compact ? "text-sm" : "text-base",
            )}
          >
            {stageLabel}
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[0.62rem] font-semibold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
            Lifecycle
          </div>
          <div
            className={cn(
              "mt-1 font-mono font-semibold text-slate-900 dark:text-slate-50",
              compact ? "text-sm" : "text-base",
            )}
          >
            {rfqProgress}%
          </div>
        </div>
      </div>
    </div>
  );
}
