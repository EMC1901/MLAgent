export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
  error_code?: string;
}

export interface CorrelationMatrixData {
  feature_names: string[];
  matrix: number[][];
}

export interface TargetCorrelationItem {
  feature_name: string;
  pearson_r: number;
  spearman_rho: number;
}

export interface FeatureImportanceItem {
  feature_name: string;
  importance_value: number;
  importance_method: string;
  direction: string;
  feature_group: string;
}

export interface DescriptorDistributionItem {
  feature_name: string;
  variance: number;
  skewness: number;
  mean: number;
  std: number;
  min_val: number;
  max_val: number;
}

export interface FeatureAnalysisSection {
  correlation_matrix: CorrelationMatrixData | null;
  target_correlations: TargetCorrelationItem[];
  feature_importance: FeatureImportanceItem[];
  descriptor_distribution: DescriptorDistributionItem[];
}

export interface PredictedVsActualData {
  points: { actual: number; predicted: number; residual: number; split?: string }[];
  r_squared: number;
  rmse: number;
  mae: number;
  residual_mean: number;
  residual_std: number;
  histogram_bins: { bin_start: number; bin_end: number; count: number }[];
  primary_metric?: string;
  primary_metric_value?: number | null;
  split_metrics?: { split: string; metric_name: string; metric_value: number }[];
}

export interface ResidualPlotData {
  points: { predicted: number; residual: number; split?: string }[];
  r_squared: number;
  rmse: number;
}

export interface TrainTestComparisonData {
  comparisons: { fold_index: number; test_value: number; n_samples: number }[];
}

export interface CrossValidationBoxPlotData {
  folds: { trial_id: string; model_family: string; fold_index: number; metric_value: number }[];
  metric_name: string;
}

export interface ConfusionMatrixData {
  labels: string[];
  matrix: number[][];
}

export interface ROCCurveData {
  curves: { class_id: string; fpr: number[]; tpr: number[]; auc: number }[];
}

export interface PRCurveData {
  curves: { class_id: string; recall: number[]; precision: number[]; average_precision: number }[];
}

export interface ModelPerformanceSection {
  model_id: string | null;
  model_family: string | null;
  model_trial_id: string | null;
  predicted_vs_actual: PredictedVsActualData | null;
  residual_plot: ResidualPlotData | null;
  train_test_comparison: TrainTestComparisonData | null;
  cross_validation_box_plot: CrossValidationBoxPlotData | null;
  confusion_matrix: ConfusionMatrixData | null;
  roc_curve: ROCCurveData | null;
  pr_curve: PRCurveData | null;
}

export interface VisualizationData {
  task_id: string;
  task_type: string;
  feature_analysis: FeatureAnalysisSection;
  model_performance: ModelPerformanceSection;
}
