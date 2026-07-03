import api from './taskApi';
import {
  DatasetProfileResponse,
  DatasetFileUploadResponse,
  DatasetPreviewResponse,
  ApiResponse,
} from '../modules/datasetProfile/types';

export const uploadDatasetFile = async (
  file: File,
): Promise<ApiResponse<DatasetFileUploadResponse>> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<ApiResponse<DatasetFileUploadResponse>>(
    '/api/dataset-profiles/upload',
    formData,
    {
      headers: {
        'Content-Type': undefined,
      },
    },
  );
  return response.data;
};

export const createDatasetProfile = async (
  taskId: string,
  uploadedFileId?: string,
): Promise<ApiResponse<DatasetProfileResponse>> => {
  const body: Record<string, unknown> = {};
  if (uploadedFileId) {
    body.uploaded_file_id = uploadedFileId;
  }
  const response = await api.post<ApiResponse<DatasetProfileResponse>>(
    `/api/dataset-profiles/${taskId}`,
    body,
  );
  return response.data;
};

export const getDatasetProfile = async (
  profileId: string,
): Promise<ApiResponse<DatasetProfileResponse>> => {
  const response = await api.get<ApiResponse<DatasetProfileResponse>>(
    `/api/dataset-profiles/${profileId}`,
  );
  return response.data;
};

export const getLatestDatasetProfileByTaskId = async (
  taskId: string,
): Promise<ApiResponse<DatasetProfileResponse>> => {
  const response = await api.get<ApiResponse<DatasetProfileResponse>>(
    `/api/tasks/${taskId}/dataset-profile`,
  );
  return response.data;
};

export const rerunDatasetProfile = async (
  taskId: string,
  uploadedFileId?: string,
): Promise<ApiResponse<DatasetProfileResponse>> => {
  const body: Record<string, unknown> = {};
  if (uploadedFileId) {
    body.uploaded_file_id = uploadedFileId;
  }
  const response = await api.post<ApiResponse<DatasetProfileResponse>>(
    `/api/dataset-profiles/${taskId}/rerun`,
    body,
  );
  return response.data;
};

export const getDatasetPreview = async (
  profileId: string,
): Promise<ApiResponse<DatasetPreviewResponse>> => {
  const response = await api.get<ApiResponse<DatasetPreviewResponse>>(
    `/api/dataset-profiles/${profileId}/preview`,
  );
  return response.data;
};
