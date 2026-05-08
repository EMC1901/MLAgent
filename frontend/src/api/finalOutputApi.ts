import api from './taskApi';
import {
  FinalOutputResponse,
  FinalOutputCreateRequest,
  ApiResponse,
} from '../modules/finalOutput/types';

export const createFinalOutput = async (
  taskId: string,
  request?: Partial<FinalOutputCreateRequest>,
): Promise<ApiResponse<FinalOutputResponse>> => {
  const response = await api.post<ApiResponse<FinalOutputResponse>>(
    `/api/final-outputs/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getFinalOutput = async (
  foId: string,
): Promise<ApiResponse<FinalOutputResponse>> => {
  const response = await api.get<ApiResponse<FinalOutputResponse>>(
    `/api/final-outputs/${foId}`,
  );
  return response.data;
};

export const getLatestFinalOutput = async (
  taskId: string,
): Promise<ApiResponse<FinalOutputResponse>> => {
  const response = await api.get<ApiResponse<FinalOutputResponse>>(
    `/api/tasks/${taskId}/final-output`,
  );
  return response.data;
};

export const rerunFinalOutput = async (
  taskId: string,
): Promise<ApiResponse<FinalOutputResponse>> => {
  const response = await api.post<ApiResponse<FinalOutputResponse>>(
    `/api/final-outputs/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getFinalReport = async (
  foId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-outputs/${foId}/report`,
  );
  return response.data;
};

export const getWorkflowTrace = async (
  foId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-outputs/${foId}/workflow-trace`,
  );
  return response.data;
};

export const getArtifactManifest = async (
  foId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-outputs/${foId}/artifact-manifest`,
  );
  return response.data;
};

export const getDownloadLinks = async (
  foId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/final-outputs/${foId}/downloads`,
  );
  return response.data;
};
