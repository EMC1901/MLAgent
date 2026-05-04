import React, { useState } from 'react';
import {
  createModelSearchContext,
  rerunModelSearchContext,
} from '../../../api/modelSearchContextApi';
import { ModelSearchContextResponse } from '../types';

interface ModelSearchContextPanelProps {
  taskId: string;
}

const ModelSearchContextPanel: React.FC<ModelSearchContextPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ModelSearchContextResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createModelSearchContext(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run model search context update.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunModelSearchContext(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run model search context update.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'updated': return '#4caf50';
      case 'updated_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      case 'blocked': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...styles.badge, backgroundColor: color }}>{label}</span>
  );

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={styles.section}>
      <strong style={styles.sectionTitle}>{title}</strong>
      <div style={styles.sectionContent}>{children}</div>
    </div>
  );

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Model Search Context Update</h3>
      <p style={styles.description}>
        Analyze the model-ready dataset after preprocessing and use LLM-guided strategy
        analysis to update the model search context before HPO and training.
      </p>

      <div style={styles.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={styles.runButton}>
          {loading ? 'Running...' : 'Run Context Update'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={styles.rerunButton}>
          {loading ? 'Running...' : 'Re-run Update'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Model Search Context Result</h4>

          <div style={styles.fieldRow}>
            <div style={styles.field}><strong>Context ID:</strong> {result.context_id}</div>
            <div style={styles.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={styles.field}><strong>Update Mode:</strong> {result.update_mode}</div>
            <div style={styles.field}><strong>Confidence:</strong> {result.confidence_score != null ? result.confidence_score.toFixed(2) : 'N/A'}</div>
          </div>

          {/* Dataset Effective Profile */}
          {result.dataset_effective_profile && (
            <Section title="Effective Dataset Profile">
              <div>Samples: {result.dataset_effective_profile.n_samples}</div>
              <div>Raw Features: {result.dataset_effective_profile.n_raw_features}</div>
              <div>
                Final Features:{' '}
                <Badge
                  label={String(result.dataset_effective_profile.n_final_features)}
                  color={result.dataset_effective_profile.n_final_features < 20 ? '#ff9800' : '#1976d2'}
                />
              </div>
              <div>Dropped Features: {result.dataset_effective_profile.n_dropped_features}</div>
              <div>
                Reduction Ratio:{' '}
                <Badge
                  label={`${(result.dataset_effective_profile.feature_reduction_ratio * 100).toFixed(1)}%`}
                  color={result.dataset_effective_profile.feature_reduction_ratio > 0.8 ? '#ff9800' : '#1976d2'}
                />
              </div>
              <div>Target Column: {result.dataset_effective_profile.target_column}</div>
              <div>Task Type: {result.dataset_effective_profile.task_type}</div>
            </Section>
          )}

          {/* Feature Group Summary */}
          {result.feature_group_summary && (
            <Section title="Feature Group Summary">
              <div>
                Retained Groups:{' '}
                {result.feature_group_summary.retained_groups.length > 0
                  ? result.feature_group_summary.retained_groups.map((g, i) => (
                      <Badge key={i} label={g} color="#2e7d32" />
                    ))
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
              <div>
                Dropped Groups:{' '}
                {result.feature_group_summary.dropped_groups.length > 0
                  ? result.feature_group_summary.dropped_groups.map((g, i) => (
                      <Badge key={i} label={g} color="#c62828" />
                    ))
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
              {result.feature_group_summary.partially_retained_groups && result.feature_group_summary.partially_retained_groups.length > 0 && (
                <div>
                  Partially Retained:{' '}
                  {result.feature_group_summary.partially_retained_groups.map((g, i) => (
                    <Badge key={i} label={g} color="#ff9800" />
                  ))}
                </div>
              )}
              <div>
                Low Feature Warning:{' '}
                <span style={{ color: result.feature_group_summary.low_effective_feature_warning ? '#ff9800' : '#2e7d32', fontWeight: 600 }}>
                  {result.feature_group_summary.low_effective_feature_warning ? 'Yes' : 'No'}
                </span>
              </div>
            </Section>
          )}

          {/* Preprocessing Summary */}
          {result.preprocessing_summary && (
            <Section title="Preprocessing Summary">
              <div>
                Imputation:{' '}
                {result.preprocessing_summary.imputation_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Scaling:{' '}
                {result.preprocessing_summary.scaling_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Feature Selection:{' '}
                {result.preprocessing_summary.feature_selection_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Categorical Encoding:{' '}
                {result.preprocessing_summary.categorical_encoding_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
            </Section>
          )}

          {/* LLM Strategy Advice */}
          {result.llm_strategy_advice && (
            <Section title="LLM Strategy Advice">
              <div>
                Confidence:{' '}
                <Badge
                  label={`${Math.round((result.llm_strategy_advice.confidence_score || 0) * 100)}%`}
                  color={(result.llm_strategy_advice.confidence_score || 0) >= 0.7 ? '#2e7d32' : '#ff9800'}
                />
              </div>
              <div>
                Candidate Models:{' '}
                {result.llm_strategy_advice.candidate_model_families.length > 0
                  ? result.llm_strategy_advice.candidate_model_families.map((m, i) => (
                      <Badge key={i} label={m} color="#1565c0" />
                    ))
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
              <div>
                Baselines:{' '}
                {result.llm_strategy_advice.baseline_models.length > 0
                  ? result.llm_strategy_advice.baseline_models.map((m, i) => (
                      <Badge key={i} label={m} color="#6a1b9a" />
                    ))
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
              <div>Model Bias: {result.llm_strategy_advice.preferred_model_bias}</div>
              <div>HPO Method: {result.llm_strategy_advice.hpo_search_method}</div>
              <div>
                HPO Budget:{' '}
                <Badge
                  label={result.llm_strategy_advice.hpo_budget_level}
                  color={result.llm_strategy_advice.hpo_budget_level === 'low' ? '#ff9800' : result.llm_strategy_advice.hpo_budget_level === 'high' ? '#2e7d32' : '#1976d2'}
                />
                {' '}({result.llm_strategy_advice.max_trials} trials)
              </div>
              <div>Validation: {result.llm_strategy_advice.validation_split_strategy} ({result.llm_strategy_advice.n_splits} splits)</div>
              {result.llm_strategy_advice.adjustment_reasons && result.llm_strategy_advice.adjustment_reasons.length > 0 && (
                <div>
                  Adjustment Reasons:{' '}
                  {result.llm_strategy_advice.adjustment_reasons.map((r, i) => (
                    <Badge key={i} label={r} color="#ff9800" />
                  ))}
                </div>
              )}
              {result.llm_strategy_advice.risk_notes && result.llm_strategy_advice.risk_notes.length > 0 && (
                <div>
                  Risk Notes:{' '}
                  {result.llm_strategy_advice.risk_notes.map((r, i) => (
                    <Badge key={i} label={r} color="#c62828" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* LLM Advice Validation */}
          {result.system_validation_result && (
            <Section title="LLM Advice Validation">
              <div>
                Is Valid:{' '}
                <span style={{ color: result.system_validation_result.is_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.system_validation_result.is_valid ? 'Yes' : 'No'}
                </span>
              </div>
              <div>
                Fallback Applied:{' '}
                <span style={{ color: result.system_validation_result.fallback_applied ? '#ff9800' : '#2e7d32', fontWeight: 600 }}>
                  {result.system_validation_result.fallback_applied ? 'Yes' : 'No'}
                </span>
              </div>
              {result.system_validation_result.rejected_suggestions && result.system_validation_result.rejected_suggestions.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#c62828' }}>Rejected Suggestions:</strong>
                  {result.system_validation_result.rejected_suggestions.map((s, i) => (
                    <div key={i} style={{ marginLeft: '16px', fontSize: '12px', color: '#c62828' }}>
                      ✗ {s}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Strategy Adjustments */}
          {result.strategy_adjustment && (
            <Section title="Strategy Adjustments">
              <div>
                Model Strategy:{' '}
                <Badge label={result.strategy_adjustment.model_strategy_adjusted ? 'Adjusted' : 'Unchanged'} color={result.strategy_adjustment.model_strategy_adjusted ? '#1565c0' : '#9e9e9e'} />
              </div>
              <div>
                HPO Strategy:{' '}
                <Badge label={result.strategy_adjustment.hpo_strategy_adjusted ? 'Adjusted' : 'Unchanged'} color={result.strategy_adjustment.hpo_strategy_adjusted ? '#1565c0' : '#9e9e9e'} />
              </div>
              <div>
                Validation Strategy:{' '}
                <Badge label={result.strategy_adjustment.validation_strategy_adjusted ? 'Adjusted' : 'Unchanged'} color={result.strategy_adjustment.validation_strategy_adjusted ? '#1565c0' : '#9e9e9e'} />
              </div>
              <div>
                Evaluation Strategy:{' '}
                <Badge label={result.strategy_adjustment.evaluation_strategy_adjusted ? 'Adjusted' : 'Unchanged'} color={result.strategy_adjustment.evaluation_strategy_adjusted ? '#1565c0' : '#9e9e9e'} />
              </div>
              {result.strategy_adjustment.adjustment_reasons && result.strategy_adjustment.adjustment_reasons.length > 0 && (
                <div>
                  Reasons:{' '}
                  {result.strategy_adjustment.adjustment_reasons.map((r, i) => (
                    <Badge key={i} label={r} color="#6a1b9a" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Updated Model Strategy */}
          {result.updated_model_strategy && Object.keys(result.updated_model_strategy).length > 0 && (
            <Section title="Updated Model Strategy">
              {Array.isArray(result.updated_model_strategy.candidate_model_families) && (
                <div>
                  Candidates:{' '}
                  {(result.updated_model_strategy.candidate_model_families as string[]).map((m, i) => (
                    <Badge key={i} label={m} color="#1565c0" />
                  ))}
                </div>
              )}
              {Array.isArray(result.updated_model_strategy.baseline_models) && (
                <div>
                  Baselines:{' '}
                  {(result.updated_model_strategy.baseline_models as string[]).map((m, i) => (
                    <Badge key={i} label={m} color="#6a1b9a" />
                  ))}
                </div>
              )}
              {result.updated_model_strategy.preferred_model_bias != null && (
                <div>Preference: {String(result.updated_model_strategy.preferred_model_bias)}</div>
              )}
            </Section>
          )}

          {/* Updated HPO Strategy */}
          {result.updated_hpo_strategy && Object.keys(result.updated_hpo_strategy).length > 0 && (
            <Section title="Updated HPO Strategy">
              <div>Enabled: {result.updated_hpo_strategy.enabled !== false ? 'Yes' : 'No'}</div>
              {result.updated_hpo_strategy.search_method != null && (
                <div>Method: {String(result.updated_hpo_strategy.search_method)}</div>
              )}
              {result.updated_hpo_strategy.budget_level != null && (
                <div>Budget: {String(result.updated_hpo_strategy.budget_level)}</div>
              )}
              {result.updated_hpo_strategy.max_trials != null && (
                <div>Max Trials: {String(result.updated_hpo_strategy.max_trials)}</div>
              )}
            </Section>
          )}

          {/* Model Search Context Input */}
          {result.model_search_context_input && (
            <Section title="Model Search Context Input (for downstream)">
              <div>
                Ready for Model Search:{' '}
                <span style={{ color: result.model_search_context_input.ready_for_model_search_plan ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.model_search_context_input.ready_for_model_search_plan ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Task Type: {result.model_search_context_input.task_type}</div>
              <div>Primary Metric: {result.model_search_context_input.primary_metric}</div>
              <div>Target Column: {result.model_search_context_input.target_column}</div>
              <div>
                Feature Columns:{' '}
                {result.model_search_context_input.feature_columns && result.model_search_context_input.feature_columns.length > 0
                  ? `${result.model_search_context_input.feature_columns.length} columns`
                  : 'None'}
              </div>
            </Section>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.warningSection}>
              <strong style={{ color: '#e65100' }}>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={styles.warningItem}>⚠ {w}</div>
              ))}
            </div>
          )}

          {/* Errors */}
          {result.errors && result.errors.length > 0 && (
            <div style={styles.errorSection}>
              <strong style={{ color: '#c62828' }}>Errors:</strong>
              {result.errors.map((e, i) => (
                <div key={i} style={styles.errorItem}>{e}</div>
              ))}
            </div>
          )}

          {/* Error Message */}
          {result.error_message && (
            <div style={styles.errorSection}>
              <strong style={{ color: '#c62828' }}>Error Message:</strong>
              <div style={{ marginTop: '4px', fontSize: '12px' }}>{result.error_message}</div>
            </div>
          )}

          {/* Full JSON */}
          <div style={styles.jsonSection}>
            <strong>Full Result (JSON):</strong>
            <pre style={styles.pre}>{JSON.stringify(result, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#f3f4f6',
    border: '1px solid #9e9e9e',
    borderRadius: '8px',
  },
  title: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: 600,
    color: '#333',
  },
  description: {
    margin: '0 0 16px 0',
    fontSize: '14px',
    color: '#666',
  },
  buttonRow: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
  },
  runButton: {
    padding: '10px 20px',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px',
    backgroundColor: '#6c757d',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  errorBox: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '4px',
    color: '#c62828',
    fontSize: '14px',
  },
  resultBox: {
    padding: '16px',
    backgroundColor: '#e8f5e9',
    border: '1px solid #4caf50',
    borderRadius: '4px',
  },
  resultTitle: {
    margin: '0 0 12px 0',
    fontSize: '16px',
    fontWeight: 600,
  },
  fieldRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '24px',
    marginBottom: '12px',
  },
  field: {
    fontSize: '14px',
  },
  section: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#fff',
    borderRadius: '4px',
    border: '1px solid #e0e0e0',
  },
  sectionTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#555',
    textTransform: 'uppercase' as const,
    display: 'block',
    marginBottom: '6px',
  },
  sectionContent: {
    fontSize: '13px',
    color: '#333',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '3px',
  },
  badge: {
    display: 'inline-block',
    color: '#fff',
    padding: '1px 8px',
    borderRadius: '10px',
    fontSize: '11px',
    marginLeft: '4px',
    marginBottom: '2px',
  },
  warningSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#fff3e0',
    borderRadius: '4px',
    border: '1px solid #ffcc02',
    fontSize: '13px',
  },
  warningItem: {
    marginTop: '4px',
    marginLeft: '8px',
    fontSize: '12px',
  },
  errorSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    border: '1px solid #f44336',
    fontSize: '13px',
  },
  errorItem: {
    marginTop: '4px',
    marginLeft: '8px',
    fontSize: '12px',
  },
  jsonSection: {
    marginTop: '16px',
  },
  pre: {
    backgroundColor: '#fff',
    padding: '12px',
    borderRadius: '4px',
    overflow: 'auto',
    fontSize: '12px',
    marginTop: '8px',
    maxHeight: '400px',
  },
};

export default ModelSearchContextPanel;
