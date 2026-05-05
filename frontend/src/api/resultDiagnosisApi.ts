import api from './taskApi';
import {
  ResultDiagnosisResponse,
  ResultDiagnosisCreateRequest,
  ResultDiagnosisSummary,
  ApiResponse,
  ClosedLoopRefinementInput,
} from '../modules/resultDiagnosis/types';

export const createResultDiagnosis = async (
  taskId: string,
  request?: Partial<ResultDiagnosisCreateRequest>,
): Promise<ApiResponse<ResultDiagnosisResponse>> => {
  const response = await api.post<ApiResponse<ResultDiagnosisResponse>>(
    `/api/result-diagnoses/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getResultDiagnosis = async (
  rdId: string,
): Promise<ApiResponse<ResultDiagnosisResponse>> => {
  const response = await api.get<ApiResponse<ResultDiagnosisResponse>>(
    `/api/result-diagnoses/${rdId}`,
  );
  return response.data;
};

export const getLatestResultDiagnosisByTaskId = async (
  taskId: string,
): Promise<ApiResponse<ResultDiagnosisResponse>> => {
  const response = await api.get<ApiResponse<ResultDiagnosisResponse>>(
    `/api/tasks/${taskId}/result-diagnosis`,
  );
  return response.data;
};

export const rerunResultDiagnosis = async (
  taskId: string,
): Promise<ApiResponse<ResultDiagnosisResponse>> => {
  const response = await api.post<ApiResponse<ResultDiagnosisResponse>>(
    `/api/result-diagnoses/${taskId}/rerun`,
    {},
  );
  return response.data;
};

export const getResultDiagnosisSummary = async (
  rdId: string,
): Promise<ApiResponse<ResultDiagnosisSummary>> => {
  const response = await api.get<ApiResponse<ResultDiagnosisSummary>>(
    `/api/result-diagnoses/${rdId}/summary`,
  );
  return response.data;
};

export const getClosedLoopRefinementInput = async (
  rdId: string,
): Promise<ApiResponse<ClosedLoopRefinementInput>> => {
  const response = await api.get<ApiResponse<ClosedLoopRefinementInput>>(
    `/api/result-diagnoses/${rdId}/closed-loop-refinement-input`,
  );
  return response.data;
};
