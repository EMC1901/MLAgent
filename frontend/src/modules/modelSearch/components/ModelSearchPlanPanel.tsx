import React, { useState } from 'react';
import {
  createModelSearchPlan,
  rerunModelSearchPlan,
} from '../../../api/modelSearchApi';
import { ModelSearchPlanResponse } from '../types';
import { PRIORITY_COLORS, BUDGET_COLORS } from '../constants';

interface ModelSearchPlanPanelProps {
  taskId: string;
  initialResult?: ModelSearchPlanResponse;
}

const ModelSearchPlanPanel: React.FC<ModelSearchPlanPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ModelSearchPlanResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createModelSearchPlan(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to create model search plan.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunModelSearchPlan(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run model search plan.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return '#4caf50';
      case 'planned_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      case 'blocked': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={s.section}>
      <strong style={s.sectionTitle}>{title}</strong>
      <div style={s.sectionContent}>{children}</div>
    </div>
  );

  return (
    <div style={s.container}>
      <h3 style={s.title}>Automated Model and HPO Search</h3>
      <p style={s.description}>
        Generate a structured Model Search Plan using LLM-guided strategy analysis,
        Model Registry validation, and HPO budget planning. This plan will be consumed
        by the downstream Executable Pipeline Generation module.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Generating Plan...' : 'Generate Model Search Plan'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Generating...' : 'Re-run Plan'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Model Search Plan Result</h4>

          <div style={s.fieldRow}>
            <div style={s.field}><strong>Plan ID:</strong> {result.model_search_plan_id}</div>
            <div style={s.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={s.field}><strong>Planning Mode:</strong> {result.planning_mode}</div>
          </div>

          {/* Dataset Context */}
          {result.dataset_context && (
            <Section title="Dataset Context">
              <div>Task Type: <Badge label={result.dataset_context.task_type || 'N/A'} color="#1565c0" /></div>
              <div>Primary Metric: <Badge label={result.dataset_context.primary_metric || 'N/A'} color="#6a1b9a" /></div>
              <div>Samples: {result.dataset_context.n_samples}</div>
              <div>Features: {result.dataset_context.n_features}</div>
              <div>Target Column: {result.dataset_context.target_column}</div>
            </Section>
          )}

          {/* Candidate Model Plan */}
          {result.candidate_model_plan && (
            <Section title="Candidate Model Plan">
              {/* Baseline Models */}
              {result.candidate_model_plan.baseline_models.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                  <strong>Baseline Models:</strong>
                  {result.candidate_model_plan.baseline_models.map((b, i) => (
                    <Badge
                      key={i}
                      label={`${b.model_id} (${b.role}${b.hpo_enabled ? ', HPO' : ''})`}
                      color="#6a1b9a"
                    />
                  ))}
                </div>
              )}

              {/* Candidate Models */}
              {result.candidate_model_plan.candidate_models.length > 0 && (
                <div style={{ marginBottom: '8px' }}>
                  <strong>Candidate Models:</strong>
                  <table style={s.table}>
                    <thead>
                      <tr>
                        <th style={s.th}>Model</th>
                        <th style={s.th}>Family</th>
                        <th style={s.th}>Priority</th>
                        <th style={s.th}>HPO</th>
                        <th style={s.th}>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.candidate_model_plan.candidate_models.map((c, i) => (
                        <tr key={i}>
                          <td style={s.td}>{c.model_id}</td>
                          <td style={s.td}>{c.model_family}</td>
                          <td style={s.td}>
                            <Badge label={c.priority} color={PRIORITY_COLORS[c.priority] || '#1976d2'} />
                          </td>
                          <td style={s.td}>
                            {c.hpo_enabled
                              ? <Badge label="Yes" color="#2e7d32" />
                              : <Badge label="No" color="#9e9e9e" />}
                          </td>
                          <td style={s.td}>{c.reason || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Excluded Models */}
              {result.candidate_model_plan.excluded_models.length > 0 && (
                <div>
                  <strong style={{ color: '#c62828' }}>Excluded Models:</strong>
                  {result.candidate_model_plan.excluded_models.map((e, i) => (
                    <div key={i} style={{ marginLeft: '16px', fontSize: '12px', color: '#c62828' }}>
                      {e.model_id} — {e.reason || 'No reason given'}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* HPO Plan */}
          {result.hpo_plan && (
            <Section title="HPO Plan">
              <div>
                HPO Enabled:{' '}
                <Badge label={result.hpo_plan.enabled ? 'Yes' : 'No'} color={result.hpo_plan.enabled ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div>Search Method: <Badge label={result.hpo_plan.search_method || 'N/A'} color="#1565c0" /></div>
              <div>
                Budget Level:{' '}
                <Badge label={result.hpo_plan.budget_level} color={BUDGET_COLORS[result.hpo_plan.budget_level] || '#1976d2'} />
              </div>
              <div>Max Total Trials: <strong>{result.hpo_plan.max_total_trials}</strong></div>
              <div>Max Parallel Trials: {result.hpo_plan.max_parallel_trials}</div>
              <div>
                Early Stopping:{' '}
                <Badge label={result.hpo_plan.early_stopping ? 'Yes' : 'No'} color={result.hpo_plan.early_stopping ? '#ff9800' : '#9e9e9e'} />
              </div>
              {result.hpo_plan.fallback_method && (
                <div>Fallback Method: {result.hpo_plan.fallback_method}</div>
              )}

              {/* Trial Allocation */}
              {result.hpo_plan.trial_allocation.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <strong>Trial Allocation:</strong>
                  <table style={s.table}>
                    <thead>
                      <tr>
                        <th style={s.th}>Model</th>
                        <th style={s.th}>Max Trials</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.hpo_plan.trial_allocation.map((t, i) => (
                        <tr key={i}>
                          <td style={s.td}>{t.model_id}</td>
                          <td style={s.td}>
                            <Badge
                              label={String(t.max_trials)}
                              color={t.max_trials === 0 ? '#9e9e9e' : '#1565c0'}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Section>
          )}

          {/* Search Space Plan */}
          {result.search_space_plan && result.search_space_plan.spaces.length > 0 && (
            <Section title="Search Space Plan">
              {result.search_space_plan.spaces.map((sp, i) => (
                <div key={i} style={{ marginBottom: '8px' }}>
                  <strong>{sp.model_id}</strong> <span style={{ fontSize: '11px', color: '#888' }}>({sp.search_space_id})</span>
                  {sp.parameters.length > 0 ? (
                    <table style={{ ...s.table, marginTop: '4px' }}>
                      <thead>
                        <tr>
                          <th style={s.th}>Parameter</th>
                          <th style={s.th}>Type</th>
                          <th style={s.th}>Range</th>
                          <th style={s.th}>Sampling</th>
                          <th style={s.th}>Default</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sp.parameters.map((p, j) => (
                          <tr key={j}>
                            <td style={s.td}>{p.name}</td>
                            <td style={s.td}>{p.param_type}</td>
                            <td style={s.td}>
                              {p.choices.length > 0
                                ? p.choices.join(', ')
                                : `[${p.low ?? '?'}, ${p.high ?? '?'}]`}
                            </td>
                            <td style={s.td}>{p.sampling}</td>
                            <td style={s.td}>{p.default_value || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ fontSize: '12px', color: '#888', marginLeft: '16px' }}>No HPO parameters (no HPO needed)</div>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Validation Plan */}
          {result.validation_plan && (
            <Section title="Validation Plan">
              <div>Split Strategy: <Badge label={result.validation_plan.split_strategy} color="#1565c0" /></div>
              <div>Splits: {result.validation_plan.n_splits}</div>
              <div>Random State: {result.validation_plan.random_state}</div>
              <div>Shuffle: <Badge label={result.validation_plan.shuffle ? 'Yes' : 'No'} color={result.validation_plan.shuffle ? '#2e7d32' : '#9e9e9e'} /></div>
              <div>Stratification Required: <Badge label={result.validation_plan.stratification_required ? 'Yes' : 'No'} color={result.validation_plan.stratification_required ? '#ff9800' : '#9e9e9e'} /></div>
            </Section>
          )}

          {/* Evaluation Plan */}
          {result.evaluation_plan && (
            <Section title="Evaluation Plan">
              <div>Primary Metric: <Badge label={result.evaluation_plan.primary_metric || 'N/A'} color="#6a1b9a" /></div>
              <div>Direction: <Badge label={result.evaluation_plan.metric_direction} color="#1565c0" /></div>
              {result.evaluation_plan.secondary_metrics.length > 0 && (
                <div>
                  Secondary Metrics:{' '}
                  {result.evaluation_plan.secondary_metrics.map((m, i) => (
                    <Badge key={i} label={m} color="#00897b" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* LLM Model Search Advice */}
          {result.llm_model_search_advice && (
            <Section title="LLM Model Search Advice">
              <div>
                LLM Used:{' '}
                <Badge label={result.llm_model_search_advice.used ? 'Yes' : 'No'} color={result.llm_model_search_advice.used ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div>
                Confidence:{' '}
                <Badge
                  label={`${Math.round((result.llm_model_search_advice.confidence_score || 0) * 100)}%`}
                  color={(result.llm_model_search_advice.confidence_score || 0) >= 0.7 ? '#2e7d32' : '#ff9800'}
                />
              </div>
              <div style={{ fontSize: '13px', marginTop: '4px', fontStyle: 'italic' }}>
                {result.llm_model_search_advice.summary}
              </div>
            </Section>
          )}

          {/* System Validation Result */}
          {result.system_validation_result && (
            <Section title="System Validation Result">
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
              {result.system_validation_result.rejected_models.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#c62828' }}>Rejected Models:</strong>
                  {result.system_validation_result.rejected_models.map((r, i) => (
                    <div key={i} style={{ marginLeft: '16px', fontSize: '12px', color: '#c62828' }}>{r}</div>
                  ))}
                </div>
              )}
              {result.system_validation_result.rejected_hpo_methods.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#c62828' }}>Rejected HPO Methods:</strong>
                  {result.system_validation_result.rejected_hpo_methods.map((r, i) => (
                    <div key={i} style={{ marginLeft: '16px', fontSize: '12px', color: '#c62828' }}>{r}</div>
                  ))}
                </div>
              )}
              {result.system_validation_result.warnings.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#e65100' }}>Validation Warnings:</strong>
                  {result.system_validation_result.warnings.map((w, i) => (
                    <div key={i} style={{ marginLeft: '16px', fontSize: '12px', color: '#e65100' }}>{w}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Pipeline Generation Input Summary */}
          {result.pipeline_generation_input && (
            <Section title="Pipeline Generation Input">
              <div>
                Ready for Pipeline Generation:{' '}
                <span style={{ color: result.pipeline_generation_input.ready_for_pipeline_generation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.pipeline_generation_input.ready_for_pipeline_generation ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Target Column: {result.pipeline_generation_input.target_column}</div>
              <div>Feature Columns: {result.pipeline_generation_input.feature_columns.length} columns</div>
            </Section>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningSection}>
              <strong style={{ color: '#e65100' }}>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={s.warningItem}>{w}</div>
              ))}
            </div>
          )}

          {/* Errors */}
          {result.errors && result.errors.length > 0 && (
            <div style={s.errorSection2}>
              <strong style={{ color: '#c62828' }}>Errors:</strong>
              {result.errors.map((e, i) => (
                <div key={i} style={s.errorItem}>{e}</div>
              ))}
            </div>
          )}

          {/* Error Message */}
          {result.error_message && (
            <div style={s.errorSection2}>
              <strong style={{ color: '#c62828' }}>Error Message:</strong>
              <div style={{ marginTop: '4px', fontSize: '12px' }}>{result.error_message}</div>
            </div>
          )}

          {/* Full JSON */}
          <details style={s.jsonSection}>
            <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '13px', marginBottom: '8px' }}>
              Full Result (JSON)
            </summary>
            <pre style={s.pre}>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
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
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '4px',
    fontSize: '12px',
  },
  th: {
    textAlign: 'left' as const,
    padding: '4px 8px',
    borderBottom: '2px solid #e0e0e0',
    fontWeight: 600,
    color: '#555',
  },
  td: {
    padding: '3px 8px',
    borderBottom: '1px solid #f0f0f0',
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
  errorSection2: {
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

export default ModelSearchPlanPanel;
