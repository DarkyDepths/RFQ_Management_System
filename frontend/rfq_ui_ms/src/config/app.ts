import type { AppRole } from "@/models/ui/role";

export const appConfig = {
  shortName: "GHI Estimation",
  name: "RFQ Lifecycle Intelligence Platform",
  owner: "GHI Estimation Department",
  description:
    "Premium industrial platform shell for RFQ lifecycle operations and intelligence artifacts.",
  platformLine: "RFQ Lifecycle Intelligence Platform — GHI Estimation Department",
  demoBanner: "Demo Mode — Mock Data Active",
  defaultRole: "manager" as AppRole,
  featuredRfqId: "RFQ-2026-0142",
  timings: {
    dashboardLoadMs: 720,
    detailLoadMs: 760,
    stagedIntelMs: 980,
    uploadTransitionMs: 1400,
  },
} as const;
