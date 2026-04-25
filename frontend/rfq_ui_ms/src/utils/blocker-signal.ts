import type { RfqCardModel } from "@/models/manager/rfq";

type BlockedStageLike = {
  blockerReasonCode?: string;
  label?: string;
  state?: string;
};

export interface RfqBlockedSignal {
  isBlocked: boolean;
  reasonLabel?: string;
  stageLabel?: string;
}

export function getBlockedStageHeadline(
  rfq: Pick<RfqCardModel, "stageHistory" | "stageLabel" | "blockerStatus" | "blockerReasonCode">,
) {
  const blockedSignal = getRfqBlockedSignal(rfq);
  if (!blockedSignal.isBlocked) {
    return null;
  }

  return `Blocked in ${blockedSignal.stageLabel ?? rfq.stageLabel}`;
}

function toTitleCase(value: string) {
  return value
    .split(" ")
    .filter(Boolean)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

export function formatBlockerReasonLabel(blockerReasonCode?: string) {
  const normalized = blockerReasonCode?.trim();
  if (!normalized) {
    return undefined;
  }

  return toTitleCase(normalized.replaceAll("_", " "));
}

function getBlockedStage(
  rfq: Pick<RfqCardModel, "stageHistory" | "stageLabel" | "blockerStatus" | "blockerReasonCode">,
): BlockedStageLike | null {
  const blockedStage = rfq.stageHistory.find((stage) => stage.state === "blocked");
  if (blockedStage) {
    return blockedStage;
  }

  if (rfq.blockerStatus === "Blocked") {
    return {
      blockerReasonCode: rfq.blockerReasonCode,
      label: rfq.stageLabel,
      state: "blocked",
    };
  }

  return null;
}

export function getRfqBlockedSignal(
  rfq: Pick<RfqCardModel, "stageHistory" | "stageLabel" | "blockerStatus" | "blockerReasonCode">,
): RfqBlockedSignal {
  const blockedStage = getBlockedStage(rfq);

  if (!blockedStage) {
    return { isBlocked: false };
  }

  return {
    isBlocked: true,
    reasonLabel: formatBlockerReasonLabel(blockedStage.blockerReasonCode),
    stageLabel: blockedStage.label ?? rfq.stageLabel,
  };
}
