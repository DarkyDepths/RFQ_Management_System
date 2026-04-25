import type { ManagerRfqStatus } from "@/models/manager/rfq";
import { isTerminalRfqStatus } from "@/utils/status";

export type LifecycleProgressTone = "early" | "mid" | "late" | "complete" | "failed";

function clampProgress(progress: number) {
  return Math.max(0, Math.min(100, Math.floor(progress)));
}

export function getLifecycleProgressTone(
  progress: number,
  status: ManagerRfqStatus,
): LifecycleProgressTone {
  if (status === "lost" || status === "cancelled") {
    return "failed";
  }

  const normalizedProgress = clampProgress(progress);

  if (isTerminalRfqStatus(status) && normalizedProgress >= 100) {
    return "complete";
  }

  if (normalizedProgress <= 20) {
    return "early";
  }

  if (normalizedProgress <= 60) {
    return "mid";
  }

  return "late";
}

export function getLifecycleProgressFillPercent(
  progress: number,
  status: ManagerRfqStatus,
) {
  const normalizedProgress = clampProgress(progress);

  if (isTerminalRfqStatus(status) && normalizedProgress >= 100) {
    return 100;
  }

  return normalizedProgress;
}

export function getLifecycleProgressFillClasses(
  progress: number,
  status: ManagerRfqStatus,
) {
  switch (getLifecycleProgressTone(progress, status)) {
    case "failed":
      return "bg-gradient-to-r from-rose-500/30 to-rose-400/30 dark:from-rose-500/25 dark:to-rose-400/25 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]";
    case "complete":
      return "bg-gradient-to-r from-emerald-500/30 to-emerald-400/30 dark:from-emerald-500/25 dark:to-emerald-400/25 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]";
    case "late":
      return "bg-gradient-to-r from-emerald-500/20 to-emerald-400/20 dark:from-emerald-500/15 dark:to-emerald-400/15 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]";
    case "mid":
      return "bg-gradient-to-r from-emerald-500/10 to-emerald-400/10 dark:from-emerald-500/10 dark:to-emerald-400/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]";
    case "early":
    default:
      return "bg-gradient-to-r from-emerald-500/5 to-emerald-400/5 dark:from-emerald-500/5 dark:to-emerald-400/5 shadow-[inset_0_1px_0_rgba(255,255,255,0.4)] dark:shadow-[inset_0_1px_0_rgba(255,255,255,0.03)]";
  }
}

export function getLifecycleProgressBaseClasses() {
  return "bg-[#ffffff] dark:bg-[#161b24]";
}

export function getLifecycleProgressBoundaryClasses() {
  return "bg-emerald-400/40 shadow-[0_0_0_1px_rgba(16,185,129,0.15)] dark:bg-emerald-400/30 dark:shadow-[0_0_0_1px_rgba(16,185,129,0.08)]";
}
