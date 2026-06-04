import axios from 'axios';

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 600000,
});

api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.baseURL}${config.url}`, config.data ?? '');
    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  },
);

api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}:`, response.data);
    return response;
  },
  (error) => {
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED' || error.message?.includes('Network Error')) {
      console.error('[API] Network Error: Backend at', error.config?.baseURL, 'is not reachable. Is the backend server running?');
    } else if (error.code === 'ERR_CANCELED') {
      console.error('[API] Request timeout:', error.config?.url);
    } else if (error.response) {
      console.error(`[API] HTTP ${error.response.status} from ${error.config?.url}:`, error.response.data);
    } else {
      console.error('[API] Unknown error:', error.message, error);
    }
    return Promise.reject(error);
  },
);

export interface TaskSpecificationCreateRequest {
  task_name?: string;
  task_description?: string;
  material_system?: string;
  prediction_target?: string;
  task_type?: string;
  dataset_description?: string;
  input_type?: string;
  target_column?: string;
  evaluation_metric?: string;
  user_priority?: string[];
  constraints?: string[];
}

export interface TaskSpecificationResponse {
  task_id: string;
  task_name?: string;
  task_description?: string;
  material_system?: string;
  prediction_target?: string;
  task_type?: string;
  dataset_description?: string;
  input_type?: string;
  target_column?: string;
  evaluation_metric?: string;
  user_priority?: string[];
  constraints?: string[];
  status: string;
  missing_fields?: string[];
  validation_messages?: string[];
  created_at?: string;
  updated_at?: string;
}


export interface TaskSummaryResponse {
  task_id: string;
  task_name?: string;
  task_type?: string;
  prediction_target?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}

export const createTask = async (
  request: TaskSpecificationCreateRequest
): Promise<ApiResponse<TaskSpecificationResponse>> => {
  const response = await api.post<ApiResponse<TaskSpecificationResponse>>('/api/tasks', request);
  return response.data;
};

export const getTask = async (
  taskId: string
): Promise<ApiResponse<TaskSpecificationResponse>> => {
  const response = await api.get<ApiResponse<TaskSpecificationResponse>>(`/api/tasks/${taskId}`);
  return response.data;
};

export const updateTask = async (
  taskId: string,
  request: Partial<TaskSpecificationCreateRequest>
): Promise<ApiResponse<TaskSpecificationResponse>> => {
  const response = await api.put<ApiResponse<TaskSpecificationResponse>>(`/api/tasks/${taskId}`, request);
  return response.data;
};

export const listTasks = async (): Promise<ApiResponse<TaskSummaryResponse[]>> => {
  const response = await api.get<ApiResponse<TaskSummaryResponse[]>>('/api/tasks');
  return response.data;
};

export default api;
