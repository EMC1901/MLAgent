export const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  loading_artifact: 'Loading Artifact',
  validating: 'Validating',
  filtering: 'Filtering',
  preprocessing: 'Preprocessing',
  artifact_saving: 'Saving Artifacts',
  preprocessed: 'Preprocessed',
  preprocessed_with_warning: 'Preprocessed (with warnings)',
  failed: 'Failed',
  blocked: 'Blocked',
};

export const STATUS_COLORS: Record<string, string> = {
  pending: 'default',
  loading_artifact: 'processing',
  validating: 'processing',
  filtering: 'processing',
  preprocessing: 'processing',
  artifact_saving: 'processing',
  preprocessed: 'success',
  preprocessed_with_warning: 'warning',
  failed: 'error',
  blocked: 'error',
};

export const DROP_REASON_LABELS: Record<string, string> = {
  non_numeric_object_column: 'Non-numeric Object',
  all_missing: 'All Missing',
  constant: 'Constant',
  high_missing: 'High Missing',
  invalid_inf_values: 'Invalid Inf Values',
};
