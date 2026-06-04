import api, { ApiResponse } from './taskApi';

export interface LLMConfigRequest {
  model_name: string;
  thinking_enabled: boolean;
  api_key: string;
  base_url?: string;
}

export interface LLMConfigData {
  model_name: string;
  thinking_enabled: boolean;
  api_key_masked: string;
  base_url: string;
  is_custom: boolean;
}

export interface LLMValidationData {
  valid: boolean;
  message: string;
  model_name: string;
  latency_ms: number;
  tokens_used: number;
}

export interface LLMConfigSetResponse {
  config: LLMConfigData;
  validation: LLMValidationData;
}

export const setLLMConfig = async (
  request: LLMConfigRequest
): Promise<ApiResponse<LLMConfigSetResponse>> => {
  const response = await api.post<ApiResponse<LLMConfigSetResponse>>(
    '/api/llm-config',
    request
  );
  return response.data;
};

export const getLLMConfig = async (): Promise<ApiResponse<LLMConfigData>> => {
  const response = await api.get<ApiResponse<LLMConfigData>>('/api/llm-config');
  return response.data;
};

export const resetLLMConfig = async (): Promise<ApiResponse<LLMConfigData>> => {
  const response = await api.delete<ApiResponse<LLMConfigData>>('/api/llm-config');
  return response.data;
};
