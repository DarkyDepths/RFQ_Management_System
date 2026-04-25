import type {
  ManagerApiWorkflowDetail,
  ManagerApiWorkflowSummary,
} from "@/models/manager/api-workflow";
import type {
  ManagerWorkflowResponse,
  WorkflowModel,
} from "@/models/manager/workflow";
import {
  translateManagerWorkflowStageTemplate,
  translateStageTemplate,
} from "@/translators/manager/stages";
import { getWorkflowPlannedDurationDays } from "@/utils/workflow-deadline";

export function translateWorkflow(
  workflow: ManagerWorkflowResponse,
): WorkflowModel {
  const stages = workflow.stages.map(translateStageTemplate);

  return {
    id: workflow.id,
    name: workflow.name,
    code: workflow.code,
    description: workflow.description,
    recommendedUse: workflow.recommendedUse,
    selectionMode: workflow.selectionMode ?? "fixed",
    baseWorkflowId: workflow.baseWorkflowId ?? null,
    turnaroundDays:
      getWorkflowPlannedDurationDays({
        ...workflow,
        stageCount: workflow.stages.length,
        stages,
      }) ?? workflow.turnaroundDays,
    stageCount: workflow.stages.length,
    stages,
  };
}

function calculateWorkflowTurnaroundDays(
  workflow: ManagerApiWorkflowDetail,
) {
  return workflow.stages.reduce(
    (total, stage) => total + stage.planned_duration_days,
    0,
  );
}

export function translateManagerWorkflowSummary(
  workflow: ManagerApiWorkflowSummary,
): WorkflowModel {
  return {
    id: workflow.id,
    name: workflow.name,
    code: workflow.code,
    stageCount: workflow.stage_count,
    isActive: workflow.is_active,
    isDefault: workflow.is_default,
    selectionMode: workflow.selection_mode ?? "fixed",
    baseWorkflowId: workflow.base_workflow_id ?? null,
    stages: [],
  };
}

export function translateManagerWorkflowDetail(
  workflow: ManagerApiWorkflowDetail,
): WorkflowModel {
  return {
    ...translateManagerWorkflowSummary(workflow),
    description: workflow.description ?? undefined,
    turnaroundDays: calculateWorkflowTurnaroundDays(workflow),
    stages: workflow.stages.map(translateManagerWorkflowStageTemplate),
  };
}
