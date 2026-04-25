import type {
  ManagerStageTemplateResponse,
  StageTemplateModel,
} from "@/models/manager/stage";

export interface ManagerWorkflowResponse {
  id: string;
  name: string;
  code?: string;
  description: string;
  recommendedUse: string;
  turnaroundDays: number;
  selectionMode?: "fixed" | "customizable";
  baseWorkflowId?: string | null;
  stages: ManagerStageTemplateResponse[];
}

export interface WorkflowModel {
  id: string;
  name: string;
  code?: string;
  description?: string;
  recommendedUse?: string;
  turnaroundDays?: number;
  stageCount: number;
  isActive?: boolean;
  isDefault?: boolean;
  selectionMode?: "fixed" | "customizable";
  baseWorkflowId?: string | null;
  stages: StageTemplateModel[];
}
