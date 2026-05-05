import api from './taskApi';
import {
  MetricEvaluationResponse,
  MetricEvaluationCreateRequest,
  MetricEvaluationSummary,
  ApiResponse,
  ModelRankingItem,
  TrialMetricResult,
  FoldMetricResult,
  ResultDiagnosisInput,
} from '../modules/metricEvaluation/types';

export const createMetricEvaluation = async (
  taskId: string,
  request?: Partial<MetricEvaluationCreateRequest>,
): Promise<ApiResponse<MetricEvaluationResponse>> => {
  const response = await api.post<ApiResponse<MetricEvaluationResponse>>(
    `/api/metric-evaluations/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getMetricEvaluation = async (
  meId: string,
): Promise<ApiResponse<MetricEvaluationResponse>> => {
  const response = await api.get<ApiResponse<MetricEvaluationResponse>>(
    `/api/metric-evaluations/${meId}`,
  );
  return response.data;
};

export const getLatestMetricEvaluationByTaskId = async (
  taskId: string,
): Promise<ApiResponse<MetricEvaluationResponse>> => {
  const response = await api.get<ApiResponse<MetricEvaluationResponse>>(
    `/api/tasks/${taskId}/metric-evaluation`,
  );
  return response.data;
};

export const rerunMetricEvaluation = async (
  taskId: string,
): Promise<ApiResponse<MetricEvaluationResponse>> => {
  const response = await api.post<ApiResponse<MetricEvaluationResponse>>(
    `/api/metric-evaluations/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getMetricEvaluationSummary = async (
  meId: string,
): Promise<ApiResponse<MetricEvaluationSummary>> => {
  const response = await api.get<ApiResponse<MetricEvaluationSummary>>(
    `/api/metric-evaluations/${meId}/summary`,
  );
  return response.data;
};

export const getMetricEvaluationRanking = async (
  meId: string,
): Promise<ApiResponse<ModelRankingItem[]>> => {
  const response = await api.get<ApiResponse<ModelRankingItem[]>>(
    `/api/metric-evaluations/${meId}/ranking`,
  );
  return response.data;
};

export const getMetricEvaluationTrials = async (
  meId: string,
): Promise<ApiResponse<TrialMetricResult[]>> => {
  const response = await api.get<ApiResponse<TrialMetricResult[]>>(
    `/api/metric-evaluations/${meId}/trials`,
  );
  return response.data;
};

export const getMetricEvaluationFolds = async (
  meId: string,
): Promise<ApiResponse<FoldMetricResult[]>> => {
  const response = await api.get<ApiResponse<FoldMetricResult[]>>(
    `/api/metric-evaluations/${meId}/folds`,
  );
  return response.data;
};

export const getResultDiagnosisInput = async (
  meId: string,
): Promise<ApiResponse<ResultDiagnosisInput>> => {
  const response = await api.get<ApiResponse<ResultDiagnosisInput>>(
    `/api/metric-evaluations/${meId}/result-diagnosis-input`,
  );
  return response.data;
};
