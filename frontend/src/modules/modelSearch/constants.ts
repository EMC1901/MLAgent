export const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  loading_context: 'Loading Context',
  llm_advising: 'LLM Advising',
  validating_advice: 'Validating Advice',
  generating_plan: 'Generating Plan',
  planned: 'Planned',
  planned_with_warning: 'Planned (with warnings)',
  failed: 'Failed',
  blocked: 'Blocked',
};

export const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  loading_context: 'processing',
  llm_advising: 'processing',
  validating_advice: 'processing',
  generating_plan: 'processing',
  planned: 'success',
  planned_with_warning: 'warning',
  failed: 'error',
  blocked: 'error',
};

export const PRIORITY_COLORS: Record<string, string> = {
  high: '#2e7d32',
  medium: '#1976d2',
  low: '#9e9e9e',
};

export const BUDGET_COLORS: Record<string, string> = {
  low: '#ff9800',
  moderate: '#1976d2',
  high: '#2e7d32',
};

export const METRIC_DIRECTION_LABELS: Record<string, string> = {
  minimize: 'Minimize (lower is better)',
  maximize: 'Maximize (higher is better)',
};
