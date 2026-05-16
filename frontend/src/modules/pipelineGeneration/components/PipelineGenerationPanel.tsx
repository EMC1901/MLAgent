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

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={s.section}>
      <strong style={s.sectionTitle}>{title}</strong>
      <div style={s.sectionContent}>{children}</div>
    </div>
  );

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
              <strong>Status:</strong>{' '}
              <span style={{ color: STATUS_COLORS[result.status] || '#9e9e9e', fontWeight: 600 }}>
                {result.status}
              </span>
            </div>
            <div style={s.field}>
              <strong>Ready for Execution:</strong>{' '}
              <span style={{ color: result.ready_for_execution ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_execution ? 'Yes' : 'No'}
              </span>
            </div>
            <div style={s.field}><strong>Generation Mode:</strong> {result.generation_mode}</div>
          </div>

          {/* Pipeline Bundle Summary */}
          {result.pipeline_bundle && (
            <Section title="Pipeline Bundle Summary">
              <div>Bundle ID: <Badge label={result.pipeline_bundle.bundle_id} color="#1565c0" /></div>
              <div>
                Task Type: <Badge label={result.pipeline_bundle.task_type || 'N/A'} color="#1565c0" />
              </div>
              <div>Target Column: {result.pipeline_bundle.target_column}</div>
              <div>Primary Metric: <Badge label={result.pipeline_bundle.primary_metric || 'N/A'} color="#6a1b9a" /></div>
              <div>Metric Direction: {result.pipeline_bundle.metric_direction}</div>
              <div>Pipeline Specs: <strong>{result.n_pipeline_specs}</strong> total</div>
              <div>Baselines: {result.n_baseline_specs} | HPO: {result.n_hpo_specs}</div>
              {result.pipeline_bundle.feature_columns.length > 0 && (
                <div>Feature Columns: {result.pipeline_bundle.feature_columns.length} columns</div>
              )}
            </Section>
          )}

          {/* Pipeline Spec Table */}
          {result.pipeline_specs && result.pipeline_specs.length > 0 && (
            <Section title={`Pipeline Specs (${result.pipeline_specs.length})`}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Spec ID</th>
                    <th style={s.th}>Role</th>
                    <th style={s.th}>Model</th>
                    <th style={s.th}>Family</th>
                    <th style={s.th}>Priority</th>
                    <th style={s.th}>HPO</th>
                    <th style={s.th}>Exec Ready</th>
                    <th style={s.th}>Warnings</th>
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
                      <td style={s.td}>{spec.warnings.length > 0 ? spec.warnings.length : 'None'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Trial Plan */}
          {result.trial_plan && (
            <Section title="Trial Plan">
              <div>
                HPO Enabled:{' '}
                <Badge label={result.trial_plan.hpo_enabled ? 'Yes' : 'No'} color={result.trial_plan.hpo_enabled ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div>Search Method: <Badge label={result.trial_plan.search_method || 'N/A'} color="#1565c0" /></div>
              <div>Max Total Trials: <strong>{result.trial_plan.max_total_trials}</strong></div>
              <div>Max Parallel Trials: {result.trial_plan.max_parallel_trials}</div>

              {result.trial_plan.trial_allocation && result.trial_plan.trial_allocation.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <strong>Trial Allocation:</strong>
                  <table style={s.table}>
                    <thead>
                      <tr>
                        <th style={s.th}>Model</th>
                        <th style={s.th}>Role</th>
                        <th style={s.th}>Max Trials</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.trial_plan.trial_allocation.map((t, i) => (
                        <tr key={i}>
                          <td style={s.td}>{t.model_id}</td>
                          <td style={s.td}>{t.role}</td>
                          <td style={s.td}>
                            <Badge label={String(t.max_trials)} color={t.max_trials > 1 ? '#1565c0' : '#9e9e9e'} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {result.trial_plan.baseline_trial_policy && (
                <div style={{ marginTop: '4px', fontSize: '12px', color: '#888' }}>
                  Baseline Policy: {result.trial_plan.baseline_trial_policy.description}
                </div>
              )}
              {result.trial_plan.candidate_trial_policy && (
                <div style={{ fontSize: '12px', color: '#888' }}>
                  Candidate Policy: {result.trial_plan.candidate_trial_policy.description}
                </div>
              )}
              {result.trial_plan.early_stopping_policy && result.trial_plan.early_stopping_policy.enabled && (
                <div style={{ fontSize: '12px', color: '#ff9800' }}>
                  Early Stopping: Enabled (patience: {result.trial_plan.early_stopping_policy.patience})
                </div>
              )}
              {result.trial_plan.fallback_policy && result.trial_plan.fallback_policy.enabled && (
                <div style={{ fontSize: '12px', color: '#666' }}>
                  Fallback: {result.trial_plan.fallback_policy.description}
                </div>
              )}
            </Section>
          )}

          {/* Component Binding */}
          {result.component_binding_result && (
            <Section title="Component Binding Result">
              <div>
                All Valid:{' '}
                <span style={{ color: result.component_binding_result.all_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.component_binding_result.all_valid ? 'Yes' : 'No'}
                </span>
              </div>
              {result.component_binding_result.bindings.length > 0 && (
                <table style={s.table}>
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
                    {result.component_binding_result.bindings.map((b, i) => (
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
              {result.component_binding_result.errors.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  {result.component_binding_result.errors.map((e, i) => (
                    <div key={i} style={{ color: '#c62828', fontSize: '12px' }}>{e}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Artifact Manifest */}
          {result.artifact_manifest && (
            <Section title="Artifact Manifest">
              <div>
                Model Ready Matrix:{' '}
                <Badge label={result.artifact_manifest.model_ready_exists ? 'Exists' : 'Missing'} color={result.artifact_manifest.model_ready_exists ? '#2e7d32' : '#c62828'} />
              </div>
              {result.artifact_manifest.model_ready_matrix_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>{result.artifact_manifest.model_ready_matrix_path}</div>
              )}
              <div>
                Preprocessor:{' '}
                <Badge label={result.artifact_manifest.preprocessor_exists ? 'Exists' : 'Missing/N/A'} color={result.artifact_manifest.preprocessor_exists ? '#2e7d32' : '#9e9e9e'} />
              </div>
              {result.artifact_manifest.preprocessor_artifact_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>{result.artifact_manifest.preprocessor_artifact_path}</div>
              )}
              <div>Features: {result.artifact_manifest.n_features}</div>
              <div>Target: {result.artifact_manifest.target_column}</div>
              <div>
                Complete:{' '}
                <span style={{ color: result.artifact_manifest.is_complete ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.artifact_manifest.is_complete ? 'Yes' : 'No'}
                </span>
              </div>
            </Section>
          )}

          {/* Validation & Safety */}
          {result.pipeline_validation_result && (
            <Section title="Pipeline Validation">
              <div>
                Overall Valid:{' '}
                <span style={{ color: result.pipeline_validation_result.is_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.pipeline_validation_result.is_valid ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={{ fontSize: '12px', marginTop: '4px' }}>
                Structure: <Badge label={result.pipeline_validation_result.structure_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.structure_valid ? '#2e7d32' : '#c62828'} />
                {' '}Registry: <Badge label={result.pipeline_validation_result.registry_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.registry_valid ? '#2e7d32' : '#c62828'} />
                {' '}Artifact: <Badge label={result.pipeline_validation_result.artifact_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.artifact_valid ? '#2e7d32' : '#c62828'} />
                {' '}Task Compat: <Badge label={result.pipeline_validation_result.task_type_compatible ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.task_type_compatible ? '#2e7d32' : '#c62828'} />
              </div>
              {result.pipeline_validation_result.errors.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#c62828' }}>Validation Errors:</strong>
                  {result.pipeline_validation_result.errors.map((e, i) => (
                    <div key={i} style={{ color: '#c62828', fontSize: '12px', marginLeft: '8px' }}>{e}</div>
                  ))}
                </div>
              )}
              {result.pipeline_validation_result.warnings.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <strong style={{ color: '#e65100' }}>Validation Warnings:</strong>
                  {result.pipeline_validation_result.warnings.map((w, i) => (
                    <div key={i} style={{ color: '#e65100', fontSize: '12px', marginLeft: '8px' }}>{w}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {result.safety_check_result && (
            <Section title="Safety Check">
              <div>
                Is Safe:{' '}
                <span style={{ color: result.safety_check_result.is_safe ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.safety_check_result.is_safe ? 'Yes' : 'No'}
                </span>
              </div>
              {Object.entries(result.safety_check_result.checks).map(([check, passed]) => (
                <div key={check} style={{ fontSize: '12px' }}>
                  {check}: <Badge label={String(passed)} color={passed ? '#2e7d32' : '#c62828'} />
                </div>
              ))}
              {result.safety_check_result.errors.length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  {result.safety_check_result.errors.map((e, i) => (
                    <div key={i} style={{ color: '#c62828', fontSize: '12px' }}>{e}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* LLM Advisory Review */}
          {result.llm_advisory_review && (
            <Section title="LLM Advisory Review">
              <div style={{ fontSize: '12px', color: '#888', fontStyle: 'italic', marginBottom: '6px' }}>
                Non-blocking machine learning risk notes. System Validator determines execution readiness.
              </div>

              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '4px' }}>
                <div>
                  Impact:{' '}
                  <Badge
                    label={result.llm_advisory_review.execution_impact === 'non_blocking' ? 'Non-blocking' : result.llm_advisory_review.execution_impact}
                    color={result.llm_advisory_review.execution_impact === 'non_blocking' ? '#2e7d32' : '#ff9800'}
                  />
                </div>
                <div>
                  Risk Level:{' '}
                  <Badge
                    label={result.llm_advisory_review.risk_level}
                    color={
                      result.llm_advisory_review.risk_level === 'none' ? '#4caf50' :
                      result.llm_advisory_review.risk_level === 'low' ? '#2196f3' :
                      result.llm_advisory_review.risk_level === 'medium' ? '#ff9800' : '#f44336'
                    }
                  />
                </div>
                <div>
                  Review Confidence:{' '}
                  <Badge
                    label={result.llm_advisory_review.confidence_level}
                    color={
                      result.llm_advisory_review.confidence_level === 'high' ? '#2e7d32' :
                      result.llm_advisory_review.confidence_level === 'medium' ? '#ff9800' : '#ff9800'
                    }
                  />
                </div>
              </div>

              {result.llm_advisory_review.confidence_level === 'low' && (
                <div style={{ fontSize: '11px', color: '#888', fontStyle: 'italic', marginBottom: '4px' }}>
                  Low confidence is expected before actual training metrics are available.
                </div>
              )}

              {/* Checklist */}
              {result.llm_advisory_review.checklist.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ fontSize: '12px' }}>Review Checklist:</strong>
                  <table style={s.table}>
                    <thead>
                      <tr>
                        <th style={s.th}>Dimension</th>
                        <th style={s.th}>Status</th>
                        <th style={s.th}>Comment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.llm_advisory_review.checklist.map((item, i) => (
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
              {result.llm_advisory_review.non_blocking_risks.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ fontSize: '12px', color: '#e65100' }}>Non-blocking Risks:</strong>
                  {result.llm_advisory_review.non_blocking_risks.map((r, i) => (
                    <div key={i} style={{ marginLeft: '8px', marginTop: '2px', fontSize: '11px' }}>
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

              {/* Blocking Issues (should be rare, but shown if present) */}
              {result.llm_advisory_review.blocking_issues.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ fontSize: '12px', color: '#c62828' }}>Potential Blocking Issues (advisory):</strong>
                  {result.llm_advisory_review.blocking_issues.map((r, i) => (
                    <div key={i} style={{ marginLeft: '8px', marginTop: '2px', fontSize: '11px', color: '#c62828' }}>
                      [{r.severity}] {r.category}: {r.message}
                    </div>
                  ))}
                </div>
              )}

              {/* Resource Warnings */}
              {result.llm_advisory_review.resource_warnings.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ fontSize: '12px', color: '#e65100' }}>Resource Warnings:</strong>
                  {result.llm_advisory_review.resource_warnings.map((w, i) => (
                    <div key={i} style={{ fontSize: '11px', marginLeft: '8px', color: '#e65100' }}>{w}</div>
                  ))}
                </div>
              )}

              {/* Future Improvement Suggestions */}
              {result.llm_advisory_review.future_improvement_suggestions.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ fontSize: '12px' }}>Future Improvement Suggestions:</strong>
                  {result.llm_advisory_review.future_improvement_suggestions.map((s, i) => (
                    <div key={i} style={{ fontSize: '11px', marginLeft: '8px' }}>{s}</div>
                  ))}
                </div>
              )}

              {/* Normalization Notes */}
              {result.llm_advisory_review.normalization_notes.length > 0 && (
                <div style={{ marginTop: '6px', padding: '4px 8px', backgroundColor: '#fff8e1', borderRadius: '4px' }}>
                  <strong style={{ fontSize: '11px', color: '#f57f17' }}>Normalization Notes:</strong>
                  {result.llm_advisory_review.normalization_notes.map((n, i) => (
                    <div key={i} style={{ fontSize: '10px', marginLeft: '8px', color: '#f57f17' }}>{n}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Execution Input */}
          {result.execution_input && (
            <Section title="Execution Input (For Downstream)">
              <div>Pipeline Generation ID: {result.execution_input.pipeline_generation_id}</div>
              <div>Pipeline Bundle ID: {result.execution_input.pipeline_bundle_id}</div>
              <div>Task Type: {result.execution_input.task_type || 'N/A'}</div>
              <div>Target Column: {result.execution_input.target_column}</div>
              <div>Feature Columns: {result.execution_input.feature_columns.length} columns</div>
              <div>Pipeline Specs: {result.execution_input.pipeline_specs.length}</div>
              <div>
                Ready for Execution:{' '}
                <span style={{ color: result.execution_input.ready_for_execution ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.execution_input.ready_for_execution ? 'Yes' : 'No'}
                </span>
              </div>
              {result.execution_input.model_ready_matrix_path && (
                <div style={{ fontSize: '12px', color: '#888' }}>Data: {result.execution_input.model_ready_matrix_path}</div>
              )}
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

export default PipelineGenerationPanel;
