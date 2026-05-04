import React, { useState } from 'react';
import {
  createFeaturePreprocessing,
  rerunFeaturePreprocessing,
} from '../../../api/featurePreprocessingApi';
import { FeaturePreprocessingResponse } from '../types';

interface FeaturePreprocessingPanelProps {
  taskId: string;
}

const FeaturePreprocessingPanel: React.FC<FeaturePreprocessingPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FeaturePreprocessingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFeaturePreprocessing(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run feature preprocessing.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFeaturePreprocessing(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run feature preprocessing.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'preprocessed': return '#4caf50';
      case 'preprocessed_with_warning': return '#ff9800';
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
      <h3 style={styles.title}>Feature Preprocessing</h3>
      <p style={styles.description}>
        Clean, impute, scale, and select features from the feature engineering output
        to produce a model-ready dataset.
      </p>

      <div style={styles.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={styles.runButton}>
          {loading ? 'Running...' : 'Run Feature Preprocessing'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={styles.rerunButton}>
          {loading ? 'Running...' : 'Re-run Preprocessing'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Feature Preprocessing Result</h4>

          <div style={styles.fieldRow}>
            <div style={styles.field}><strong>Preprocessing ID:</strong> {result.preprocessing_id}</div>
            <div style={styles.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={styles.field}><strong>FE ID:</strong> {result.feature_engineering_id}</div>
            <div style={styles.field}><strong>WP ID:</strong> {result.workflow_plan_id}</div>
          </div>

          {/* Validation Summary */}
          {result.validation_summary && (
            <Section title="Validation Summary">
              <div>
                Model Ready:{' '}
                <span style={{ color: result.validation_summary.is_model_ready ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.validation_summary.is_model_ready ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Samples: {result.validation_summary.n_samples}</div>
              <div>Raw Features: {result.validation_summary.n_raw_features}</div>
              <div>Valid Before Preprocessing: {result.validation_summary.n_valid_features_before_preprocessing}</div>
              <div>After Preprocessing: {result.validation_summary.n_features_after_preprocessing}</div>
              <div>Dropped Features: {result.validation_summary.n_dropped_features}</div>
              <div>Target Column: {result.validation_summary.target_column}</div>
              <div>Task Type: {result.validation_summary.task_type}</div>
            </Section>
          )}

          {/* Column Filtering */}
          {result.column_validation && (
            <Section title="Column Filtering">
              {result.column_validation.retained_features && result.column_validation.retained_features.length > 0 && (
                <div>Retained: {result.column_validation.retained_features.length} features</div>
              )}
              {result.column_validation.dropped_invalid_features && result.column_validation.dropped_invalid_features.length > 0 && (
                <div>
                  Invalid Features:{' '}
                  {result.column_validation.dropped_invalid_features.map((f, i) => (
                    <Badge key={i} label={f.name} color="#c62828" />
                  ))}
                </div>
              )}
              {result.column_validation.dropped_all_missing_features && result.column_validation.dropped_all_missing_features.length > 0 && (
                <div>
                  All-Missing:{' '}
                  {result.column_validation.dropped_all_missing_features.map((f, i) => (
                    <Badge key={i} label={f.name} color="#c62828" />
                  ))}
                </div>
              )}
              {result.column_validation.dropped_constant_features && result.column_validation.dropped_constant_features.length > 0 && (
                <div>
                  Constant:{' '}
                  {result.column_validation.dropped_constant_features.map((f, i) => (
                    <Badge key={i} label={f.name} color="#ff9800" />
                  ))}
                </div>
              )}
              {result.column_validation.dropped_high_missing_features && result.column_validation.dropped_high_missing_features.length > 0 && (
                <div>
                  High-Missing:{' '}
                  {result.column_validation.dropped_high_missing_features.map((f, i) => (
                    <Badge key={i} label={f.name} color="#ff9800" />
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Feature Group Validation */}
          {result.feature_group_validation && result.feature_group_validation.groups && result.feature_group_validation.groups.length > 0 && (
            <Section title="Feature Group Validation">
              {result.feature_group_validation.groups.map((g, i) => (
                <div key={i} style={{ marginBottom: '4px' }}>
                  <strong>{g.group_name}:</strong>{' '}
                  <span style={{ color: g.status === 'retained' ? '#2e7d32' : g.status === 'dropped' ? '#c62828' : '#ff9800' }}>
                    {g.status}
                  </span>
                  {' '}({g.n_valid_features}/{g.n_raw_features} valid)
                  {g.reason && <span style={{ fontSize: '11px', color: '#888' }}> — {g.reason}</span>}
                </div>
              ))}
            </Section>
          )}

          {/* Preprocessing Execution */}
          {result.preprocessing_execution && (
            <Section title="Preprocessing Execution">
              <div>
                Imputation:{' '}
                {result.preprocessing_execution.imputation.executed
                  ? <Badge label={`Executed (${result.preprocessing_execution.imputation.strategy})`} color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Scaling:{' '}
                {result.preprocessing_execution.scaling.executed
                  ? <Badge label={`Executed (${result.preprocessing_execution.scaling.strategy})`} color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Categorical Encoding:{' '}
                {result.preprocessing_execution.categorical_encoding.executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
              <div>
                Feature Selection:{' '}
                {result.preprocessing_execution.feature_selection.executed
                  ? (
                    <Badge
                      label={`Executed (${result.preprocessing_execution.feature_selection.strategy})${result.preprocessing_execution.feature_selection.columns_dropped.length > 0 ? ` - ${result.preprocessing_execution.feature_selection.columns_dropped.length} dropped` : ''}`}
                      color="#2e7d32"
                    />
                  )
                  : <Badge label="None" color="#9e9e9e" />}
              </div>
            </Section>
          )}

          {/* Model Ready Artifact */}
          {result.model_ready_artifact && (
            <Section title="Model Ready Artifact">
              <div>Artifact ID: {result.model_ready_artifact.artifact_id}</div>
              <div>Storage: {result.model_ready_artifact.storage_type}</div>
              <div>Samples: {result.model_ready_artifact.n_samples}</div>
              <div>Features: {result.model_ready_artifact.n_features}</div>
              <div>Target: {result.model_ready_artifact.target_column}</div>
            </Section>
          )}

          {/* Model Search Input */}
          {result.model_search_input && (
            <Section title="Model Search Input">
              <div>
                Ready for Model Search:{' '}
                <span style={{ color: result.model_search_input.ready_for_model_search ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.model_search_input.ready_for_model_search ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Task Type: {result.model_search_input.task_type}</div>
              <div>Primary Metric: {result.model_search_input.primary_metric}</div>
              <div>Target: {result.model_search_input.target_column}</div>
              <div>Feature Count: {result.model_search_input.feature_columns?.length}</div>
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

export default FeaturePreprocessingPanel;
