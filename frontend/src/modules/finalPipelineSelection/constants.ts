export const STATUS_COLORS: Record<string, string> = {
  selecting: '#2196f3',
  selected: '#4caf50',
  selected_with_warning: '#ff9800',
  failed: '#f44336',
};

export const STATUS_LABELS: Record<string, string> = {
  selecting: 'Selecting',
  selected: 'Selected',
  selected_with_warning: 'Selected (Warning)',
  failed: 'Failed',
};

export const CANDIDATE_STATUS_COLORS: Record<string, string> = {
  eligible: '#2196f3',
  selected: '#4caf50',
  rejected: '#f44336',
  warning: '#ff9800',
};

export const CANDIDATE_STATUS_LABELS: Record<string, string> = {
  eligible: 'Eligible',
  selected: 'Selected',
  rejected: 'Rejected',
  warning: 'Warning',
};

export const PROFILE_LABELS: Record<string, string> = {
  metric_first: 'Metric First',
  balanced: 'Balanced',
  interpretable: 'Interpretable',
  efficient: 'Efficient',
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  low: '#f44336',
  medium: '#ff9800',
  high: '#4caf50',
};

export const INTEGRITY_COLORS: Record<string, string> = {
  complete: '#4caf50',
  partial: '#ff9800',
  missing: '#f44336',
};

export const DEFAULT_PROFILE = 'balanced';
