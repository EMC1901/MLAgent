import React, { useState } from 'react';
import {
  createMetricEvaluation,
  rerunMetricEvaluation,
} from '../../../api/metricEvaluationApi';
import { MetricEvaluationResponse } from '../types';
import { STATUS_COLORS, STATUS_LABELS, DIRECTION_LABELS, ROLE_COLORS } from '../constants';

interface MetricEvaluationPanelProps {
  taskId: string;
  initialResult?: MetricEvaluationResponse;
}

const MetricEvaluationPanel: React.FC<MetricEvaluationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MetricEvaluationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

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

  // --- Render helpers ---

  const renderSummary = () => {
    if (!result) return null;
    return (
      <div>
        {/* Counts */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Evaluation Counts</h4>
          <div style={s.grid}>
            <div style={{ ...s.countBox, border: '1px solid #e0e0e0' }}>
              <div style={s.countNumber}>{result.n_trials_evaluated}</div>
              <div style={s.countLabel}>Trials Evaluated</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #ffcdd2' }}>
              <div style={{ ...s.countNumber, color: '#c62828' }}>{result.n_trials_failed}</div>
              <div style={s.countLabel}>Trials Failed</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #bbdefb' }}>
              <div style={{ ...s.countNumber, color: '#1565c0' }}>{result.n_models_evaluated}</div>
              <div style={s.countLabel}>Models Evaluated</div>
            </div>
          </div>
        </div>

        {/* Best Model */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Best Model Candidate</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Best Model:</strong> <span>{result.best_model_id || 'N/A'}</span></div>
            <div style={s.field}><strong>Best Trial:</strong> <code>{result.best_trial_id || 'N/A'}</code></div>
            <div style={s.field}><strong>Best Pipeline Spec:</strong> <code>{result.best_pipeline_spec_id || 'N/A'}</code></div>
          </div>
          {result.metric_summary && (
            <div style={s.subCard}>
              <strong>Metric Summary</strong>
              <div style={{ ...s.grid, marginTop: '8px', marginBottom: 0 }}>
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
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderModelRanking = () => {
    if (!result?.model_ranking || result.model_ranking.length === 0) {
      return <p>No model ranking data available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Model Ranking ({result.model_ranking.length})</h4>
        <table style={{ ...s.table, tableLayout: 'auto', minWidth: '900px' }}>
          <colgroup>
            <col style={{ width: '50px' }} />
            <col style={{ width: '130px' }} />
            <col style={{ width: '90px' }} />
            <col style={{ width: '110px' }} />
            <col style={{ width: '110px' }} />
            <col style={{ width: '100px' }} />
            <col style={{ width: '110px' }} />
            <col />
          </colgroup>
          <thead>
            <tr>
              <th style={s.th}>Rank</th>
              <th style={s.th}>Model</th>
              <th style={s.th}>Family</th>
              <th style={s.th}>Best Trial</th>
              <th style={s.th}>{result.primary_metric || 'Metric'}</th>
              <th style={s.th}>vs Baseline</th>
              <th style={s.th}>Improve %</th>
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
      </div>
    );
  };

  const renderTrialMetrics = () => {
    if (!result?.trial_metric_results || result.trial_metric_results.length === 0) {
      return <p>No trial metrics available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Trial Metrics ({result.trial_metric_results.length})</h4>
        <table style={{ ...s.table, minWidth: '950px' }}>
          <thead>
            <tr>
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
      </div>
    );
  };

  const renderFoldMetrics = () => {
    if (!result?.fold_metric_results || result.fold_metric_results.length === 0) {
      return <p>No fold metrics available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Fold Metrics ({result.fold_metric_results.length})</h4>
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
    );
  };

  const renderBaseline = () => {
    if (!result?.baseline_comparison) {
      return <p>No baseline comparison available.</p>;
    }
    const bc = result.baseline_comparison;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Baseline Comparison</h4>
        {bc.baseline_available ? (
          <>
            <div style={s.grid}>
              <div style={s.field}>
                <strong>Best Baseline:</strong> {bc.best_baseline_model_id || 'N/A'}
                {' ('}{bc.best_baseline_metric_value != null
                  ? bc.best_baseline_metric_value.toFixed(6)
                  : 'N/A'}{')'}
              </div>
              <div style={s.field}>
                <strong>Best Candidate:</strong> {bc.best_candidate_model_id || 'N/A'}
                {' ('}{bc.best_candidate_metric_value != null
                  ? bc.best_candidate_metric_value.toFixed(6)
                  : 'N/A'}{')'}
              </div>
              <div style={s.field}>
                <strong>Absolute Improvement:</strong>{' '}
                <span style={{
                  color: bc.candidate_beats_baseline ? '#2e7d32' : '#c62828',
                  fontWeight: 600,
                }}>
                  {bc.absolute_improvement != null
                    ? bc.absolute_improvement.toFixed(6)
                    : 'N/A'}
                </span>
              </div>
              <div style={s.field}>
                <strong>Relative Improvement:</strong>{' '}
                {bc.relative_improvement_percentage != null
                  ? bc.relative_improvement_percentage.toFixed(2) + '%'
                  : 'N/A'}
              </div>
              <div style={s.field}>
                <strong>Candidate Beats Baseline:</strong>{' '}
                <span style={{
                  color: bc.candidate_beats_baseline ? '#2e7d32' : '#c62828',
                  fontWeight: 600,
                }}>
                  {bc.candidate_beats_baseline ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
            {bc.comparison_notes && bc.comparison_notes.length > 0 && (
              <div style={s.subCard}>
                <strong>Comparison Notes:</strong>
                <ul style={s.list}>
                  {bc.comparison_notes.map((note, i) => (
                    <li key={i}>{note}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        ) : (
          <p style={{ color: '#999', fontSize: '13px' }}>No baseline available for comparison.</p>
        )}
      </div>
    );
  };

  const renderTab = (tabId: string, label: string) => (
    <button
      key={tabId}
      onClick={() => setActiveTab(tabId)}
      style={{
        ...s.tabButton,
        backgroundColor: activeTab === tabId ? '#1976d2' : '#e0e0e0',
        color: activeTab === tabId ? '#fff' : '#333',
      }}
    >
      {label}
    </button>
  );

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'ranking', label: 'Model Ranking' },
    { id: 'trials', label: 'Trial Metrics' },
    { id: 'folds', label: 'Fold Metrics' },
    { id: 'baseline', label: 'Baseline' },
    { id: 'json', label: 'Full JSON' },
  ];

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
              <strong>Status: </strong>
              <Badge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}><strong>Pipeline Exec:</strong> {result.pipeline_execution_id}</div>
            <div style={s.field}><strong>Task Type:</strong> {result.task_type || 'N/A'}</div>
            <div style={s.field}>
              <strong>Primary Metric: </strong>
              <Badge label={result.primary_metric || 'N/A'} color="#6a1b9a" />
            </div>
            <div style={s.field}>
              <strong>Direction: </strong>
              <span>{DIRECTION_LABELS[result.metric_direction] || result.metric_direction}</span>
            </div>
            <div style={s.field}>
              <strong>Ready for Diagnosis: </strong>
              <span style={{ color: result.ready_for_result_diagnosis ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_result_diagnosis ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningBox}>
              <strong>Warnings:</strong>
              <ul style={s.list}>
                {result.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          {result.error_message && (
            <div style={s.errorBox}>
              <strong>Error:</strong> {result.error_message}
            </div>
          )}

          {/* Tab navigation */}
          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          {/* Tab content */}
          <div style={s.tabContent}>
            {activeTab === 'summary' && renderSummary()}
            {activeTab === 'ranking' && renderModelRanking()}
            {activeTab === 'trials' && renderTrialMetrics()}
            {activeTab === 'folds' && renderFoldMetrics()}
            {activeTab === 'baseline' && renderBaseline()}
            {activeTab === 'json' && (
              <div style={s.card}>
                <h4 style={s.cardTitle}>Full JSON</h4>
                <pre style={s.json}>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '24px',
    padding: '16px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
  },
  title: { margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600 },
  description: { margin: '0 0 16px 0', color: '#666', fontSize: '13px', lineHeight: 1.5 },
  buttonRow: { display: 'flex', gap: '8px', marginBottom: '16px' },
  runButton: {
    padding: '10px 20px', backgroundColor: '#7b1fa2', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px', backgroundColor: '#f57c00', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  errorBox: {
    padding: '12px', backgroundColor: '#ffebee', border: '1px solid #f44336',
    borderRadius: '4px', color: '#c62828', marginBottom: '16px',
  },
  resultBox: {
    padding: '16px', backgroundColor: '#fff', border: '1px solid #e0e0e0',
    borderRadius: '8px',
  },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  fieldRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  badge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '12px',
    color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px',
  },
  warningBox: {
    padding: '12px', backgroundColor: '#fff3e0', border: '1px solid #ff9800',
    borderRadius: '4px', color: '#e65100', marginBottom: '16px',
  },
  list: { margin: '4px 0', paddingLeft: '20px' },
  tabBar: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' },
  tabButton: {
    padding: '6px 14px', border: 'none', borderRadius: '16px',
    fontSize: '13px', fontWeight: 600, cursor: 'pointer',
  },
  tabContent: { minHeight: '200px', maxHeight: '60vh', overflowY: 'auto' as const },
  card: {
    padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px',
    marginBottom: '12px', border: '1px solid #e0e0e0',
    overflowX: 'auto' as const,
  },
  subCard: {
    padding: '10px', backgroundColor: '#fff', borderRadius: '4px',
    marginBottom: '8px', border: '1px solid #eee',
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  summaryText: { marginTop: '8px', color: '#333', fontSize: '14px', lineHeight: 1.5 },
  table: {
    width: '100%', borderCollapse: 'collapse' as const, fontSize: '13px',
    tableLayout: 'fixed' as const, minWidth: '700px',
  },
  th: {
    textAlign: 'left' as const, padding: '6px 8px', borderBottom: '2px solid #e0e0e0',
    fontWeight: 600, backgroundColor: '#fafafa', whiteSpace: 'nowrap' as const,
  },
  td: {
    padding: '6px 8px', borderBottom: '1px solid #eee',
    verticalAlign: 'top' as const, wordBreak: 'break-word' as const,
  },
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
  },
  countBox: {
    textAlign: 'center' as const,
    padding: '12px',
    backgroundColor: '#fff',
    borderRadius: '8px',
  },
  countNumber: {
    fontSize: '24px',
    fontWeight: 700,
    color: '#333',
  },
  countLabel: {
    fontSize: '11px',
    color: '#888',
    textTransform: 'uppercase' as const,
    marginTop: '2px',
  },
};

export default MetricEvaluationPanel;
