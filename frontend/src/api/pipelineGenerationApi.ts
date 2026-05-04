import api from './taskApi';
import {
  PipelineGenerationResponse,
  PipelineGenerationCreateRequest,
  PipelineGenerationSummary,
  ApiResponse,
  ExecutionInput,
} from '../modules/pipelineGeneration/types';

export const createPipelineGeneration = async (
  taskId: string,
  request?: Partial<PipelineGenerationCreateRequest>,
): Promise<ApiResponse<PipelineGenerationResponse>> => {
  const response = await api.post<ApiResponse<PipelineGenerationResponse>>(
    `/api/pipeline-generations/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getPipelineGeneration = async (
  pgId: string,
): Promise<ApiResponse<PipelineGenerationResponse>> => {
  const response = await api.get<ApiResponse<PipelineGenerationResponse>>(
    `/api/pipeline-generations/${pgId}`,
  );
  return response.data;
};

export const getLatestPipelineGenerationByTaskId = async (
  taskId: string,
): Promise<ApiResponse<PipelineGenerationResponse>> => {
  const response = await api.get<ApiResponse<PipelineGenerationResponse>>(
    `/api/tasks/${taskId}/pipeline-generation`,
  );
  return response.data;
};

export const rerunPipelineGeneration = async (
  taskId: string,
): Promise<ApiResponse<PipelineGenerationResponse>> => {
  const response = await api.post<ApiResponse<PipelineGenerationResponse>>(
    `/api/pipeline-generations/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getPipelineGenerationSummary = async (
  pgId: string,
): Promise<ApiResponse<PipelineGenerationSummary>> => {
  const response = await api.get<ApiResponse<PipelineGenerationSummary>>(
    `/api/pipeline-generations/${pgId}/summary`,
  );
  return response.data;
};

export const getPipelineGenerationExecutionInput = async (
  pgId: string,
): Promise<ApiResponse<ExecutionInput>> => {
  const response = await api.get<ApiResponse<ExecutionInput>>(
    `/api/pipeline-generations/${pgId}/execution-input`,
  );
  return response.data;
};
