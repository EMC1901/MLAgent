from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CorrelationMatrixData(BaseModel):
    feature_names: List[str] = Field(default_factory=list)
    matrix: List[List[float]] = Field(default_factory=list)


class TargetCorrelationItem(BaseModel):
    feature_name: str = ""
    pearson_r: float = 0.0
    spearman_rho: float = 0.0


class FeatureImportanceItem(BaseModel):
    feature_name: str = ""
    importance_value: float = 0.0
    importance_method: str = ""
    direction: str = ""
    feature_group: str = ""


class DescriptorDistributionItem(BaseModel):
    feature_name: str = ""
    variance: float = 0.0
    skewness: float = 0.0
    mean: float = 0.0
    std: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0


class FeatureAnalysisSection(BaseModel):
    correlation_matrix: Optional[CorrelationMatrixData] = None
    target_correlations: List[TargetCorrelationItem] = Field(default_factory=list)
    feature_importance: List[FeatureImportanceItem] = Field(default_factory=list)
    descriptor_distribution: List[DescriptorDistributionItem] = Field(default_factory=list)


class PredictedVsActualData(BaseModel):
    points: List[Dict[str, Any]] = Field(default_factory=list)
    r_squared: float = 0.0
    rmse: float = 0.0
    mae: float = 0.0
    residual_mean: float = 0.0
    residual_std: float = 0.0
    histogram_bins: List[Dict[str, float]] = Field(default_factory=list)
    primary_metric: str = ""
    primary_metric_value: Optional[float] = None
    split_metrics: List[Dict[str, Any]] = Field(default_factory=list)


class ResidualPlotData(BaseModel):
    points: List[Dict[str, Any]] = Field(default_factory=list)
    r_squared: float = 0.0
    rmse: float = 0.0


class TrainTestComparisonData(BaseModel):
    comparisons: List[Dict[str, Any]] = Field(default_factory=list)


class CrossValidationBoxPlotData(BaseModel):
    folds: List[Dict[str, Any]] = Field(default_factory=list)
    metric_name: str = ""


class ConfusionMatrixData(BaseModel):
    labels: List[str] = Field(default_factory=list)
    matrix: List[List[int]] = Field(default_factory=list)


class ROCCurveData(BaseModel):
    curves: List[Dict[str, Any]] = Field(default_factory=list)


class PRCurveData(BaseModel):
    curves: List[Dict[str, Any]] = Field(default_factory=list)


class ModelPerformanceSection(BaseModel):
    model_id: Optional[str] = None
    model_family: Optional[str] = None
    model_trial_id: Optional[str] = None
    predicted_vs_actual: Optional[PredictedVsActualData] = None
    residual_plot: Optional[ResidualPlotData] = None
    train_test_comparison: Optional[TrainTestComparisonData] = None
    cross_validation_box_plot: Optional[CrossValidationBoxPlotData] = None
    confusion_matrix: Optional[ConfusionMatrixData] = None
    roc_curve: Optional[ROCCurveData] = None
    pr_curve: Optional[PRCurveData] = None


class VisualizationDataResponse(BaseModel):
    task_id: str = ""
    task_type: str = ""
    feature_analysis: FeatureAnalysisSection = Field(default_factory=FeatureAnalysisSection)
    model_performance: ModelPerformanceSection = Field(default_factory=ModelPerformanceSection)
