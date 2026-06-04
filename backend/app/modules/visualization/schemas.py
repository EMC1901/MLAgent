from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class CorrelationMatrixData(BaseModel):
    feature_names: List[str] = []
    matrix: List[List[float]] = []


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
    target_correlations: List[TargetCorrelationItem] = []
    feature_importance: List[FeatureImportanceItem] = []
    descriptor_distribution: List[DescriptorDistributionItem] = []


class PredictedVsActualData(BaseModel):
    points: List[Dict[str, float]] = []
    r_squared: float = 0.0
    rmse: float = 0.0
    mae: float = 0.0
    residual_mean: float = 0.0
    residual_std: float = 0.0
    histogram_bins: List[Dict[str, float]] = []


class ResidualPlotData(BaseModel):
    points: List[Dict[str, float]] = []
    r_squared: float = 0.0
    rmse: float = 0.0


class TrainTestComparisonData(BaseModel):
    comparisons: List[Dict[str, Any]] = []


class CrossValidationBoxPlotData(BaseModel):
    folds: List[Dict[str, Any]] = []
    metric_name: str = ""


class ConfusionMatrixData(BaseModel):
    labels: List[str] = []
    matrix: List[List[int]] = []


class ROCCurveData(BaseModel):
    curves: List[Dict[str, Any]] = []


class PRCurveData(BaseModel):
    curves: List[Dict[str, Any]] = []


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
    feature_analysis: FeatureAnalysisSection = FeatureAnalysisSection()
    model_performance: ModelPerformanceSection = ModelPerformanceSection()
