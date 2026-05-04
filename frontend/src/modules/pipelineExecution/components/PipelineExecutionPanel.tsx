import React, { useState } from 'react';
import {
  createPipelineExecution,
  rerunPipelineExecution,
} from '../../../api/pipelineExecutionApi';
import { PipelineExecutionResponse } from '../types';
import { STATUS_COLORS, TRIAL_STATUS_COLORS, ROLE_COLORS, TRIAL_TYPE_COLORS } from '../constants';

interface PipelineExecutionPanelProps {
  taskId: string;
}

const PipelineExecutionPanel: React.FC<PipelineExecutionPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineExecutionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

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

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={s.section}>
      <strong style={s.sectionTitle}>{title}</strong>
      <div style={s.sectionContent}>{children}</div>
    </div>
  );

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
              <strong>Status:</strong>{' '}
              <span style={{ color: STATUS_COLORS[result.status] || '#9e9e9e', fontWeight: 600 }}>
                {result.status}
              </span>
            </div>
            <div style={s.field}><strong>Pipeline Generation:</strong> {result.pipeline_generation_id}</div>
            <div style={s.field}>
              <strong>Ready for Metric Eval:</strong>{' '}
              <span style={{ color: result.ready_for_metric_evaluation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_metric_evaluation ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {/* Counts */}
          <Section title="Execution Progress">
            <div style={s.countRow}>
              <div style={s.countBox}>
                <div style={s.countNumber}>{result.n_pipeline_specs}</div>
                <div style={s.countLabel}>Pipeline Specs</div>
              </div>
              <div style={s.countBox}>
                <div style={s.countNumber}>{result.n_trials_planned}</div>
                <div style={s.countLabel}>Trials Planned</div>
              </div>
              <div style={s.countBox}>
                <div style={{ ...s.countNumber, color: '#2e7d32' }}>{result.n_trials_completed}</div>
                <div style={s.countLabel}>Completed</div>
              </div>
              <div style={s.countBox}>
                <div style={{ ...s.countNumber, color: '#c62828' }}>{result.n_trials_failed}</div>
                <div style={s.countLabel}>Failed</div>
              </div>
              <div style={s.countBox}>
                <div style={{ ...s.countNumber, color: '#1565c0' }}>{result.n_models_trained}</div>
                <div style={s.countLabel}>Models Trained</div>
              </div>
              <div style={s.countBox}>
                <div style={s.countNumber}>{result.duration_seconds.toFixed(1)}s</div>
                <div style={s.countLabel}>Duration</div>
              </div>
            </div>
          </Section>

          {/* Pipeline Run Results Table */}
          {result.pipeline_run_results && result.pipeline_run_results.length > 0 && (
            <Section title={`Pipeline Runs (${result.pipeline_run_results.length})`}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Run ID</th>
                    <th style={s.th}>Role</th>
                    <th style={s.th}>Model</th>
                    <th style={s.th}>Family</th>
                    <th style={s.th}>HPO</th>
                    <th style={s.th}>Trials Planned</th>
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
            </Section>
          )}

          {/* Trial Results Table */}
          {result.trial_results && result.trial_results.length > 0 && (
            <Section title={`Trial Results (${result.trial_results.length})`}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Trial ID</th>
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
                      <td style={s.td}><code>{t.trial_id}</code></td>
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
                        {t.prediction_artifact_path ? (
                          <span style={{ fontSize: '10px', color: '#2e7d32' }}>Saved</span>
                        ) : '-'}
                      </td>
                      <td style={s.td}>
                        {t.model_artifact_path ? (
                          <span style={{ fontSize: '10px', color: '#1565c0' }}>Saved</span>
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
            </Section>
          )}

          {/* Artifact Manifest */}
          {result.training_artifact_manifest && (
            <Section title="Training Artifact Manifest">
              <div>Artifact Dir: <code style={{ fontSize: '11px' }}>{result.training_artifact_manifest.training_artifact_dir}</code></div>
              {result.training_artifact_manifest.manifest_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Manifest: {result.training_artifact_manifest.manifest_path}</div>
              )}
              {result.training_artifact_manifest.trial_results_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Trial Results: {result.training_artifact_manifest.trial_results_path}</div>
              )}
              <div style={{ marginTop: '4px' }}>
                <strong>Predictions:</strong> {result.training_artifact_manifest.prediction_paths.length} files
              </div>
              <div>
                <strong>Models:</strong> {result.training_artifact_manifest.model_paths.length} files
              </div>
              {result.training_artifact_manifest.log_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Log: {result.training_artifact_manifest.log_path}</div>
              )}
              {result.training_artifact_manifest.split_metadata_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Splits: {result.training_artifact_manifest.split_metadata_path}</div>
              )}
            </Section>
          )}

          {/* Metric Evaluation Input */}
          {result.metric_evaluation_input && (
            <Section title="Metric Evaluation Input (Downstream)">
              <div>
                Ready for Metric Evaluation:{' '}
                <span style={{ color: result.metric_evaluation_input.ready_for_metric_evaluation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.metric_evaluation_input.ready_for_metric_evaluation ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Task Type: {result.metric_evaluation_input.task_type || 'N/A'}</div>
              <div>Target Column: {result.metric_evaluation_input.target_column}</div>
              <div>Primary Metric: <Badge label={result.metric_evaluation_input.primary_metric || 'N/A'} color="#6a1b9a" /></div>
              <div>Metric Direction: {result.metric_evaluation_input.metric_direction}</div>
              <div>Prediction Artifacts: {result.metric_evaluation_input.prediction_artifacts.length}</div>
              <div>Model Artifacts: {result.metric_evaluation_input.model_artifacts.length}</div>
              <div>Trial Results: {result.metric_evaluation_input.trial_results.length} summaries</div>
            </Section>
          )}

          {/* Runtime Environment */}
          {result.runtime_environment && (
            <Section title="Runtime Environment">
              <div style={s.envGrid}>
                <div>Python: {result.runtime_environment.python_version || 'N/A'}</div>
                <div>Platform: {result.runtime_environment.platform || 'N/A'}</div>
                <div>scikit-learn: {result.runtime_environment.scikit_learn_version || 'N/A'}</div>
                <div>pandas: {result.runtime_environment.pandas_version || 'N/A'}</div>
                <div>numpy: {result.runtime_environment.numpy_version || 'N/A'}</div>
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

          {/* Error Message */}
          {result.error_message && (
            <div style={s.errorSection}>
              <strong style={{ color: '#c62828' }}>Error Message:</strong>
              <div style={{ marginTop: '4px', fontSize: '12px' }}>{result.error_message}</div>
            </div>
          )}

          {/* Full JSON */}
          <div style={s.jsonSection}>
            <strong>Full Result (JSON):</strong>
            <pre style={s.pre}>{JSON.stringify(result, null, 2)}</pre>
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
  envGrid: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '4px',
    fontSize: '12px',
    color: '#666',
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

export default PipelineExecutionPanel;
