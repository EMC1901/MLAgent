export const STATUS_COLORS: Record<string, string> = {
  deciding: '#1976d2',
  decided: '#2e7d32',
  decided_with_warning: '#e65100',
  adopted: '#1565c0',
  failed: '#c62828',
};

export const STATUS_LABELS: Record<string, string> = {
  deciding: 'Deciding',
  decided: 'Decided',
  decided_with_warning: 'Decided (Warning)',
  adopted: 'Adopted',
  failed: 'Failed',
};

export const DECISION_COLORS: Record<string, string> = {
  proceed_next_stage: '#2e7d32',
  iterate_refinement: '#e65100',
};

export const DECISION_LABELS: Record<string, string> = {
  proceed_next_stage: 'Proceed to Final Selection',
  iterate_refinement: 'Iterate & Refine',
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  low: '#ff9800',
  medium: '#1976d2',
  high: '#4caf50',
};

export const RERUN_STAGE_COLORS: Record<string, string> = {
  workflow_planning: '#7b1fa2',
  feature_engineering: '#c2185b',
  feature_preprocessing: '#e65100',
  model_search_context: '#f57c00',
  model_search: '#1976d2',
  pipeline_generation: '#00838f',
  pipeline_execution: '#2e7d32',
  metric_evaluation: '#4527a0',
};

export const RERUN_STAGE_LABELS: Record<string, string> = {
  workflow_planning: 'Workflow Planning',
  feature_engineering: 'Feature Engineering',
  feature_preprocessing: 'Data Preprocessing',
  model_search_context: 'Model Search Context',
  model_search: 'Model Search',
  pipeline_generation: 'Pipeline Generation',
  pipeline_execution: 'Pipeline Execution',
  metric_evaluation: 'Metric Evaluation',
};
