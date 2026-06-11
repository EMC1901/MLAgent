import api from './taskApi';
import {
  FeaturePreprocessingResponse,
  FeaturePreprocessingCreateRequest,
  PreviewResponse,
  ApiResponse,
  PlanResponse,
  RationaleResponse,
  ExecutionReportResponse,
  RemovedFeaturesResponse,
  FeatureLineageResponse,
  ArtifactManifestResponse,
  ProvenanceResponse,
  CapabilitiesResponse,
  PlanRequest,
  ExecuteRequest,
} from '../modules/featurePreprocessing/types';

// Feature preprocessing LLM calls can take 5-10 min for thinking models
// (glm-5.1 with reasoning). With retries the total may reach ~15 min.
const FEATURE_PREPROCESSING_TIMEOUT = 900000; // 15 minutes

export const createFeaturePreprocessing = async (
  taskId: string,
  request?: FeaturePreprocessingCreateRequest,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.post<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${taskId}`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

export const getFeaturePreprocessing = async (
  preprocessingId: string,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.get<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${preprocessingId}`,
  );
  return response.data;
};

export const getLatestFeaturePreprocessingByTaskId = async (
  taskId: string,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.get<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/tasks/${taskId}/feature-preprocessing`,
  );
  return response.data;
};

export const rerunFeaturePreprocessing = async (
  taskId: string,
  request?: FeaturePreprocessingCreateRequest,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.post<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${taskId}/rerun`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

export const getModelReadyPreview = async (
  preprocessingId: string,
): Promise<ApiResponse<PreviewResponse>> => {
  const response = await api.get<ApiResponse<PreviewResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/preview`,
  );
  return response.data;
};

// Capabilities
export const getFPCapabilities = async (): Promise<ApiResponse<CapabilitiesResponse>> => {
  const response = await api.get<ApiResponse<CapabilitiesResponse>>(
    '/api/feature-preprocessing/capabilities',
  );
  return response.data;
};

// Plan-only (generate plan without execution)
export const generatePreprocessingPlan = async (
  taskId: string,
  request?: PlanRequest,
): Promise<ApiResponse<PlanResponse>> => {
  const response = await api.post<ApiResponse<PlanResponse>>(
    `/api/feature-preprocessing/${taskId}/plan`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

// Execute (execute a validated plan)
export const executePreprocessingPlan = async (
  taskId: string,
  request?: ExecuteRequest,
): Promise<ApiResponse<FeaturePreprocessingResponse>> => {
  const response = await api.post<ApiResponse<FeaturePreprocessingResponse>>(
    `/api/feature-preprocessing/${taskId}/execute`,
    request || {},
    { timeout: FEATURE_PREPROCESSING_TIMEOUT },
  );
  return response.data;
};

// Sub-resource: Plan
export const getPreprocessingPlan = async (
  preprocessingId: string,
): Promise<ApiResponse<PlanResponse>> => {
  const response = await api.get<ApiResponse<PlanResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/plan`,
  );
  return response.data;
};

// Sub-resource: Rationale
export const getPreprocessingRationale = async (
  preprocessingId: string,
): Promise<ApiResponse<RationaleResponse>> => {
  const response = await api.get<ApiResponse<RationaleResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/rationale`,
  );
  return response.data;
};

// Sub-resource: Execution Report
export const getPreprocessingExecutionReport = async (
  preprocessingId: string,
): Promise<ApiResponse<ExecutionReportResponse>> => {
  const response = await api.get<ApiResponse<ExecutionReportResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/execution-report`,
  );
  return response.data;
};

// Sub-resource: Removed Features
export const getPreprocessingRemovedFeatures = async (
  preprocessingId: string,
): Promise<ApiResponse<RemovedFeaturesResponse>> => {
  const response = await api.get<ApiResponse<RemovedFeaturesResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/removed-features`,
  );
  return response.data;
};

// Sub-resource: Feature Lineage
export const getPreprocessingFeatureLineage = async (
  preprocessingId: string,
): Promise<ApiResponse<FeatureLineageResponse>> => {
  const response = await api.get<ApiResponse<FeatureLineageResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/feature-lineage`,
  );
  return response.data;
};

// Sub-resource: Artifact Manifest
export const getPreprocessingArtifactManifest = async (
  preprocessingId: string,
): Promise<ApiResponse<ArtifactManifestResponse>> => {
  const response = await api.get<ApiResponse<ArtifactManifestResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/artifact-manifest`,
  );
  return response.data;
};

// Sub-resource: Provenance
export const getPreprocessingProvenance = async (
  preprocessingId: string,
): Promise<ApiResponse<ProvenanceResponse>> => {
  const response = await api.get<ApiResponse<ProvenanceResponse>>(
    `/api/feature-preprocessing/${preprocessingId}/provenance`,
  );
  return response.data;
};
