"use client";

import { CircularGauge } from "@/components/common/CircularGauge";

export function IntelligenceReadinessBar({
  readiness,
  confidence,
}: {
  readiness: number;
  confidence: number;
}) {
  return (
    <div className="surface-panel p-6">
      <h3 className="text-sm font-semibold text-foreground">
        Readiness & Confidence
      </h3>
      <div className="mt-5 flex items-center justify-center gap-8">
        <CircularGauge label="Readiness" size={100} value={readiness} />
        <CircularGauge
          color="hsl(213, 60%, 52%)"
          label="Confidence"
          size={100}
          value={confidence}
        />
      </div>
    </div>
  );
}
