import type {
  ArtifactKind,
  ArtifactStatus,
} from "@/models/intelligence/artifacts";
import type { IntelligenceAvailabilityState } from "@/models/intelligence/snapshot";
import type {
  LiveManagerRfqStatus,
  ManagerRfqStatus,
} from "@/models/manager/rfq";

export const terminalRfqStatuses = ["awarded", "lost", "cancelled"] as const;
const terminalRfqStatusSet = new Set<ManagerRfqStatus>(terminalRfqStatuses);
const liveActiveRfqStatusSet = new Set<ManagerRfqStatus>(["in_preparation"]);

export const liveRfqStatusMeta: Record<
  LiveManagerRfqStatus,
  {
    label: string;
    tone: "steel" | "gold" | "emerald" | "rose" | "pending";
  }
> = {
  in_preparation: {
    label: "In Preparation",
    tone: "pending",
  },
  awarded: {
    label: "Awarded",
    tone: "emerald",
  },
  lost: {
    label: "Lost",
    tone: "rose",
  },
  cancelled: {
    label: "Cancelled",
    tone: "rose",
  },
};

export const intelligenceStatusMeta: Record<
  ArtifactStatus,
  {
    label: string;
    tone: "steel" | "gold" | "emerald" | "rose" | "pending";
  }
> = {
  pending: {
    label: "Pending",
    tone: "pending",
  },
  partial: {
    label: "Partial",
    tone: "gold",
  },
  complete: {
    label: "Complete",
    tone: "emerald",
  },
  failed: {
    label: "Failed",
    tone: "rose",
  },
  not_uploaded: {
    label: "No Workbook Yet",
    tone: "pending",
  },
};

export const intelligenceAvailabilityMeta: Record<
  IntelligenceAvailabilityState,
  {
    label: string;
    tone: "steel" | "gold" | "emerald" | "rose" | "pending";
  }
> = {
  not_available_yet: {
    label: "Not Available Yet",
    tone: "pending",
  },
  pending: {
    label: "Pending",
    tone: "pending",
  },
  partial: {
    label: "Partial",
    tone: "gold",
  },
  preliminary: {
    label: "Preliminary",
    tone: "gold",
  },
  failed: {
    label: "Failed",
    tone: "rose",
  },
  available: {
    label: "Available",
    tone: "emerald",
  },
};

export const artifactKindLabel: Record<ArtifactKind, string> = {
  analytical_record: "Analytical Record",
  briefing: "Briefing",
  cost_breakdown: "Cost Breakdown",
  intake_profile: "Intake Profile",
  other: "Artifact",
  parser_report: "Parser Report",
  workbook_profile: "Workbook Profile",
  workbook_review: "Workbook Review",
  snapshot: "Snapshot",
};

export function getAccentForArtifact(kind: ArtifactKind) {
  switch (kind) {
    case "analytical_record":
      return "emerald";
    case "briefing":
      return "gold";
    case "cost_breakdown":
      return "steel";
    case "intake_profile":
      return "gold";
    case "parser_report":
      return "rose";
    case "workbook_profile":
      return "steel";
    case "workbook_review":
      return "emerald";
    case "snapshot":
      return "rose";
    case "other":
    default:
      return "steel";
  }
}

export function isTerminalRfqStatus(status: ManagerRfqStatus) {
  return terminalRfqStatusSet.has(status);
}

export function isLiveActiveRfqStatus(status: ManagerRfqStatus) {
  return liveActiveRfqStatusSet.has(status);
}
