// Status labels & colors
export const STATUS_LABELS: Record<string, string> = {
  deciding: 'Deciding',
  decided: 'Decided',
  decided_with_warning: 'Decided (Warnings)',
  fallback: 'Fallback (Rules)',
  failed: 'Failed',
};

export const STATUS_COLORS: Record<string, string> = {
  deciding: '#1976d2',
  decided: '#2e7d32',
  decided_with_warning: '#ef6c00',
  fallback: '#f9a825',
  failed: '#c62828',
};

// Decision labels & colors
export const DECISION_LABELS: Record<string, string> = {
  iterate: 'ITERATE',
  stop: 'STOP',
};

export const DECISION_COLORS: Record<string, string> = {
  iterate: '#7b1fa2',
  stop: '#c62828',
};

// Confidence labels & colors
export const CONFIDENCE_LABELS: Record<string, string> = {
  high: 'High',
  medium: 'Medium',
  low: 'Low',
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  high: '#2e7d32',
  medium: '#ef6c00',
  low: '#c62828',
};

// Completion level colors
export const COMPLETION_COLORS: Record<string, string> = {
  achieved: '#2e7d32',
  partial: '#ef6c00',
  not_achieved: '#c62828',
};

// Gap magnitude colors
export const GAP_MAGNITUDE_COLORS: Record<string, string> = {
  small: '#ff9800',
  moderate: '#ef6c00',
  large: '#e65100',
  critical: '#c62828',
};

// Improvement estimate colors
export const IMPROVEMENT_COLORS: Record<string, string> = {
  high: '#2e7d32',
  moderate: '#ef6c00',
  low: '#c62828',
  none: '#9e9e9e',
};

// Stage labels
export const STAGE_LABELS: Record<string, string> = {
  task_specification: 'Task Spec',
  task_interpretation: 'Interpretation',
  dataset_profile: 'Dataset Profile',
  workflow_planning: 'Workflow Plan',
  feature_engineering: 'Feature Engineering',
  feature_preprocessing: 'Data Preprocessing',
  model_search_context: 'Model Search',
  pipeline_generation: 'Pipeline Gen',
  pipeline_execution: 'Pipeline Exec',
  metric_evaluation: 'Metric Eval',
};

export const STAGE_COLORS: Record<string, string> = {
  task_specification: '#9e9e9e',
  task_interpretation: '#78909c',
  dataset_profile: '#00838f',
  workflow_planning: '#1976d2',
  feature_engineering: '#00695c',
  feature_preprocessing: '#4a148c',
  model_search_context: '#e65100',
  pipeline_generation: '#bf360c',
  pipeline_execution: '#827717',
  metric_evaluation: '#3e2723',
};

// Stage action labels
export const ACTION_LABELS: Record<string, string> = {
  expand: 'Expand',
  replace: 'Replace',
  add: 'Add',
  remove: 'Remove',
  adjust: 'Adjust',
  keep: 'Keep',
};

export const ACTION_COLORS: Record<string, string> = {
  expand: '#2e7d32',
  replace: '#c62828',
  add: '#1976d2',
  remove: '#f44336',
  adjust: '#ef6c00',
  keep: '#9e9e9e',
};

// Root cause dimension labels
export const DIMENSION_LABELS: Record<string, string> = {
  data_side: 'Data',
  feature_side: 'Features',
  model_side: 'Model',
  evaluation_side: 'Evaluation',
};

export const DIMENSION_COLORS: Record<string, string> = {
  data_side: '#00838f',
  feature_side: '#00695c',
  model_side: '#e65100',
  evaluation_side: '#3e2723',
};

// Stop category labels
export const STOP_CATEGORY_LABELS: Record<string, string> = {
  target_achieved: 'Target Achieved',
  converged: 'Converged',
  diminishing_returns: 'Diminishing Returns',
  resource_limit: 'Resource Limit',
  insoluble: 'Insoluble',
};
