import api from './taskApi';
import {
  ModelSearchContextResponse,
  ModelSearchContextCreateRequest,
  ApiResponse,
} from '../modules/modelSearchContext/types';

const MODEL_SEARCH_TIMEOUT = 300000; // 5 minutes (includes LLM call)

export const createModelSearchContext = async (
  taskId: string,
  request?: ModelSearchContextCreateRequest,
): Promise<ApiResponse<ModelSearchContextResponse>> => {
  const response = await api.post<ApiResponse<ModelSearchContextResponse>>(
    `/api/model-search-contexts/${taskId}`,
    request || {},
    { timeout: MODEL_SEARCH_TIMEOUT },
  );
  return response.data;
};

export const getModelSearchContext = async (
  contextId: string,
): Promise<ApiResponse<ModelSearchContextResponse>> => {
  const response = await api.get<ApiResponse<ModelSearchContextResponse>>(
    `/api/model-search-contexts/${contextId}`,
  );
  return response.data;
};

export const getLatestModelSearchContextByTaskId = async (
  taskId: string,
): Promise<ApiResponse<ModelSearchContextResponse>> => {
  const response = await api.get<ApiResponse<ModelSearchContextResponse>>(
    `/api/tasks/${taskId}/model-search-context`,
  );
  return response.data;
};

export const rerunModelSearchContext = async (
  taskId: string,
  request?: ModelSearchContextCreateRequest,
): Promise<ApiResponse<ModelSearchContextResponse>> => {
  const response = await api.post<ApiResponse<ModelSearchContextResponse>>(
    `/api/model-search-contexts/${taskId}/rerun`,
    request || {},
    { timeout: MODEL_SEARCH_TIMEOUT },
  );
  return response.data;
};
