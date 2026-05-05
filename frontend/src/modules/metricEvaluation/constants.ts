export const STATUS_COLORS: Record<string, string> = {
  evaluating: '#1976d2',
  evaluated: '#2e7d32',
  evaluated_with_warning: '#e65100',
  partially_evaluated: '#e65100',
  failed: '#c62828',
  pending: '#9e9e9e',
};

export const STATUS_LABELS: Record<string, string> = {
  evaluating: 'Evaluating',
  evaluated: 'Evaluated',
  evaluated_with_warning: 'Evaluated (Warning)',
  partially_evaluated: 'Partially Evaluated',
  failed: 'Failed',
  pending: 'Pending',
};

export const DIRECTION_LABELS: Record<string, string> = {
  minimize: 'Lower is Better',
  maximize: 'Higher is Better',
};

export const ROLE_COLORS: Record<string, string> = {
  baseline: '#6c757d',
  candidate: '#1976d2',
  hpo_candidate: '#6a1b9a',
};
