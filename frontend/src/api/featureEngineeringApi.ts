import api from './taskApi';
import {
  FeatureEngineeringResponse,
  FeatureEngineeringCreateRequest,
  FeaturePreviewResponse,
  ApiResponse,
  RegistryListResponse,
  RegistryDetailResponse,
  DependenciesStatusResponse,
} from '../modules/featureEngineering/types';

// Feature engineering can take much longer due to matminer featurizers
// (e.g., 4604 rows × 3 featurizers ≈ 7-10 minutes)
const FEATURE_ENGINEERING_TIMEOUT = 600000; // 10 minutes

export const createFeatureEngineering = async (
  taskId: string,
  request?: FeatureEngineeringCreateRequest,
): Promise<ApiResponse<FeatureEngineeringResponse>> => {
  const response = await api.post<ApiResponse<FeatureEngineeringResponse>>(
    `/api/feature-engineering/${taskId}`,
    request || {},
    { timeout: FEATURE_ENGINEERING_TIMEOUT },
  );
  return response.data;
};

export const getFeatureEngineering = async (
  featureEngineeringId: string,
): Promise<ApiResponse<FeatureEngineeringResponse>> => {
  const response = await api.get<ApiResponse<FeatureEngineeringResponse>>(
    `/api/feature-engineering/${featureEngineeringId}`,
  );
  return response.data;
};

export const getLatestFeatureEngineeringByTaskId = async (
  taskId: string,
): Promise<ApiResponse<FeatureEngineeringResponse>> => {
  const response = await api.get<ApiResponse<FeatureEngineeringResponse>>(
    `/api/tasks/${taskId}/feature-engineering`,
  );
  return response.data;
};

export const rerunFeatureEngineering = async (
  taskId: string,
  request?: FeatureEngineeringCreateRequest,
): Promise<ApiResponse<FeatureEngineeringResponse>> => {
  const response = await api.post<ApiResponse<FeatureEngineeringResponse>>(
    `/api/feature-engineering/${taskId}/rerun`,
    request || {},
    { timeout: FEATURE_ENGINEERING_TIMEOUT },
  );
  return response.data;
};

export const getFeatureMatrixPreview = async (
  featureEngineeringId: string,
): Promise<ApiResponse<FeaturePreviewResponse>> => {
  const response = await api.get<ApiResponse<FeaturePreviewResponse>>(
    `/api/feature-engineering/${featureEngineeringId}/preview`,
  );
  return response.data;
};

// Registry API
export interface RegistryQueryParams {
  input_modality?: string;
  task_type?: string;
  status?: string;
  feature_type?: string;
  requires_dependency?: string;
  mvp_supported?: boolean;
}

export const getFeaturizers = async (
  params?: RegistryQueryParams,
): Promise<ApiResponse<RegistryListResponse>> => {
  const response = await api.get<ApiResponse<RegistryListResponse>>(
    '/api/registries/featurizers',
    { params },
  );
  return response.data;
};

export const getFeaturizerDetail = async (
  featurizerId: string,
): Promise<ApiResponse<RegistryDetailResponse>> => {
  const response = await api.get<ApiResponse<RegistryDetailResponse>>(
    `/api/registries/featurizers/${featurizerId}`,
  );
  return response.data;
};

export const getFeaturizerDependencies = async (): Promise<
  ApiResponse<DependenciesStatusResponse>
> => {
  const response = await api.get<ApiResponse<DependenciesStatusResponse>>(
    '/api/registries/featurizers/dependencies',
  );
  return response.data;
};

// FE Capabilities
export const getFECapabilities = async (): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    '/api/feature-engineering/capabilities',
  );
  return response.data;
};

// Sub-resource: Execution Report
export const getFEExecutionReport = async (
  featureEngineeringId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/feature-engineering/${featureEngineeringId}/execution-report`,
  );
  return response.data;
};

// Sub-resource: Feature Groups
export const getFEFeatureGroups = async (
  featureEngineeringId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/feature-engineering/${featureEngineeringId}/feature-groups`,
  );
  return response.data;
};

// Sub-resource: Quality Profile
export const getFEQualityProfile = async (
  featureEngineeringId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/feature-engineering/${featureEngineeringId}/quality-profile`,
  );
  return response.data;
};

// Sub-resource: Preprocessing Decision Input
export const getFEPreprocessingDecisionInput = async (
  featureEngineeringId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/feature-engineering/${featureEngineeringId}/preprocessing-decision-input`,
  );
  return response.data;
};

// Sub-resource: Provenance
export const getFEProvenance = async (
  featureEngineeringId: string,
): Promise<ApiResponse<Record<string, unknown>>> => {
  const response = await api.get<ApiResponse<Record<string, unknown>>>(
    `/api/feature-engineering/${featureEngineeringId}/provenance`,
  );
  return response.data;
};
