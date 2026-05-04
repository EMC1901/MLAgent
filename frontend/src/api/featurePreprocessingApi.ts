import api from './taskApi';
import {
  FeaturePreprocessingResponse,
  FeaturePreprocessingCreateRequest,
  PreviewResponse,
  ApiResponse,
} from '../modules/featurePreprocessing/types';

// Feature preprocessing can take time for imputation/scaling on large matrices
const FEATURE_PREPROCESSING_TIMEOUT = 600000; // 10 minutes

export const createFeaturePreprocessing = async (
  taskId: string,
  request?: FeaturePreprocessingCreateRequest,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.post<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${taskId}`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

export const getFeaturePreprocessing = async (
  preprocessingId: string,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.get<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${preprocessingId}`,
  );
  return response.data;
};

export const getLatestFeaturePreprocessingByTaskId = async (
  taskId: string,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.get<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/tasks/${taskId}/feature-preprocessing`,
  );
  return response.data;
};

export const rerunFeaturePreprocessing = async (
  taskId: string,
  request?: FeaturePreprocessingCreateRequest,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.post<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${taskId}/rerun`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

export const getModelReadyPreview = async (
  preprocessingId: string,
): Promise<ApiResponse<PreviewResponse>> => {
  const response = await api.get<ApiResponse<PreviewResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/preview`,
  );
  return response.data;
};
