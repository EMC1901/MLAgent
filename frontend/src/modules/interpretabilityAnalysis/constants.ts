export const STATUS_COLORS: Record<string, string> = {
  analyzing: '#2196f3',
  analyzed: '#4caf50',
  analyzed_with_warning: '#ff9800',
  failed: '#f44336',
};

export const STATUS_LABELS: Record<string, string> = {
  analyzing: 'Analyzing',
  analyzed: 'Analyzed',
  analyzed_with_warning: 'Analyzed (Warning)',
  failed: 'Failed',
};

export const PROFILE_LABELS: Record<string, string> = {
  compact: 'Compact',
  standard: 'Standard',
  full: 'Full',
};

export const CONFIDENCE_COLORS: Record<string, string> = {
  low: '#f44336',
  medium: '#ff9800',
  high: '#4caf50',
};

export const DIRECTION_LABELS: Record<string, string> = {
  positive: '+',
  negative: '-',
  non_monotonic: '~',
  unknown: '?',
};

export const DIRECTION_COLORS: Record<string, string> = {
  positive: '#4caf50',
  negative: '#f44336',
  non_monotonic: '#ff9800',
  unknown: '#9e9e9e',
};

export const EVIDENCE_COLORS: Record<string, string> = {
  weak: '#f44336',
  moderate: '#ff9800',
  strong: '#4caf50',
};

export const METHOD_LABELS: Record<string, string> = {
  coefficient: 'Coefficient Importance',
  native_importance: 'Native Importance',
  permutation_importance: 'Permutation Importance',
  shap: 'SHAP',
};

export const DEFAULT_PROFILE = 'standard';
