import api from './taskApi';
import {
  TaskInterpretationResponse,
  TaskInterpretationCreateRequest,
  ApiResponse,
} from '../modules/taskInterpretation/types';

export const createInterpretation = async (
  taskId: string,
  request?: TaskInterpretationCreateRequest,
): Promise<ApiResponse<TaskInterpretationResponse>> => {
  const response = await api.post<ApiResponse<TaskInterpretationResponse>>(
    `/api/task-interpretations/${taskId}`,
    request || {},
  );
  return response.data;
};

export const getInterpretation = async (
  interpretationId: string,
): Promise<ApiResponse<TaskInterpretationResponse>> => {
  const response = await api.get<ApiResponse<TaskInterpretationResponse>>(
    `/api/task-interpretations/${interpretationId}`,
  );
  return response.data;
};

export const getLatestInterpretation = async (
  taskId: string,
): Promise<ApiResponse<TaskInterpretationResponse>> => {
  const response = await api.get<ApiResponse<TaskInterpretationResponse>>(
    `/api/tasks/${taskId}/interpretation`,
  );
  return response.data;
};

export const rerunInterpretation = async (
  taskId: string,
  request?: TaskInterpretationCreateRequest,
): Promise<ApiResponse<TaskInterpretationResponse>> => {
  const response = await api.post<ApiResponse<TaskInterpretationResponse>>(
    `/api/task-interpretations/${taskId}/rerun`,
    request || {},
  );
  return response.data;
};
