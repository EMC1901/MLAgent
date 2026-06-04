import React, { useState } from 'react';
import {
  createPipelineExecution,
  rerunPipelineExecution,
} from '../../../api/pipelineExecutionApi';
import { PipelineExecutionResponse } from '../types';
import { STATUS_COLORS, TRIAL_STATUS_COLORS, ROLE_COLORS, TRIAL_TYPE_COLORS } from '../constants';

interface PipelineExecutionPanelProps {
  taskId: string;
  initialResult?: PipelineExecutionResponse;
}

const PipelineExecutionPanel: React.FC<PipelineExecutionPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineExecutionResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRunTraining = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createPipelineExecution(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to execute pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunPipelineExecution(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run pipeline execution.');
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
        <div style={s.card}>
          <h4 style={s.cardTitle}>Execution Progress</h4>
          <div style={s.grid}>
            <div style={{ ...s.countBox, border: '1px solid #e0e0e0' }}>
              <div style={s.countNumber}>{result.n_pipeline_specs}</div>
              <div style={s.countLabel}>Pipeline Specs</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #e0e0e0' }}>
              <div style={s.countNumber}>{result.n_trials_planned}</div>
              <div style={s.countLabel}>Trials Planned</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #c8e6c9' }}>
              <div style={{ ...s.countNumber, color: '#2e7d32' }}>{result.n_trials_completed}</div>
              <div style={s.countLabel}>Completed</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #ffcdd2' }}>
              <div style={{ ...s.countNumber, color: '#c62828' }}>{result.n_trials_failed}</div>
              <div style={s.countLabel}>Failed</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #bbdefb' }}>
              <div style={{ ...s.countNumber, color: '#1565c0' }}>{result.n_models_trained}</div>
              <div style={s.countLabel}>Models Trained</div>
            </div>
            <div style={{ ...s.countBox, border: '1px solid #e0e0e0' }}>
              <div style={s.countNumber}>{result.duration_seconds.toFixed(1)}s</div>
              <div style={s.countLabel}>Duration</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderPipelineRuns = () => {
    if (!result?.pipeline_run_results || result.pipeline_run_results.length === 0) {
      return <p>No pipeline runs available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Pipeline Runs ({result.pipeline_run_results.length})</h4>
        <table style={{ ...s.table, minWidth: '900px' }}>
          <thead>
            <tr>
              <th style={s.th}>Run ID</th>
              <th style={s.th}>Role</th>
              <th style={s.th}>Model</th>
              <th style={s.th}>Family</th>
              <th style={s.th}>HPO</th>
              <th style={s.th}>Planned</th>
              <th style={s.th}>Completed</th>
              <th style={s.th}>Failed</th>
              <th style={s.th}>Status</th>
              <th style={s.th}>Duration</th>
            </tr>
          </thead>
          <tbody>
            {result.pipeline_run_results.map((pr, i) => (
              <tr key={i}>
                <td style={s.td}><code>{pr.pipeline_run_id}</code></td>
                <td style={s.td}>
                  <Badge label={pr.pipeline_role} color={ROLE_COLORS[pr.pipeline_role] || '#1976d2'} />
                </td>
                <td style={s.td}>{pr.model_id}</td>
                <td style={s.td}>{pr.model_family || '-'}</td>
                <td style={s.td}>
                  <Badge label={pr.hpo_enabled ? 'Yes' : 'No'} color={pr.hpo_enabled ? '#2e7d32' : '#9e9e9e'} />
                </td>
                <td style={s.td}>{pr.n_trials_planned}</td>
                <td style={s.td}><span style={{ color: '#2e7d32' }}>{pr.n_trials_completed}</span></td>
                <td style={s.td}><span style={{ color: '#c62828' }}>{pr.n_trials_failed}</span></td>
                <td style={s.td}>
                  <Badge label={pr.status} color={STATUS_COLORS[pr.status] || '#9e9e9e'} />
                </td>
                <td style={s.td}>{pr.duration_seconds.toFixed(1)}s</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderTrialResults = () => {
    if (!result?.trial_results || result.trial_results.length === 0) {
      return <p>No trial results available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Trial Results ({result.trial_results.length})</h4>
        <table style={{ ...s.table, minWidth: '950px' }}>
          <thead>
            <tr>
              <th style={s.th}>Model</th>
              <th style={s.th}>Type</th>
              <th style={s.th}>Params</th>
              <th style={s.th}>Folds</th>
              <th style={s.th}>Status</th>
              <th style={s.th}>Prediction</th>
              <th style={s.th}>Model Path</th>
              <th style={s.th}>Duration</th>
              <th style={s.th}>Error</th>
            </tr>
          </thead>
          <tbody>
            {result.trial_results.map((t, i) => (
              <tr key={i} style={{ backgroundColor: t.status === 'failed' ? '#ffebee' : 'transparent' }}>
                <td style={s.td}>{t.model_id}</td>
                <td style={s.td}>
                  <Badge label={t.trial_type} color={TRIAL_TYPE_COLORS[t.trial_type] || '#1976d2'} />
                </td>
                <td style={s.td}>
                  <span style={{ fontSize: '11px' }}>
                    {Object.entries(t.params || {}).slice(0, 3).map(([k, v]) => `${k}=${v}`).join(', ') || '-'}
                  </span>
                </td>
                <td style={s.td}>{t.fold_results?.length || 0}</td>
                <td style={s.td}>
                  <Badge label={t.status} color={TRIAL_STATUS_COLORS[t.status] || '#9e9e9e'} />
                </td>
                <td style={s.td}>
                  {(t.prediction_artifact_paths && t.prediction_artifact_paths.length > 0) ? (
                    <span style={{ fontSize: '10px', color: '#2e7d32' }}>Saved ({t.prediction_artifact_paths.length})</span>
                  ) : '-'}
                </td>
                <td style={s.td}>
                  {(t.model_artifact_paths && t.model_artifact_paths.length > 0) ? (
                    <span style={{ fontSize: '10px', color: '#1565c0' }}>Saved ({t.model_artifact_paths.length})</span>
                  ) : '-'}
                </td>
                <td style={s.td}>{t.duration_seconds.toFixed(1)}s</td>
                <td style={s.td}>
                  {t.error_message ? (
                    <span style={{ fontSize: '10px', color: '#c62828' }}>{t.error_message.substring(0, 60)}</span>
                  ) : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
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
    { id: 'runs', label: 'Pipeline Runs' },
    { id: 'trials', label: 'Trial Results' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Pipeline Execution and Training</h3>
      <p style={s.description}>
        Execute model training and HPO trials from the upstream Pipeline Generation output.
        Training is performed by the system Controlled Executor using only registered models.
        No final model ranking is performed — that is handled by Metric Evaluation.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRunTraining} disabled={loading} style={s.runButton}>
          {loading ? 'Training in Progress...' : 'Run Training'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Training'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Pipeline Execution Result</h4>

          {/* Execution Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>Execution ID:</strong> {result.pipeline_execution_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}><strong>Pipeline Generation:</strong> {result.pipeline_generation_id}</div>
            <div style={s.field}>
              <strong>Ready for Metric Eval: </strong>
              <span style={{ color: result.ready_for_metric_evaluation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_metric_evaluation ? 'Yes' : 'No'}
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
            {activeTab === 'runs' && renderPipelineRuns()}
            {activeTab === 'trials' && renderTrialResults()}
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
    padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff',
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
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px', marginBottom: '8px' },
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

export default PipelineExecutionPanel;
