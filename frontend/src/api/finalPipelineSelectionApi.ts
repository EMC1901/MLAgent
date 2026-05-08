import api from './taskApi';
import {
  FinalPipelineSelectionResponse,
  FinalPipelineSelectionCreateRequest,
  ApiResponse,
} from '../modules/finalPipelineSelection/types';

export const createFinalPipelineSelection = async (
  taskId: string,
  request?: Partial<FinalPipelineSelectionCreateRequest>,
): Promise<ApiResponse<FinalPipelineSelectionResponse>> => {
  const response = await api.post<ApiResponse<FinalPipelineSelectionResponse>>(
    `/api/final-pipeline-selections/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getFinalPipelineSelection = async (
  fpsId: string,
): Promise<ApiResponse<FinalPipelineSelectionResponse>> => {
  const response = await api.get<ApiResponse<FinalPipelineSelectionResponse>>(
    `/api/final-pipeline-selections/${fpsId}`,
  );
  return response.data;
};

export const getLatestFinalPipelineSelection = async (
  taskId: string,
): Promise<ApiResponse<FinalPipelineSelectionResponse>> => {
  const response = await api.get<ApiResponse<FinalPipelineSelectionResponse>>(
    `/api/tasks/${taskId}/final-pipeline-selection`,
  );
  return response.data;
};

export const rerunFinalPipelineSelection = async (
  taskId: string,
): Promise<ApiResponse<FinalPipelineSelectionResponse>> => {
  const response = await api.post<ApiResponse<FinalPipelineSelectionResponse>>(
    `/api/final-pipeline-selections/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getCandidateRanking = async (
  fpsId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-pipeline-selections/${fpsId}/ranking`,
  );
  return response.data;
};

export const getLLMExplanation = async (
  fpsId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-pipeline-selections/${fpsId}/llm-explanation`,
  );
  return response.data;
};

export const getArtifactManifest = async (
  fpsId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-pipeline-selections/${fpsId}/artifact-manifest`,
  );
  return response.data;
};

export const getInterpretabilityAnalysisInput = async (
  fpsId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-pipeline-selections/${fpsId}/interpretability-analysis-input`,
  );
  return response.data;
};
