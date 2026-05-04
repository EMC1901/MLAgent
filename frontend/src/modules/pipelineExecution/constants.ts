export const STATUS_COLORS: Record<string, string> = {
  pending: '#9e9e9e',
  running: '#1976d2',
  completed: '#2e7d32',
  completed_with_warning: '#ff9800',
  partially_failed: '#ff9800',
  failed: '#c62828',
  skipped: '#9e9e9e',
  cancelled: '#757575',
};

export const TRIAL_STATUS_COLORS: Record<string, string> = {
  pending: '#9e9e9e',
  running: '#1976d2',
  completed: '#2e7d32',
  failed: '#c62828',
  skipped: '#ff9800',
};

export const ROLE_COLORS: Record<string, string> = {
  baseline: '#6a1b9a',
  candidate: '#1565c0',
  hpo_candidate: '#e65100',
};

export const TRIAL_TYPE_COLORS: Record<string, string> = {
  baseline: '#6a1b9a',
  fixed_params: '#1565c0',
  hpo: '#e65100',
};
