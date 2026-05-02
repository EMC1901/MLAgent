import api from './taskApi';
import {
  WorkflowPlanResponse,
  WorkflowPlanCreateRequest,
  ApiResponse,
} from '../modules/workflowPlanning/types';

export const createWorkflowPlan = async (
  taskId: string,
  request?: WorkflowPlanCreateRequest,
): Promise<ApiResponse<WorkflowPlanResponse>> => {
  const response = await api.post<ApiResponse<WorkflowPlanResponse>>(
    `/api/workflow-plans/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getWorkflowPlan = async (
  planId: string,
): Promise<ApiResponse<WorkflowPlanResponse>> => {
  const response = await api.get<ApiResponse<WorkflowPlanResponse>>(
    `/api/workflow-plans/${planId}`,
  );
  return response.data;
};

export const getLatestWorkflowPlanByTaskId = async (
  taskId: string,
): Promise<ApiResponse<WorkflowPlanResponse>> => {
  const response = await api.get<ApiResponse<WorkflowPlanResponse>>(
    `/api/tasks/${taskId}/workflow-plan`,
  );
  return response.data;
};

export const rerunWorkflowPlan = async (
  taskId: string,
  request?: WorkflowPlanCreateRequest,
): Promise<ApiResponse<WorkflowPlanResponse>> => {
  const response = await api.post<ApiResponse<WorkflowPlanResponse>>(
    `/api/workflow-plans/${taskId}/rerun`,
    request || {},
  );
  return response.data;
};
