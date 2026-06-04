import React, { useState } from 'react';
import {
  createPipelineGeneration,
  rerunPipelineGeneration,
} from '../../../api/pipelineGenerationApi';
import { PipelineGenerationResponse } from '../types';
import { STATUS_COLORS, PRIORITY_COLORS, ROLE_COLORS } from '../constants';

interface PipelineGenerationPanelProps {
  taskId: string;
  initialResult?: PipelineGenerationResponse;
}

const PipelineGenerationPanel: React.FC<PipelineGenerationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineGenerationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createPipelineGeneration(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to generate pipeline.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunPipelineGeneration(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run pipeline generation.');
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
        {/* Pipeline Bundle Summary */}
        {result.pipeline_bundle && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Pipeline Bundle Summary</h4>
            <div style={s.grid}>
              <div style={s.field}>
                <strong>Bundle ID: </strong>
                <Badge label={result.pipeline_bundle.bundle_id} color="#1565c0" />
              </div>
              <div style={s.field}>
                <strong>Task Type: </strong>
                <Badge label={result.pipeline_bundle.task_type || 'N/A'} color="#1565c0" />
              </div>
              <div style={s.field}><strong>Target Column:</strong> {result.pipeline_bundle.target_column}</div>
              <div style={s.field}>
                <strong>Primary Metric: </strong>
                <Badge label={result.pipeline_bundle.primary_metric || 'N/A'} color="#6a1b9a" />
              </div>
              <div style={s.field}><strong>Metric Direction:</strong> {result.pipeline_bundle.metric_direction}</div>
              <div style={s.field}>
                <strong>Pipeline Specs:</strong> {result.n_pipeline_specs} total
              </div>
              <div style={s.field}>
                <strong>Baselines:</strong> {result.n_baseline_specs} | <strong>HPO:</strong> {result.n_hpo_specs}
              </div>
              {result.pipeline_bundle.feature_columns.length > 0 && (
                <div style={s.field}>
                  <strong>Feature Columns:</strong> {result.pipeline_bundle.feature_columns.length} columns
                </div>
              )}
            </div>
          </div>
        )}

        {/* Validation */}
        {result.pipeline_validation_result && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Pipeline Validation</h4>
            <div style={s.grid}>
              <div style={s.field}>
                <strong>Overall Valid: </strong>
                <span style={{ color: result.pipeline_validation_result.is_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.pipeline_validation_result.is_valid ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={s.field}>
                <strong>Structure: </strong>
                <Badge label={result.pipeline_validation_result.structure_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.structure_valid ? '#2e7d32' : '#c62828'} />
              </div>
              <div style={s.field}>
                <strong>Registry: </strong>
                <Badge label={result.pipeline_validation_result.registry_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.registry_valid ? '#2e7d32' : '#c62828'} />
              </div>
              <div style={s.field}>
                <strong>Artifact: </strong>
                <Badge label={result.pipeline_validation_result.artifact_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.artifact_valid ? '#2e7d32' : '#c62828'} />
              </div>
              <div style={s.field}>
                <strong>Task Compat: </strong>
                <Badge label={result.pipeline_validation_result.task_type_compatible ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.task_type_compatible ? '#2e7d32' : '#c62828'} />
              </div>
            </div>
            {result.pipeline_validation_result.errors.length > 0 && (
              <div style={s.subCard}>
                <strong style={{ color: '#c62828' }}>Validation Errors:</strong>
                <ul style={s.list}>
                  {result.pipeline_validation_result.errors.map((e, i) => (
                    <li key={i} style={{ color: '#c62828', fontSize: '12px' }}>{e}</li>
                  ))}
                </ul>
              </div>
            )}
            {result.pipeline_validation_result.warnings.length > 0 && (
              <div style={s.subCard}>
                <strong style={{ color: '#e65100' }}>Validation Warnings:</strong>
                <ul style={s.list}>
                  {result.pipeline_validation_result.warnings.map((w, i) => (
                    <li key={i} style={{ color: '#e65100', fontSize: '12px' }}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  const renderPipelineSpecs = () => {
    if (!result?.pipeline_specs || result.pipeline_specs.length === 0) {
      return <p>No pipeline specs available.</p>;
    }
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Pipeline Specs ({result.pipeline_specs.length})</h4>
        <table style={{ ...s.table, minWidth: '800px' }}>
          <thead>
            <tr>
              <th style={s.th}>Spec ID</th>
              <th style={s.th}>Role</th>
              <th style={s.th}>Model</th>
              <th style={s.th}>Family</th>
              <th style={s.th}>Priority</th>
              <th style={s.th}>HPO</th>
              <th style={s.th}>Exec Ready</th>
            </tr>
          </thead>
          <tbody>
            {result.pipeline_specs.map((spec, i) => (
              <tr key={i}>
                <td style={s.td}><code>{spec.pipeline_spec_id}</code></td>
                <td style={s.td}>
                  <Badge label={spec.pipeline_role} color={ROLE_COLORS[spec.pipeline_role] || '#1976d2'} />
                </td>
                <td style={s.td}>{spec.model_display_name || spec.model_id}</td>
                <td style={s.td}>{spec.model_family || '-'}</td>
                <td style={s.td}>
                  <Badge label={spec.priority} color={PRIORITY_COLORS[spec.priority] || '#1976d2'} />
                </td>
                <td style={s.td}>
                  <Badge label={spec.hpo_enabled ? 'Yes' : 'No'} color={spec.hpo_enabled ? '#2e7d32' : '#9e9e9e'} />
                </td>
                <td style={s.td}>
                  <span style={{ color: spec.execution_ready ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                    {spec.execution_ready ? 'Yes' : 'No'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderComponentBinding = () => {
    if (!result?.component_binding_result) {
      return <p>No component binding results available.</p>;
    }
    const cb = result.component_binding_result;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Component Binding Result</h4>
        <div style={s.field}>
          <strong>All Valid: </strong>
          <span style={{ color: cb.all_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
            {cb.all_valid ? 'Yes' : 'No'}
          </span>
        </div>
        {cb.bindings.length > 0 && (
          <table style={{ ...s.table, marginTop: '8px' }}>
            <thead>
              <tr>
                <th style={s.th}>Model</th>
                <th style={s.th}>Registry</th>
                <th style={s.th}>HPO Valid</th>
                <th style={s.th}>Val. Strategy</th>
                <th style={s.th}>Metric Valid</th>
              </tr>
            </thead>
            <tbody>
              {cb.bindings.map((b, i) => (
                <tr key={i}>
                  <td style={s.td}>{b.model_id}</td>
                  <td style={s.td}>
                    <Badge label={b.model_registry_valid ? 'Valid' : 'Invalid'} color={b.model_registry_valid ? '#2e7d32' : '#c62828'} />
                  </td>
                  <td style={s.td}>
                    <Badge label={b.hpo_registry_valid ? 'Valid' : 'N/A'} color={b.hpo_registry_valid ? '#2e7d32' : '#9e9e9e'} />
                  </td>
                  <td style={s.td}>
                    <Badge label={b.validation_strategy_valid ? 'Valid' : 'Invalid'} color={b.validation_strategy_valid ? '#2e7d32' : '#c62828'} />
                  </td>
                  <td style={s.td}>
                    <Badge label={b.metric_valid ? 'Valid' : 'Invalid'} color={b.metric_valid ? '#2e7d32' : '#c62828'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        {cb.errors.length > 0 && (
          <div style={s.subCard}>
            <strong style={{ color: '#c62828' }}>Binding Errors:</strong>
            <ul style={s.list}>
              {cb.errors.map((e, i) => (
                <li key={i} style={{ color: '#c62828', fontSize: '12px' }}>{e}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderLlmReview = () => {
    if (!result?.llm_advisory_review) {
      return <p>No AI advisory review available.</p>;
    }
    const review = result.llm_advisory_review;
    return (
      <div>
        <div style={s.card}>
          <h4 style={s.cardTitle}>AI Advisory Review</h4>
          <p style={{ fontSize: '12px', color: '#888', fontStyle: 'italic', marginBottom: '8px' }}>
            Non-blocking machine learning risk notes. System Validator determines execution readiness.
          </p>

          <div style={s.grid}>
            <div style={s.field}>
              <strong>Impact: </strong>
              <Badge
                label={review.execution_impact === 'non_blocking' ? 'Non-blocking' : review.execution_impact}
                color={review.execution_impact === 'non_blocking' ? '#2e7d32' : '#ff9800'}
              />
            </div>
            <div style={s.field}>
              <strong>Risk Level: </strong>
              <Badge
                label={review.risk_level}
                color={
                  review.risk_level === 'none' ? '#4caf50' :
                  review.risk_level === 'low' ? '#2196f3' :
                  review.risk_level === 'medium' ? '#ff9800' : '#f44336'
                }
              />
            </div>
            <div style={s.field}>
              <strong>Review Confidence: </strong>
              <Badge
                label={review.confidence_level}
                color={
                  review.confidence_level === 'high' ? '#2e7d32' :
                  review.confidence_level === 'medium' ? '#ff9800' : '#ff9800'
                }
              />
            </div>
          </div>

          {review.confidence_level === 'low' && (
            <p style={{ fontSize: '11px', color: '#888', fontStyle: 'italic', marginBottom: '4px' }}>
              Low confidence is expected before actual training metrics are available.
            </p>
          )}

          {/* Checklist */}
          {review.checklist.length > 0 && (
            <div style={s.subCard}>
              <strong>Review Checklist:</strong>
              <table style={{ ...s.table, marginTop: '8px' }}>
                <thead>
                  <tr>
                    <th style={s.th}>Dimension</th>
                    <th style={s.th}>Status</th>
                    <th style={s.th}>Comment</th>
                  </tr>
                </thead>
                <tbody>
                  {review.checklist.map((item, i) => (
                    <tr key={i}>
                      <td style={s.td}>{item.dimension}</td>
                      <td style={s.td}>
                        <Badge
                          label={item.status}
                          color={
                            item.status === 'pass' ? '#2e7d32' :
                            item.status === 'warning' ? '#ff9800' : '#9e9e9e'
                          }
                        />
                      </td>
                      <td style={s.td}>{item.comment}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Non-blocking Risks */}
          {review.non_blocking_risks.length > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#e65100' }}>Non-blocking Risks:</strong>
              {review.non_blocking_risks.map((r, i) => (
                <div key={i} style={{ marginLeft: '8px', marginTop: '4px', fontSize: '11px' }}>
                  <Badge label={r.severity} color={
                    r.severity === 'high' ? '#c62828' :
                    r.severity === 'medium' ? '#ff9800' : '#2196f3'
                  } />
                  {' '}[{r.category}] {r.message}
                  {r.suggested_action && (
                    <div style={{ color: '#888', marginLeft: '8px' }}>→ {r.suggested_action}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Blocking Issues */}
          {review.blocking_issues.length > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#c62828' }}>Potential Blocking Issues (advisory):</strong>
              {review.blocking_issues.map((r, i) => (
                <div key={i} style={{ marginLeft: '8px', marginTop: '2px', fontSize: '11px', color: '#c62828' }}>
                  [{r.severity}] {r.category}: {r.message}
                </div>
              ))}
            </div>
          )}

          {/* Resource Warnings */}
          {review.resource_warnings.length > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#e65100' }}>Resource Warnings:</strong>
              <ul style={s.list}>
                {review.resource_warnings.map((w, i) => (
                  <li key={i} style={{ color: '#e65100', fontSize: '11px' }}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Future Improvement Suggestions */}
          {review.future_improvement_suggestions.length > 0 && (
            <div style={s.subCard}>
              <strong>Future Improvement Suggestions:</strong>
              <ul style={s.list}>
                {review.future_improvement_suggestions.map((sug, i) => (
                  <li key={i} style={{ fontSize: '11px' }}>{sug}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Normalization Notes */}
          {review.normalization_notes.length > 0 && (
            <div style={{ ...s.subCard, backgroundColor: '#fff8e1' }}>
              <strong style={{ color: '#f57f17', fontSize: '11px' }}>Normalization Notes:</strong>
              {review.normalization_notes.map((n, i) => (
                <div key={i} style={{ fontSize: '10px', marginLeft: '8px', color: '#f57f17' }}>{n}</div>
              ))}
            </div>
          )}
        </div>
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
    { id: 'specs', label: 'Pipeline Specs' },
    { id: 'binding', label: 'Component Binding' },
    { id: 'review', label: 'AI Review' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Executable Pipeline Generation</h3>
      <p style={s.description}>
        Convert the Model Search Plan into validated, registry-bound Pipeline Specs
        and Execution Input ready for the downstream Pipeline Execution module.
        This module generates specifications only — no training is performed.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleGenerate} disabled={loading} style={s.runButton}>
          {loading ? 'Generating Pipeline...' : 'Generate Pipeline'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Generating...' : 'Re-run Generation'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Pipeline Generation Result</h4>

          {/* Summary Row */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>PG ID:</strong> {result.pipeline_generation_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}>
              <strong>Ready for Execution: </strong>
              <span style={{ color: result.ready_for_execution ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_execution ? 'Yes' : 'No'}
              </span>
            </div>
            <div style={s.field}><strong>Generation Mode:</strong> {result.generation_mode}</div>
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
            {activeTab === 'specs' && renderPipelineSpecs()}
            {activeTab === 'binding' && renderComponentBinding()}
            {activeTab === 'review' && renderLlmReview()}
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
  subCard: {
    padding: '10px', backgroundColor: '#fff', borderRadius: '4px',
    marginBottom: '8px', border: '1px solid #eee',
    marginTop: '8px',
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
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
};

export default PipelineGenerationPanel;
