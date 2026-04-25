import { apiConfig } from "@/config/api";
import { requestManagerJson } from "@/connectors/manager/base";
import { managerWorkflowResponses } from "@/demo/manager/workflows";
import type {
  ManagerApiWorkflowDetail,
  ManagerApiWorkflowListResponse,
} from "@/models/manager/api-workflow";
import type {
  ManagerWorkflowResponse,
  WorkflowModel,
} from "@/models/manager/workflow";
import {
  translateManagerWorkflowDetail,
  translateWorkflow,
} from "@/translators/manager/workflows";
import { sleep } from "@/utils/async";

export async function listWorkflows(): Promise<WorkflowModel[]> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.7));
    return managerWorkflowResponses.map(translateWorkflow);
  }

  const response = await requestManagerJson<ManagerApiWorkflowListResponse>(
    "/workflows",
  );

  const workflowDetails = await Promise.all(
    response.data.map((workflow) =>
      requestManagerJson<ManagerApiWorkflowDetail>(
        `/workflows/${workflow.id}`,
      ),
    ),
  );

  return workflowDetails.map(translateManagerWorkflowDetail);
}

export async function getWorkflow(
  workflowId: string,
): Promise<WorkflowModel | null> {
  if (apiConfig.useMockData) {
    await sleep(Math.round(apiConfig.demoLatencyMs * 0.55));
    const workflow = managerWorkflowResponses.find(
      (candidate) => candidate.id === workflowId,
    );
    return workflow ? translateWorkflow(workflow) : null;
  }

  const response = await requestManagerJson<ManagerApiWorkflowDetail>(
    `/workflows/${workflowId}`,
  );

  return translateManagerWorkflowDetail(response);
}
