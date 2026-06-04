export const STATUS_COLORS: Record<string, string> = {
  diagnosing: '#1976d2',
  diagnosed: '#2e7d32',
  diagnosed_with_warning: '#e65100',
  fallback_diagnosed: '#e65100',
  failed: '#c62828',
  pending: '#9e9e9e',
};

export const STATUS_LABELS: Record<string, string> = {
  diagnosing: 'Diagnosing',
  diagnosed: 'Diagnosed',
  diagnosed_with_warning: 'Diagnosed (Warning)',
  fallback_diagnosed: 'Fallback Diagnosed',
  failed: 'Failed',
  pending: 'Pending',
};

export const DIAGNOSIS_TYPE_COLORS: Record<string, string> = {
  underfitting: '#e65100',
  overfitting_risk: '#c62828',
  feature_insufficiency: '#6a1b9a',
  feature_noise: '#6a1b9a',
  model_mismatch: '#d84315',
  hpo_insufficient: '#f9a825',
  validation_instability: '#c2185b',
  weak_baseline_improvement: '#1976d2',
  data_quality_limitation: '#00838f',
  metric_mismatch: '#4527a0',
  limited_pipeline_gain: '#546e7a',
};

export const SEVERITY_COLORS: Record<string, string> = {
  low: '#4caf50',
  medium: '#ff9800',
  high: '#f44336',
  critical: '#b71c1c',
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  low: '#ff9800',
  medium: '#1976d2',
  high: '#4caf50',
};

export const EVIDENCE_STRENGTH_COLORS: Record<string, string> = {
  weak: '#ff9800',
  moderate: '#1976d2',
  strong: '#4caf50',
};

export const PRIORITY_COLORS: Record<string, string> = {
  high: '#c62828',
  medium: '#e65100',
  low: '#546e7a',
};

export const PERFORMANCE_COLORS: Record<string, string> = {
  excellent: '#2e7d32',
  acceptable: '#1976d2',
  weak: '#e65100',
  failed: '#c62828',
};

export const IMPROVEMENT_LABELS: Record<string, string> = {
  strong: 'Strong',
  moderate: 'Moderate',
  weak: 'Weak',
  none: 'None',
  unknown: 'Unknown',
};

export const STABILITY_LABELS: Record<string, string> = {
  stable: 'Stable',
  moderately_unstable: 'Moderately Unstable',
  unstable: 'Unstable',
};

export const TARGET_STAGE_LABELS: Record<string, string> = {
  workflow_planning: 'Workflow Planning',
  feature_engineering: 'Feature Engineering',
  preprocessing: 'Preprocessing',
  model_search: 'Model Search',
  hpo: 'HPO',
  validation: 'Validation',
};

export const RECOMMENDATION_TYPE_LABELS: Record<string, string> = {
  expand_features: 'Expand Features',
  change_models: 'Change Models',
  increase_hpo: 'Increase HPO',
  adjust_validation: 'Adjust Validation',
  change_metric: 'Change Metric',
};

export const DIAGNOSIS_MODE_LABELS: Record<string, string> = {
  llm_based: 'AI Based',
  hybrid: 'Hybrid (AI + System)',
  system_rule_based: 'System Rule Based',
};
