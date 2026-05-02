import React, { useState } from 'react';
import { createFeatureEngineering, rerunFeatureEngineering } from '../../../api/featureEngineeringApi';
import { FeatureEngineeringResponse } from '../types';

interface FeatureEngineeringPanelProps {
  taskId: string;
}

const FeatureEngineeringPanel: React.FC<FeatureEngineeringPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FeatureEngineeringResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFeatureEngineering(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run feature engineering.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFeatureEngineering(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run feature engineering.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#4caf50';
      case 'completed_with_warning': return '#ff9800';
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
      <h3 style={styles.title}>Automated Feature Engineering</h3>
      <p style={styles.description}>
        Convert raw material input into ML-ready feature matrices based on the
        workflow plan&rsquo;s feature strategy.
      </p>

      <div style={styles.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={styles.runButton}>
          {loading ? 'Running...' : 'Run Feature Engineering'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={styles.rerunButton}>
          {loading ? 'Running...' : 'Re-run Feature Engineering'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Feature Engineering Result</h4>

          <div style={styles.fieldRow}>
            <div style={styles.field}><strong>FE ID:</strong> {result.feature_engineering_id}</div>
            <div style={styles.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={styles.field}><strong>Input Modality:</strong> {result.input_modality}</div>
            <div style={styles.field}><strong>Feature Type:</strong> {result.feature_type}</div>
          </div>

          {/* Feature Generation */}
          {result.feature_generation && (
            <Section title="Feature Generation">
              <div>
                <strong>Selected:</strong>{' '}
                {result.feature_generation.selected_featurizers?.map((f, i) => (
                  <Badge key={i} label={f} color="#2e7d32" />
                ))}
              </div>
              {result.feature_generation.semantic_featurizers && result.feature_generation.semantic_featurizers.length > 0 && (
                <div>
                  <strong>Semantic:</strong>{' '}
                  {result.feature_generation.semantic_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#1565c0" />
                  ))}
                </div>
              )}
              {result.feature_generation.fallback_featurizers && result.feature_generation.fallback_featurizers.length > 0 && (
                <div>
                  <strong>Fallback:</strong>{' '}
                  {result.feature_generation.fallback_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#ff9800" />
                  ))}
                </div>
              )}
              {result.feature_generation.skipped_featurizers && result.feature_generation.skipped_featurizers.length > 0 && (
                <div>
                  <strong>Skipped:</strong>{' '}
                  {result.feature_generation.skipped_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#9e9e9e" />
                  ))}
                </div>
              )}
              {result.feature_generation.unsupported_future_featurizers && result.feature_generation.unsupported_future_featurizers.length > 0 && (
                <div>
                  <strong>Future/Unsupported:</strong>{' '}
                  {result.feature_generation.unsupported_future_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#9e9e9e" />
                  ))}
                </div>
              )}
              {result.feature_generation.executed_featurizers?.map((ef, i) => (
                <div key={i} style={{ marginTop: '4px' }}>
                  <strong>{ef.display_name || ef.name}:</strong>{' '}
                  <span style={{ color: ef.status === 'success' ? '#2e7d32' : ef.status === 'failed' ? '#c62828' : '#ff9800' }}>
                    {ef.status}
                  </span>
                  {' '}({ef.n_features_generated} features, {ef.failed_sample_count} failed
                  {ef.execution_time_ms != null ? `, ${ef.execution_time_ms}ms` : ''})
                  {ef.dependency_versions && Object.keys(ef.dependency_versions).length > 0 && (
                    <span style={{ fontSize: '11px', color: '#888' }}>
                      {' '}deps: {JSON.stringify(ef.dependency_versions)}
                    </span>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Feature Matrix */}
          {result.feature_matrix && (
            <Section title="Feature Matrix">
              <div>Samples: {result.feature_matrix.n_samples}</div>
              <div>Features: {result.feature_matrix.n_features}</div>
              <div>Target Column: {result.feature_matrix.target_column}</div>
              <div>Artifact ID: {result.feature_matrix.artifact_id}</div>
            </Section>
          )}

          {/* Feature Schema */}
          {result.feature_schema && (
            <Section title="Feature Schema">
              <div>Numeric: {result.feature_schema.numeric_feature_count}</div>
              <div>Categorical: {result.feature_schema.categorical_feature_count}</div>
              <div>Constant: {result.feature_schema.constant_feature_count}</div>
              <div>All-missing: {result.feature_schema.all_missing_feature_count}</div>
            </Section>
          )}

          {/* Feature Groups */}
          {result.feature_schema?.feature_groups && result.feature_schema.feature_groups.length > 0 && (
            <Section title="Feature Groups">
              {result.feature_schema.feature_groups.map((g, i) => (
                <div key={i} style={{ marginBottom: '4px' }}>
                  <strong>{g.group_name}:</strong>{' '}
                  <span style={{ color: g.status === 'success' ? '#2e7d32' : '#9e9e9e' }}>
                    {g.status}
                  </span>
                  {' '}({g.n_features} features)
                  {g.display_name && (
                    <span style={{ fontSize: '11px', color: '#888' }}> — {g.display_name}</span>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Feature Quality */}
          {result.feature_quality && (
            <Section title="Feature Quality">
              <div>Valid Matrix: {result.feature_quality.is_valid_feature_matrix ? 'Yes' : 'No'}</div>
              <div>Total Missing: {result.feature_quality.missing_values?.total_missing}</div>
              {result.feature_quality.dropped_features && result.feature_quality.dropped_features.length > 0 && (
                <div>Dropped Features: {result.feature_quality.dropped_features.join(', ')}</div>
              )}
              {result.feature_quality.constant_features && result.feature_quality.constant_features.length > 0 && (
                <div>Constant Features: {result.feature_quality.constant_features.join(', ')}</div>
              )}
              {result.feature_quality.invalid_features && result.feature_quality.invalid_features.length > 0 && (
                <div>Invalid Features: {result.feature_quality.invalid_features.join(', ')}</div>
              )}
            </Section>
          )}

          {/* Preprocessing */}
          {result.preprocessing_requirements && (
            <Section title="Preprocessing Requirements">
              <div>Scaling Required: {result.preprocessing_requirements.scaling_required ? 'Yes' : 'No'}</div>
              <div>Imputation Required: {result.preprocessing_requirements.imputation_required ? 'Yes' : 'No'}</div>
              <div>Feature Selection Required: {result.preprocessing_requirements.feature_selection_required ? 'Yes' : 'No'}</div>
            </Section>
          )}

          {/* Downstream Input */}
          {result.downstream_input && (
            <Section title="Downstream Input">
              <div>Ready for Pipeline Generation: <strong>{result.downstream_input.ready_for_pipeline_generation ? 'Yes' : 'No'}</strong></div>
              <div>Task Type: {result.downstream_input.task_type}</div>
              <div>Primary Metric: {result.downstream_input.primary_metric}</div>
              <div>Target Column: {result.downstream_input.target_column}</div>
              <div>Feature Count: {result.downstream_input.feature_columns?.length}</div>
            </Section>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.warningSection}>
              <strong style={{ color: '#e65100' }}>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={styles.warningItem}>{w}</div>
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

export default FeatureEngineeringPanel;
