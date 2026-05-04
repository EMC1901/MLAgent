import api from './taskApi';
import {
  ModelSearchPlanResponse,
  ModelSearchPlanCreateRequest,
  ModelSearchPlanSummary,
  ApiResponse,
} from '../modules/modelSearch/types';

const MODEL_SEARCH_TIMEOUT = 300000; // 5 minutes (includes LLM call)

export const createModelSearchPlan = async (
  taskId: string,
  request?: Partial<ModelSearchPlanCreateRequest>,
): Promise<ApiResponse<ModelSearchPlanResponse>> => {
  const response = await api.post<ApiResponse<ModelSearchPlanResponse>>(
    `/api/model-search-plans/${taskId}`,
    request || {},
    { timeout: MODEL_SEARCH_TIMEOUT },
  );
  return response.data;
};

export const getModelSearchPlan = async (
  planId: string,
): Promise<ApiResponse<ModelSearchPlanResponse>> => {
  const response = await api.get<ApiResponse<ModelSearchPlanResponse>>(
    `/api/model-search-plans/${planId}`,
  );
  return response.data;
};

export const getLatestModelSearchPlanByTaskId = async (
  taskId: string,
): Promise<ApiResponse<ModelSearchPlanResponse>> => {
  const response = await api.get<ApiResponse<ModelSearchPlanResponse>>(
    `/api/tasks/${taskId}/model-search-plan`,
  );
  return response.data;
};

export const rerunModelSearchPlan = async (
  taskId: string,
  request?: Partial<ModelSearchPlanCreateRequest>,
): Promise<ApiResponse<ModelSearchPlanResponse>> => {
  const response = await api.post<ApiResponse<ModelSearchPlanResponse>>(
    `/api/model-search-plans/${taskId}/rerun`,
    request || {},
    { timeout: MODEL_SEARCH_TIMEOUT },
  );
  return response.data;
};

export const getModelSearchPlanSummary = async (
  planId: string,
): Promise<ApiResponse<ModelSearchPlanSummary>> => {
  const response = await api.get<ApiResponse<ModelSearchPlanSummary>>(
    `/api/model-search-plans/${planId}/summary`,
  );
  return response.data;
};
