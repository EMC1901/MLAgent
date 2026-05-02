from pydantic import BaseModel
from typing import Optional, List


class FeaturizerSpec(BaseModel):
    id: str
    display_name: str
    description: str = ""
    input_modalities: List[str] = []
    feature_type: str
    supported_task_types: List[str] = ["regression", "classification"]
    aliases: List[str] = []
    status: str = "available"
    mvp_supported: bool = True
    requires_dependencies: List[str] = []
    dependency_status: dict = {}
    output_feature_kind: str = "numeric"
    estimated_feature_count: str = "10-50"
    fallback_priority: int = 10


class FeaturizerResolveResult(BaseModel):
    input_name: str
    resolved_id: Optional[str] = None
    matched_by: Optional[str] = None
    status: Optional[str] = None


class FeaturizerFallbackResult(BaseModel):
    fallback_featurizer_id: Optional[str] = None
    reason: str = ""


class FeaturizerRegistrySummary(BaseModel):
    featurizers: List[FeaturizerSpec] = []
    total_available: int = 0
    total_planned: int = 0


class FeaturizerRegistryQuery(BaseModel):
    input_modality: Optional[str] = None
    task_type: Optional[str] = None
    status: Optional[str] = "available"


class DependencyCheckResult(BaseModel):
    status: str = "unknown"
    version: Optional[str] = None


class DependenciesStatusResponse(BaseModel):
    dependencies: dict = {}


class FeaturizerDetailResponse(BaseModel):
    spec: Optional[FeaturizerSpec] = None
    dependency_status: dict = {}
    effective_status: str = "unknown"
