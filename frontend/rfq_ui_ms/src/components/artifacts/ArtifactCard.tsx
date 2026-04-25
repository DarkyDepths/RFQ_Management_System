"use client";

import { FileStack, Sparkles } from "lucide-react";
import { motion } from "framer-motion";

import { Badge } from "@/components/ui/badge";
import type { ArtifactModel } from "@/models/intelligence/artifacts";
import { artifactKindLabel, intelligenceStatusMeta } from "@/utils/status";
import { cn } from "@/lib/utils";

const accentMap: Record<ArtifactModel["accent"], string> = {
  steel: "from-steel-500/15 to-transparent",
  gold: "from-gold-500/15 to-transparent",
  emerald: "from-emerald-500/15 to-transparent",
  rose: "from-rose-500/15 to-transparent",
};

export function ArtifactCard({
  artifact,
}: {
  artifact: ArtifactModel;
}) {
  const statusMeta = intelligenceStatusMeta[artifact.status];

  return (
    <motion.div
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="surface-panel surface-panel-hover p-6"
      initial={{ opacity: 0, y: 18, scale: 0.98 }}
      transition={{ duration: 0.38 }}
    >
      <div
        className={cn(
          "absolute inset-x-0 top-0 h-24 bg-gradient-to-b opacity-40 dark:opacity-100",
          accentMap[artifact.accent],
        )}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-[14px] border border-border bg-card shadow-sm dark:bg-white/[0.03]">
            {artifact.kind === "snapshot" ? (
              <Sparkles className="h-5 w-5 text-gold-500 dark:text-gold-300" />
            ) : (
              <FileStack className="h-5 w-5 text-primary dark:text-steel-300" />
            )}
          </div>
          <div>
            <div className="text-[0.68rem] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              {artifactKindLabel[artifact.kind]}
            </div>
            <h3 className="mt-1 text-lg font-semibold text-foreground">
              {artifact.title}
            </h3>
          </div>
        </div>
        <Badge variant={statusMeta.tone}>{statusMeta.label}</Badge>
      </div>

      <p className="relative mt-4 text-sm leading-relaxed text-muted-foreground">
        {artifact.summary}
      </p>

      <div className="relative mt-5 flex flex-wrap items-center gap-2 border-t border-border pt-4">
        <Badge className="bg-muted/50 font-mono text-[0.7rem]" variant="default">
          {artifact.version}
        </Badge>
        {artifact.isCurrent === true ? <Badge variant="emerald">Current</Badge> : null}
        {artifact.isCurrent === false ? <Badge variant="steel">Historical</Badge> : null}
        <span className="text-[0.75rem] text-muted-foreground">
          Updated {artifact.updatedLabel}
        </span>
        {artifact.schemaVersion ? (
          <span className="text-[0.75rem] text-muted-foreground">
            Schema {artifact.schemaVersion}
          </span>
        ) : null}
      </div>
    </motion.div>
  );
}
