"use client";

import { motion } from "framer-motion";
import { Check, CircleSlash, Clock, X } from "lucide-react";

import type { StageProgressModel } from "@/models/manager/stage";
import { cn } from "@/lib/utils";

export function RFQStageTimeline({
  stages,
  compact = false,
}: {
  stages: StageProgressModel[];
  compact?: boolean;
}) {
  return (
    <div className="relative w-full overflow-hidden">
      
      <div
        className={cn(
          "hide-scrollbar flex items-center overflow-x-auto pb-1 gap-2",
          compact && "gap-1.5"
        )}
      >
        {stages.map((stage, index) => {
          const isActive = stage.state === "active";
          const isBlocked = stage.state === "blocked";
          const isCompleted = stage.state === "completed";
          const isSkipped = stage.state === "skipped";
          const pending = !isActive && !isBlocked && !isCompleted && !isSkipped;

          return (
            <div
              key={stage.id}
              className={cn(
                "relative flex shrink-0 items-center justify-center rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                isCompleted && "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 dark:bg-emerald-500/20",
                isActive && "border-steel-500/40 bg-steel-500/10 text-steel-700 dark:text-steel-300 dark:bg-steel-500/20 shadow-[0_0_15px_-3px_rgba(74,144,217,0.2)]",
                isBlocked && "border-gold-500/40 bg-gold-500/10 text-gold-700 dark:text-gold-300 dark:bg-gold-500/20",
                isSkipped && "border-rose-500/40 bg-rose-500/10 text-rose-700 dark:text-rose-400 dark:bg-rose-500/20",
                pending && "border-border bg-transparent text-muted-foreground",
                compact ? "h-7 px-2.5 text-[0.68rem]" : "h-8"
              )}
            >
              {isCompleted ? (
                <Check className="mr-1.5 h-3.5 w-3.5" />
              ) : isSkipped ? (
                <CircleSlash className="mr-1.5 h-3.5 w-3.5" />
              ) : isBlocked ? (
                <X className="mr-1.5 h-3.5 w-3.5" />
              ) : isActive ? (
                <span className="mr-2 flex h-2 w-2 relative">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-steel-400 opacity-75"></span>
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-steel-500"></span>
                </span>
              ) : (
                <Clock className="mr-1.5 h-3 w-3 opacity-50" />
              )}
              
              <span className="whitespace-nowrap">{stage.label}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
