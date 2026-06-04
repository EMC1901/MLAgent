export const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  analyzing: 'Analyzing',
  llm_advising: 'AI Advising',
  validating_advice: 'Validating Advice',
  updating: 'Updating',
  updated: 'Updated',
  updated_with_warning: 'Updated (with warnings)',
  failed: 'Failed',
  blocked: 'Blocked',
};

export const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  analyzing: 'processing',
  llm_advising: 'processing',
  validating_advice: 'processing',
  updating: 'processing',
  updated: 'success',
  updated_with_warning: 'warning',
  failed: 'error',
  blocked: 'error',
};
