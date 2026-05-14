import api from './taskApi';
import {
  WorkflowPlanResponse,
  WorkflowPlanCreateRequest,
  ApiResponse,
  FeatureStrategyResponse,
  FeatureStrategyRationaleResponse,
  PreprocessingIntentResponse,
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

// Sub-resource: Feature Strategy
export const getFeatureStrategy = async (
  planId: string,
): Promise<ApiResponse<FeatureStrategyResponse>> => {
  const response = await api.get<ApiResponse<FeatureStrategyResponse>>(
    `/api/workflow-plans/${planId}/feature-strategy`,
  );
  return response.data;
};

// Sub-resource: Feature Strategy Rationale
export const getFeatureStrategyRationale = async (
  planId: string,
): Promise<ApiResponse<FeatureStrategyRationaleResponse>> => {
  const response = await api.get<ApiResponse<FeatureStrategyRationaleResponse>>(
    `/api/workflow-plans/${planId}/feature-strategy-rationale`,
  );
  return response.data;
};

// Sub-resource: Preprocessing Intent
export const getPreprocessingIntent = async (
  planId: string,
): Promise<ApiResponse<PreprocessingIntentResponse>> => {
  const response = await api.get<ApiResponse<PreprocessingIntentResponse>>(
    `/api/workflow-plans/${planId}/preprocessing-intent`,
  );
  return response.data;
};
