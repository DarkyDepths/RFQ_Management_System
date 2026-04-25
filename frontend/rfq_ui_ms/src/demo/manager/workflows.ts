import type { ManagerWorkflowResponse } from "@/models/manager/workflow";

import {
  ghiLongWorkflowStages,
  ghiShortWorkflowStages,
} from "@/demo/manager/stages";

function buildWorkflowResponse(
  workflow: Omit<ManagerWorkflowResponse, "turnaroundDays">,
): ManagerWorkflowResponse {
  return {
    ...workflow,
    turnaroundDays: workflow.stages.reduce(
      (total, stage) => total + (stage.plannedDurationDays ?? 0),
      0,
    ),
  };
}

export const managerWorkflowResponses: ManagerWorkflowResponse[] = [
  buildWorkflowResponse({
    id: "workflow-ghi-long",
    code: "GHI-LONG",
    name: "GHI long workflow",
    description:
      "Full lifecycle for complex, engineered RFQs with design, BOQ/BOM and vendor inquiries.",
    recommendedUse:
      "Use when the RFQ needs the full GHI lifecycle across technical preparation, pricing, submission, and closeout.",
    selectionMode: "fixed",
    baseWorkflowId: null,
    stages: ghiLongWorkflowStages,
  }),
  buildWorkflowResponse({
    id: "workflow-ghi-short",
    code: "GHI-SHORT",
    name: "GHI short workflow",
    description:
      "Simplified path for repeat orders, standard items or small-value RFQs.",
    recommendedUse:
      "Use for smaller or faster GHI pursuits that still require a formal Go / No-Go decision.",
    selectionMode: "fixed",
    baseWorkflowId: null,
    stages: ghiShortWorkflowStages,
  }),
  buildWorkflowResponse({
    id: "workflow-ghi-custom",
    code: "GHI-CUSTOM",
    name: "GHI customized workflow",
    description:
      "Customizable lifecycle that reuses the full GHI long workflow catalog at RFQ creation time.",
    recommendedUse:
      "Use when the RFQ needs a tailored subset of the full GHI long workflow.",
    selectionMode: "customizable",
    baseWorkflowId: "workflow-ghi-long",
    stages: ghiLongWorkflowStages,
  }),
];
