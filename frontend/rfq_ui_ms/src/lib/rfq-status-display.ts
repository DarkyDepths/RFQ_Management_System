import { demoOnlyRfqStatusMeta } from "@/demo/manager/status";
import type { ManagerRfqStatus } from "@/models/manager/rfq";
import { liveRfqStatusMeta } from "@/utils/status";

export type TerminalRfqOutcome = "awarded" | "lost" | "cancelled";

const rfqStatusDisplayMeta = {
  ...liveRfqStatusMeta,
  ...demoOnlyRfqStatusMeta,
};

export function getRfqStatusMeta(status: ManagerRfqStatus) {
  return rfqStatusDisplayMeta[status];
}

export function getRfqStatusLabel(status: ManagerRfqStatus) {
  return getRfqStatusMeta(status).label;
}

export function getTerminalRfqOutcome(
  status: ManagerRfqStatus,
): TerminalRfqOutcome | null {
  if (status === "awarded" || status === "lost" || status === "cancelled") {
    return status;
  }

  return null;
}
