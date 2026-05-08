import api from './taskApi';
import {
  InterpretabilityAnalysisResponse,
  InterpretabilityAnalysisCreateRequest,
  ApiResponse,
} from '../modules/interpretabilityAnalysis/types';

export const createInterpretabilityAnalysis = async (
  taskId: string,
  request?: Partial<InterpretabilityAnalysisCreateRequest>,
): Promise<ApiResponse<InterpretabilityAnalysisResponse>> => {
  const response = await api.post<ApiResponse<InterpretabilityAnalysisResponse>>(
    `/api/interpretability-analyses/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getInterpretabilityAnalysis = async (
  iaId: string,
): Promise<ApiResponse<InterpretabilityAnalysisResponse>> => {
  const response = await api.get<ApiResponse<InterpretabilityAnalysisResponse>>(
    `/api/interpretability-analyses/${iaId}`,
  );
  return response.data;
};

export const getLatestInterpretabilityAnalysis = async (
  taskId: string,
): Promise<ApiResponse<InterpretabilityAnalysisResponse>> => {
  const response = await api.get<ApiResponse<InterpretabilityAnalysisResponse>>(
    `/api/tasks/${taskId}/interpretability-analysis`,
  );
  return response.data;
};

export const rerunInterpretabilityAnalysis = async (
  taskId: string,
): Promise<ApiResponse<InterpretabilityAnalysisResponse>> => {
  const response = await api.post<ApiResponse<InterpretabilityAnalysisResponse>>(
    `/api/interpretability-analyses/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getFeatureImportance = async (
  iaId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/interpretability-analyses/${iaId}/feature-importance`,
  );
  return response.data;
};

export const getShapSummary = async (
  iaId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/interpretability-analyses/${iaId}/shap-summary`,
  );
  return response.data;
};

export const getLocalExplanations = async (
  iaId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/interpretability-analyses/${iaId}/local-explanations`,
  );
  return response.data;
};

export const getFinalOutputInput = async (
  iaId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/interpretability-analyses/${iaId}/final-output-input`,
  );
  return response.data;
};
