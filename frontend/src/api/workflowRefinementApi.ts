import api from './taskApi';
import {
  WorkflowRefinementResponse,
  WorkflowRefinementCreateRequest,
  AdoptRevisedPlanResult,
  ApiResponse,
} from '../modules/workflowRefinement/types';

export const createWorkflowRefinement = async (
  taskId: string,
  request?: Partial<WorkflowRefinementCreateRequest>,
): Promise<ApiResponse<WorkflowRefinementResponse>> => {
  const response = await api.post<ApiResponse<WorkflowRefinementResponse>>(
    `/api/workflow-refinements/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getWorkflowRefinement = async (
  wrId: string,
): Promise<ApiResponse<WorkflowRefinementResponse>> => {
  const response = await api.get<ApiResponse<WorkflowRefinementResponse>>(
    `/api/workflow-refinements/${wrId}`,
  );
  return response.data;
};

export const getLatestWorkflowRefinementByTaskId = async (
  taskId: string,
): Promise<ApiResponse<WorkflowRefinementResponse>> => {
  const response = await api.get<ApiResponse<WorkflowRefinementResponse>>(
    `/api/tasks/${taskId}/workflow-refinement`,
  );
  return response.data;
};

export const rerunWorkflowRefinement = async (
  taskId: string,
): Promise<ApiResponse<WorkflowRefinementResponse>> => {
  const response = await api.post<ApiResponse<WorkflowRefinementResponse>>(
    `/api/workflow-refinements/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getRevisedWorkflowPlan = async (
  wrId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/workflow-refinements/${wrId}/revised-workflow-plan`,
  );
  return response.data;
};

export const getIterationRerunPlan = async (
  wrId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/workflow-refinements/${wrId}/iteration-rerun-plan`,
  );
  return response.data;
};

export const adoptRevisedPlan = async (
  wrId: string,
): Promise<ApiResponse<AdoptRevisedPlanResult>> => {
  const response = await api.post<ApiResponse<AdoptRevisedPlanResult>>(
    `/api/workflow-refinements/${wrId}/adopt`,
    {},
  );
  return response.data;
};
