import type { WorkflowModel } from "@/models/manager/workflow";

export function isCustomizableWorkflow(
  workflow?: WorkflowModel | null,
): boolean {
  return (workflow?.selectionMode ?? "fixed") === "customizable";
}

export function getInitialSelectedWorkflowStageIds(
  workflow?: WorkflowModel | null,
): string[] {
  if (!workflow) {
    return [];
  }

  if (!isCustomizableWorkflow(workflow)) {
    return workflow.stages.map((stage) => stage.id);
  }

  return workflow.stages
    .filter((stage) => stage.isRequired)
    .map((stage) => stage.id);
}

export function buildSelectedWorkflow(
  workflow: WorkflowModel | undefined,
  selectedStageIds: string[],
): WorkflowModel | undefined {
  if (!workflow) {
    return undefined;
  }

  const selectedSet = new Set(selectedStageIds);

  return {
    ...workflow,
    stageCount: workflow.stages.filter((stage) => selectedSet.has(stage.id)).length,
    stages: workflow.stages.filter((stage) => selectedSet.has(stage.id)),
  };
}

export function buildSkipStageIds(
  workflow: WorkflowModel | undefined,
  selectedStageIds: string[],
): string[] {
  if (!workflow || !isCustomizableWorkflow(workflow)) {
    return [];
  }

  const selectedSet = new Set(selectedStageIds);
  return workflow.stages
    .filter((stage) => !stage.isRequired && !selectedSet.has(stage.id))
    .map((stage) => stage.id);
}
