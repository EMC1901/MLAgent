import React, { useState } from 'react';
import {
  createMetricEvaluation,
  rerunMetricEvaluation,
} from '../../../api/metricEvaluationApi';
import { MetricEvaluationResponse } from '../types';
import { STATUS_COLORS, ROLE_COLORS } from '../constants';

interface MetricEvaluationPanelProps {
  taskId: string;
  initialResult?: MetricEvaluationResponse;
}

const MetricEvaluationPanel: React.FC<MetricEvaluationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MetricEvaluationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createMetricEvaluation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to evaluate metrics.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunMetricEvaluation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run metric evaluation.');
    } finally {
      setLoading(false);
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
      <h3 style={s.title}>Metric Evaluation</h3>
      <p style={s.description}>
        Evaluate model metrics from upstream Pipeline Execution results.
        Computes fold-level, trial-level, and model-level metrics, generates
        model rankings, baseline comparisons, and prepares input for Result Diagnosis.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Evaluating...' : 'Run Metric Evaluation'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Evaluation'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Metric Evaluation Result</h4>

          {/* Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>Evaluation ID:</strong> {result.metric_evaluation_id}</div>
            <div style={s.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: STATUS_COLORS[result.status] || '#9e9e9e', fontWeight: 600 }}>
                {result.status}
              </span>
            </div>
            <div style={s.field}><strong>Pipeline Exec:</strong> {result.pipeline_execution_id}</div>
            <div style={s.field}><strong>Task Type:</strong> {result.task_type || 'N/A'}</div>
          </div>

          <div style={s.fieldRow}>
            <div style={s.field}>
              <strong>Primary Metric:</strong>{' '}
              <Badge label={result.primary_metric || 'N/A'} color="#6a1b9a" />
            </div>
            <div style={s.field}><strong>Direction:</strong> {result.metric_direction}</div>
            <div style={s.field}>
              <strong>Ready for Diagnosis:</strong>{' '}
              <span style={{ color: result.ready_for_result_diagnosis ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_result_diagnosis ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Counts */}
          <Section title="Evaluation Counts">
            <div style={s.countRow}>
              <div style={s.countBox}>
                <div style={s.countNumber}>{result.n_trials_evaluated}</div>
                <div style={s.countLabel}>Trials Evaluated</div>
              </div>
              <div style={s.countBox}>
                <div style={{ ...s.countNumber, color: '#c62828' }}>{result.n_trials_failed}</div>
                <div style={s.countLabel}>Trials Failed</div>
              </div>
              <div style={s.countBox}>
                <div style={{ ...s.countNumber, color: '#1565c0' }}>{result.n_models_evaluated}</div>
                <div style={s.countLabel}>Models Evaluated</div>
              </div>
            </div>
          </Section>

          {/* Best Model */}
          <Section title="Best Model Candidate">
            <div style={s.field}><strong>Best Model:</strong> {result.best_model_id || 'N/A'}</div>
            <div style={s.field}><strong>Best Trial:</strong> <code>{result.best_trial_id || 'N/A'}</code></div>
            <div style={s.field}><strong>Best Pipeline Spec:</strong> <code>{result.best_pipeline_spec_id || 'N/A'}</code></div>
            {result.metric_summary && (
              <>
                <div style={s.field}>
                  <strong>Best {result.primary_metric}:</strong>{' '}
                  {result.metric_summary.best_metric_value != null
                    ? result.metric_summary.best_metric_value.toFixed(6)
                    : 'N/A'}
                </div>
                <div style={s.field}>
                  <strong>Mean {result.primary_metric}:</strong>{' '}
                  {result.metric_summary.mean_metric_value != null
                    ? result.metric_summary.mean_metric_value.toFixed(6)
                    : 'N/A'}
                </div>
                <div style={s.field}>
                  <strong>Std:</strong>{' '}
                  {result.metric_summary.std_metric_value != null
                    ? result.metric_summary.std_metric_value.toFixed(6)
                    : 'N/A'}
                </div>
              </>
            )}
          </Section>

          {/* Model Ranking Table */}
          {result.model_ranking && result.model_ranking.length > 0 && (
            <Section title={`Model Ranking (${result.model_ranking.length})`}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Rank</th>
                    <th style={s.th}>Model</th>
                    <th style={s.th}>Family</th>
                    <th style={s.th}>Best Trial</th>
                    <th style={s.th}>{result.primary_metric || 'Metric'} Value</th>
                    <th style={s.th}>vs Baseline</th>
                    <th style={s.th}>Improvement %</th>
                    <th style={s.th}>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {result.model_ranking.map((item, i) => (
                    <tr key={i} style={{
                      backgroundColor: item.rank === 1 ? '#e8f5e9' : 'transparent',
                    }}>
                      <td style={s.td}><strong>#{item.rank}</strong></td>
                      <td style={s.td}>
                        {item.model_id}
                        {item.rank === 1 && <Badge label="BEST" color="#2e7d32" />}
                      </td>
                      <td style={s.td}>{item.model_family || '-'}</td>
                      <td style={s.td}><code style={{ fontSize: '10px' }}>{item.best_trial_id || '-'}</code></td>
                      <td style={s.td}>
                        {item.primary_metric_value != null ? item.primary_metric_value.toFixed(6) : 'N/A'}
                      </td>
                      <td style={s.td}>
                        {item.improvement_over_best_baseline != null
                          ? (item.improvement_over_best_baseline >= 0 ? '+' : '') + item.improvement_over_best_baseline.toFixed(6)
                          : 'N/A'}
                      </td>
                      <td style={s.td}>
                        {item.improvement_percentage != null
                          ? (item.improvement_percentage >= 0 ? '+' : '') + item.improvement_percentage.toFixed(2) + '%'
                          : 'N/A'}
                      </td>
                      <td style={s.td}>
                        <span style={{ fontSize: '11px', color: '#666' }}>{item.ranking_reason}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Trial Metrics Table */}
          {result.trial_metric_results && result.trial_metric_results.length > 0 && (
            <Section title={`Trial Metrics (${result.trial_metric_results.length})`}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Trial ID</th>
                    <th style={s.th}>Model</th>
                    <th style={s.th}>Role</th>
                    <th style={s.th}>Type</th>
                    <th style={s.th}>Folds</th>
                    <th style={s.th}>Mean</th>
                    <th style={s.th}>Std</th>
                    <th style={s.th}>Min</th>
                    <th style={s.th}>Max</th>
                    <th style={s.th}>Rank</th>
                    <th style={s.th}>Best</th>
                    <th style={s.th}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trial_metric_results.map((t, i) => (
                    <tr key={i} style={{
                      backgroundColor: t.is_best_trial ? '#e8f5e9' : t.status === 'failed' ? '#ffebee' : 'transparent',
                    }}>
                      <td style={s.td}><code style={{ fontSize: '10px' }}>{t.trial_id}</code></td>
                      <td style={s.td}>{t.model_id}</td>
                      <td style={s.td}>
                        <Badge label={t.pipeline_role || '-'} color={ROLE_COLORS[t.pipeline_role || ''] || '#9e9e9e'} />
                      </td>
                      <td style={s.td}><span style={{ fontSize: '11px' }}>{t.trial_type || '-'}</span></td>
                      <td style={s.td}>{t.n_folds}</td>
                      <td style={s.td}>
                        {t.primary_metric_mean != null ? t.primary_metric_mean.toFixed(6) : 'N/A'}
                      </td>
                      <td style={s.td}>
                        {t.primary_metric_std != null ? t.primary_metric_std.toFixed(6) : 'N/A'}
                      </td>
                      <td style={s.td}>
                        {t.primary_metric_min != null ? t.primary_metric_min.toFixed(6) : 'N/A'}
                      </td>
                      <td style={s.td}>
                        {t.primary_metric_max != null ? t.primary_metric_max.toFixed(6) : 'N/A'}
                      </td>
                      <td style={s.td}>{t.rank != null ? `#${t.rank}` : '-'}</td>
                      <td style={s.td}>
                        {t.is_best_trial && <Badge label="BEST" color="#2e7d32" />}
                      </td>
                      <td style={s.td}>
                        <Badge label={t.status} color={t.status === 'evaluated' ? '#2e7d32' : '#c62828'} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Fold Metrics Table (condensed) */}
          {result.fold_metric_results && result.fold_metric_results.length > 0 && (
            <Section title={`Fold Metrics (${result.fold_metric_results.length})`}>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                <table style={s.table}>
                  <thead>
                    <tr>
                      <th style={s.th}>Trial</th>
                      <th style={s.th}>Model</th>
                      <th style={s.th}>Fold</th>
                      <th style={s.th}>Samples</th>
                      <th style={s.th}>{result.primary_metric || 'Metric'}</th>
                      <th style={s.th}>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.fold_metric_results.map((f, i) => (
                      <tr key={i} style={{
                        backgroundColor: f.status === 'failed' ? '#ffebee' : 'transparent',
                      }}>
                        <td style={s.td}><code style={{ fontSize: '10px' }}>{f.trial_id.substring(0, 12)}...</code></td>
                        <td style={s.td}>{f.model_id}</td>
                        <td style={s.td}>Fold {f.fold_index}</td>
                        <td style={s.td}>{f.n_samples}</td>
                        <td style={s.td}>
                          {f.primary_metric_value != null ? f.primary_metric_value.toFixed(6) : 'N/A'}
                        </td>
                        <td style={s.td}>
                          <Badge label={f.status} color={f.status === 'evaluated' ? '#2e7d32' : '#c62828'} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          )}

          {/* Baseline Comparison */}
          {result.baseline_comparison && (
            <Section title="Baseline Comparison">
              {result.baseline_comparison.baseline_available ? (
                <>
                  <div style={s.field}>
                    <strong>Best Baseline:</strong> {result.baseline_comparison.best_baseline_model_id || 'N/A'}
                    {' ('}{result.baseline_comparison.best_baseline_metric_value != null
                      ? result.baseline_comparison.best_baseline_metric_value.toFixed(6)
                      : 'N/A'}{')'}
                  </div>
                  <div style={s.field}>
                    <strong>Best Candidate:</strong> {result.baseline_comparison.best_candidate_model_id || 'N/A'}
                    {' ('}{result.baseline_comparison.best_candidate_metric_value != null
                      ? result.baseline_comparison.best_candidate_metric_value.toFixed(6)
                      : 'N/A'}{')'}
                  </div>
                  <div style={s.field}>
                    <strong>Absolute Improvement:</strong>{' '}
                    <span style={{
                      color: result.baseline_comparison.candidate_beats_baseline ? '#2e7d32' : '#c62828',
                      fontWeight: 600,
                    }}>
                      {result.baseline_comparison.absolute_improvement != null
                        ? result.baseline_comparison.absolute_improvement.toFixed(6)
                        : 'N/A'}
                    </span>
                  </div>
                  <div style={s.field}>
                    <strong>Relative Improvement:</strong>{' '}
                    {result.baseline_comparison.relative_improvement_percentage != null
                      ? result.baseline_comparison.relative_improvement_percentage.toFixed(2) + '%'
                      : 'N/A'}
                  </div>
                  <div style={s.field}>
                    <strong>Candidate Beats Baseline:</strong>{' '}
                    <span style={{
                      color: result.baseline_comparison.candidate_beats_baseline ? '#2e7d32' : '#c62828',
                      fontWeight: 600,
                    }}>
                      {result.baseline_comparison.candidate_beats_baseline ? 'Yes' : 'No'}
                    </span>
                  </div>
                  {result.baseline_comparison.comparison_notes.length > 0 && (
                    <div style={{ marginTop: '8px' }}>
                      {result.baseline_comparison.comparison_notes.map((note, i) => (
                        <div key={i} style={{ fontSize: '12px', color: '#555', marginTop: '2px' }}>
                          {note}
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <div style={{ color: '#888' }}>No baseline available for comparison.</div>
              )}
            </Section>
          )}

          {/* Metric Validation */}
          {result.metric_validation_result && (
            <Section title="Metric Validation">
              <div style={s.field}>
                <strong>Overall Valid:</strong>{' '}
                <span style={{
                  color: result.metric_validation_result.is_valid ? '#2e7d32' : '#c62828',
                  fontWeight: 600,
                }}>
                  {result.metric_validation_result.is_valid ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={s.checkGrid}>
                <div>All Metrics Finite: <span style={{ color: result.metric_validation_result.all_metrics_finite ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.all_metrics_finite ? 'OK' : 'FAIL'}</span></div>
                <div>Primary Metric Present: <span style={{ color: result.metric_validation_result.primary_metric_present ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.primary_metric_present ? 'OK' : 'FAIL'}</span></div>
                <div>Ranking Consistent: <span style={{ color: result.metric_validation_result.ranking_consistent ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.ranking_consistent ? 'OK' : 'FAIL'}</span></div>
                <div>Best Trial in Results: <span style={{ color: result.metric_validation_result.best_trial_in_results ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.best_trial_in_results ? 'OK' : 'FAIL'}</span></div>
                <div>Baseline Refs Valid: <span style={{ color: result.metric_validation_result.baseline_references_valid ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.baseline_references_valid ? 'OK' : 'FAIL'}</span></div>
                <div>Diagnosis Input Complete: <span style={{ color: result.metric_validation_result.diagnosis_input_complete ? '#2e7d32' : '#c62828' }}>{result.metric_validation_result.diagnosis_input_complete ? 'OK' : 'FAIL'}</span></div>
              </div>
              {result.metric_validation_result.issues.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <strong style={{ color: '#c62828' }}>Issues:</strong>
                  {result.metric_validation_result.issues.map((issue, i) => (
                    <div key={i} style={{ fontSize: '12px', color: '#c62828', marginTop: '2px' }}>
                      - {issue}
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Evaluation Artifact Manifest */}
          {result.evaluation_artifact_manifest && (
            <Section title="Evaluation Artifacts">
              <div>Artifact Dir: <code style={{ fontSize: '11px' }}>{result.evaluation_artifact_manifest.artifact_dir}</code></div>
              {result.evaluation_artifact_manifest.manifest_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Manifest: {result.evaluation_artifact_manifest.manifest_path}</div>
              )}
              {result.evaluation_artifact_manifest.metric_results_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Metric Results: {result.evaluation_artifact_manifest.metric_results_path}</div>
              )}
              {result.evaluation_artifact_manifest.fold_metrics_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Fold Metrics: {result.evaluation_artifact_manifest.fold_metrics_path}</div>
              )}
              {result.evaluation_artifact_manifest.trial_metrics_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Trial Metrics: {result.evaluation_artifact_manifest.trial_metrics_path}</div>
              )}
              {result.evaluation_artifact_manifest.model_ranking_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Model Ranking: {result.evaluation_artifact_manifest.model_ranking_path}</div>
              )}
              {result.evaluation_artifact_manifest.baseline_comparison_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Baseline Comparison: {result.evaluation_artifact_manifest.baseline_comparison_path}</div>
              )}
              {result.evaluation_artifact_manifest.result_diagnosis_input_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Diagnosis Input: {result.evaluation_artifact_manifest.result_diagnosis_input_path}</div>
              )}
            </Section>
          )}

          {/* Result Diagnosis Input Preview */}
          {result.result_diagnosis_input && (
            <Section title="Result Diagnosis Input">
              <div style={s.field}>
                <strong>Ready for Diagnosis:</strong>{' '}
                <span style={{
                  color: result.result_diagnosis_input.ready_for_result_diagnosis ? '#2e7d32' : '#c62828',
                  fontWeight: 600,
                }}>
                  {result.result_diagnosis_input.ready_for_result_diagnosis ? 'Yes' : 'No'}
                </span>
              </div>
              {result.result_diagnosis_input.best_trial && (
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Best Trial: {String(result.result_diagnosis_input.best_trial['trial_id'] || 'N/A')}
                  {' - '}{String(result.result_diagnosis_input.best_trial['model_id'] || 'N/A')}
                </div>
              )}
              <div style={{ fontSize: '12px', color: '#666' }}>
                Failed Trials: {String(
                  (result.result_diagnosis_input.failed_trials_summary as any)?.n_failed_trials ?? '0'
                )}
              </div>
            </Section>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningSection}>
              <strong style={{ color: '#e65100' }}>Warnings ({result.warnings.length}):</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={s.warningItem}>{w}</div>
              ))}
            </div>
          )}

          {/* Error */}
          {result.error_message && (
            <div style={s.errorSection}>
              <strong style={{ color: '#c62828' }}>Error:</strong>
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
    backgroundColor: '#f5f0ff',
    border: '1px solid #7b1fa2',
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
    backgroundColor: '#7b1fa2',
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
  countRow: {
    display: 'flex',
    gap: '16px',
    flexWrap: 'wrap',
  },
  countBox: {
    textAlign: 'center',
    padding: '8px 16px',
    backgroundColor: '#f5f5f5',
    borderRadius: '8px',
    minWidth: '80px',
  },
  countNumber: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#333',
  },
  countLabel: {
    fontSize: '11px',
    color: '#888',
    textTransform: 'uppercase',
  },
  checkGrid: {
    marginTop: '8px',
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '4px',
    fontSize: '12px',
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
    overflowX: 'auto',
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
  errorSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    border: '1px solid #f44336',
    fontSize: '13px',
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

export default MetricEvaluationPanel;
