import api from './taskApi';
import {
  PipelineExecutionResponse,
  PipelineExecutionCreateRequest,
  PipelineExecutionSummary,
  ApiResponse,
  TrialResultDTO,
  MetricEvaluationInputDTO,
  LogsResponse,
} from '../modules/pipelineExecution/types';

export const createPipelineExecution = async (
  taskId: string,
  request?: Partial<PipelineExecutionCreateRequest>,
): Promise<ApiResponse<PipelineExecutionResponse>> => {
  const response = await api.post<ApiResponse<PipelineExecutionResponse>>(
    `/api/pipeline-executions/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getPipelineExecution = async (
  peId: string,
): Promise<ApiResponse<PipelineExecutionResponse>> => {
  const response = await api.get<ApiResponse<PipelineExecutionResponse>>(
    `/api/pipeline-executions/${peId}`,
  );
  return response.data;
};

export const getLatestPipelineExecutionByTaskId = async (
  taskId: string,
): Promise<ApiResponse<PipelineExecutionResponse>> => {
  const response = await api.get<ApiResponse<PipelineExecutionResponse>>(
    `/api/tasks/${taskId}/pipeline-execution`,
  );
  return response.data;
};

export const rerunPipelineExecution = async (
  taskId: string,
): Promise<ApiResponse<PipelineExecutionResponse>> => {
  const response = await api.post<ApiResponse<PipelineExecutionResponse>>(
    `/api/pipeline-executions/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getPipelineExecutionSummary = async (
  peId: string,
): Promise<ApiResponse<PipelineExecutionSummary>> => {
  const response = await api.get<ApiResponse<PipelineExecutionSummary>>(
    `/api/pipeline-executions/${peId}/summary`,
  );
  return response.data;
};

export const getPipelineExecutionTrials = async (
  peId: string,
): Promise<ApiResponse<TrialResultDTO[]>> => {
  const response = await api.get<ApiResponse<TrialResultDTO[]>>(
    `/api/pipeline-executions/${peId}/trials`,
  );
  return response.data;
};

export const getPipelineExecutionMetricInput = async (
  peId: string,
): Promise<ApiResponse<MetricEvaluationInputDTO>> => {
  const response = await api.get<ApiResponse<MetricEvaluationInputDTO>>(
    `/api/pipeline-executions/${peId}/metric-evaluation-input`,
  );
  return response.data;
};

export const getPipelineExecutionLogs = async (
  peId: string,
): Promise<ApiResponse<LogsResponse>> => {
  const response = await api.get<ApiResponse<LogsResponse>>(
    `/api/pipeline-executions/${peId}/logs`,
  );
  return response.data;
};
