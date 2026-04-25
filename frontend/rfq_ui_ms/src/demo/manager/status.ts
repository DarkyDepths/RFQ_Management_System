import type {
  DemoOnlyManagerRfqStatus,
  ManagerRfqStatus,
} from "@/models/manager/rfq";
import { liveRfqStatusMeta, isLiveActiveRfqStatus } from "@/utils/status";

type RfqStatusMeta = {
  label: string;
  tone: "steel" | "gold" | "emerald" | "rose" | "pending";
};

const demoOnlyActiveRfqStatusSet = new Set<ManagerRfqStatus>([
  "under_review",
  "submitted",
  "attention_required",
]);

export const demoOnlyRfqStatusMeta: Record<
  DemoOnlyManagerRfqStatus,
  RfqStatusMeta
> = {
  draft: {
    label: "Draft",
    tone: "pending",
  },
  under_review: {
    label: "Under Review",
    tone: "steel",
  },
  submitted: {
    label: "Submitted",
    tone: "steel",
  },
  attention_required: {
    label: "Partial / Warning",
    tone: "gold",
  },
};

export const demoRfqStatusMeta: Record<ManagerRfqStatus, RfqStatusMeta> = {
  ...liveRfqStatusMeta,
  ...demoOnlyRfqStatusMeta,
};

export const demoStatusOptions: Array<{
  label: string;
  value: "all" | ManagerRfqStatus;
}> = [
  { label: "All", value: "all" },
  { label: "Draft", value: "draft" },
  { label: "In Preparation", value: "in_preparation" },
  { label: "Under Review", value: "under_review" },
  { label: "Submitted", value: "submitted" },
  { label: "Awarded", value: "awarded" },
  { label: "Lost", value: "lost" },
  { label: "Cancelled", value: "cancelled" },
  { label: "Partial / Warning", value: "attention_required" },
];

export function isDemoActiveRfqStatus(status: ManagerRfqStatus) {
  return isLiveActiveRfqStatus(status) || demoOnlyActiveRfqStatusSet.has(status);
}

export function parseDemoStatusFilter(value: string | null) {
  switch (value) {
    case "draft":
    case "in_preparation":
    case "under_review":
    case "submitted":
    case "awarded":
    case "lost":
    case "cancelled":
    case "attention_required":
      return value;
    default:
      return "all";
  }
}
