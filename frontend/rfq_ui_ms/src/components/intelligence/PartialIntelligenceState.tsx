import {
  AlertTriangle,
  Clock3,
  LoaderCircle,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import type { IntelligenceAvailabilityState } from "@/models/intelligence/snapshot";
import { intelligenceAvailabilityMeta } from "@/utils/status";

const stateMeta: Record<
  IntelligenceAvailabilityState,
  {
    description: string;
    icon: typeof Sparkles;
    title: string;
  }
> = {
  not_available_yet: {
    icon: Clock3,
    title: "Not Available Yet",
    description: "The needed RFQ inputs are not available yet for this intelligence step.",
  },
  pending: {
    icon: LoaderCircle,
    title: "Refreshing Intelligence",
    description: "The latest intelligence summary is being refreshed for this RFQ.",
  },
  partial: {
    icon: Sparkles,
    title: "Ready For Review",
    description: "A useful intelligence summary is available, but it still needs human review.",
  },
  preliminary: {
    icon: Sparkles,
    title: "Initial Guidance Ready",
    description: "An early intelligence summary is available to support review of this RFQ.",
  },
  failed: {
    icon: AlertTriangle,
    title: "Needs Attention",
    description: "One or more intelligence steps could not be completed and need follow-up.",
  },
  available: {
    icon: Sparkles,
    title: "Ready",
    description: "The current intelligence summary is available for this RFQ.",
  },
};

export function PartialIntelligenceState({
  actions,
  state,
  summary,
}: {
  actions: string[];
  state: IntelligenceAvailabilityState;
  summary: string;
}) {
  const meta = stateMeta[state];
  const badgeMeta = intelligenceAvailabilityMeta[state];
  const Icon = meta.icon;

  return (
    <div>
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-border bg-muted/40 dark:bg-white/[0.03]">
          <Icon
            className={`h-5 w-5 ${
              state === "pending" ? "animate-spin text-muted-foreground" : ""
            } ${state === "available" ? "text-emerald-500" : ""} ${
              state === "failed" ? "text-rose-500" : ""
            } ${
              state === "partial" || state === "preliminary"
                ? "text-amber-500 dark:text-gold-300"
                : ""
            } ${state === "not_available_yet" ? "text-muted-foreground" : ""}`}
          />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold text-foreground">
              {meta.title}
            </h3>
            <Badge variant={badgeMeta.tone}>{badgeMeta.label}</Badge>
          </div>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {meta.description}
          </p>
        </div>
      </div>

      <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
        {summary}
      </p>

      {actions.length > 0 ? (
        <div className="mt-4 grid gap-2 sm:grid-cols-2">
          {actions.map((action) => (
            <div key={action} className="stat-cell text-sm text-muted-foreground">
              {action}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
