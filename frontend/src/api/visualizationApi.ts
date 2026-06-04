import api from './taskApi';
import { VisualizationData, ApiResponse } from '../modules/visualization/types';

export const getVisualizationData = async (
  taskId: string,
): Promise<ApiResponse<VisualizationData>> => {
  const response = await api.get<ApiResponse<VisualizationData>>(
    `/api/visualization-data/${taskId}`,
  );
  return response.data;
};
