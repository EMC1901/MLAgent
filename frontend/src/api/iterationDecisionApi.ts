import api from './taskApi';
import {
  IterationDecisionResponse,
  IterationDecisionCreateRequest,
  IterationDecisionSummary,
  AdoptRevisedPlanResult,
  ApiResponse,
} from '../modules/iterationDecision/types';

export const createIterationDecision = async (
  taskId: string,
  request?: Partial<IterationDecisionCreateRequest>,
): Promise<ApiResponse<IterationDecisionResponse>> => {
  const response = await api.post<ApiResponse<IterationDecisionResponse>>(
    `/api/iteration-decisions/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getIterationDecision = async (
  id: string,
): Promise<ApiResponse<IterationDecisionResponse>> => {
  const response = await api.get<ApiResponse<IterationDecisionResponse>>(
    `/api/iteration-decisions/${id}`,
  );
  return response.data;
};

export const getLatestIterationDecisionByTaskId = async (
  taskId: string,
): Promise<ApiResponse<IterationDecisionResponse>> => {
  const response = await api.get<ApiResponse<IterationDecisionResponse>>(
    `/api/tasks/${taskId}/iteration-decision`,
  );
  return response.data;
};

export const rerunIterationDecision = async (
  taskId: string,
): Promise<ApiResponse<IterationDecisionResponse>> => {
  const response = await api.post<ApiResponse<IterationDecisionResponse>>(
    `/api/iteration-decisions/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getIterationDecisionSummary = async (
  id: string,
): Promise<ApiResponse<IterationDecisionSummary>> => {
  const response = await api.get<ApiResponse<IterationDecisionSummary>>(
    `/api/iteration-decisions/${id}/summary`,
  );
  return response.data;
};

export const checkNeedsFreshDecision = async (
  taskId: string,
): Promise<ApiResponse<{ needs_fresh: boolean; reason: string }>> => {
  const response = await api.get<
    ApiResponse<{ needs_fresh: boolean; reason: string }>
  >(`/api/tasks/${taskId}/iteration-decision/needs-fresh`);
  return response.data;
};

export const getRevisedWorkflowPlan = async (
  id: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/iteration-decisions/${id}/revised-workflow-plan`,
  );
  return response.data;
};

export const adoptRevisedPlan = async (
  id: string,
): Promise<ApiResponse<AdoptRevisedPlanResult>> => {
  const response = await api.post<ApiResponse<AdoptRevisedPlanResult>>(
    `/api/iteration-decisions/${id}/adopt`,
    {},
  );
  return response.data;
};
