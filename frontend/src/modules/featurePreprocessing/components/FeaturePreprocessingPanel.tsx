import React, { useState } from 'react';
import {
  createFeaturePreprocessing,
  rerunFeaturePreprocessing,
} from '../../../api/featurePreprocessingApi';
import { FeaturePreprocessingResponse, PreprocessingPlan, PreprocessingExecutionReport, ExplainabilityPreservationReport, PreprocessingProvenance } from '../types';

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

  const Section: React.FC<{ title: string; children: React.ReactNode; collapsible?: boolean }> = ({ title, children }) => {
    const [open, setOpen] = useState(true);
    return (
      <div style={styles.section}>
        <div style={styles.sectionHeader} onClick={() => setOpen(!open)}>
          <strong style={styles.sectionTitle}>{title}</strong>
          <span style={{ fontSize: '11px', color: '#999', cursor: 'pointer' }}>
            {open ? '▼' : '▶'}
          </span>
        </div>
        {open && <div style={styles.sectionContent}>{children}</div>}
      </div>
    );
  };

  const renderRationale = (r: any) => {
    if (!r) return null;
    return (
      <div style={styles.rationaleBox}>
        {r.reason && <div><strong>Reason:</strong> {r.reason}</div>}
        {r.evidence && r.evidence.length > 0 && <div><strong>Evidence:</strong> {r.evidence.join('; ')}</div>}
        {r.expected_benefit && <div><strong>Benefit:</strong> {r.expected_benefit}</div>}
        {r.risk && <div><strong>Risk:</strong> {r.risk}</div>}
        {r.fallback && <div><strong>Fallback:</strong> {r.fallback}</div>}
      </div>
    );
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Feature Preprocessing (LLM-Guided)</h3>
      <p style={styles.description}>
        LLM plans and executes preprocessing: leakage detection, imputation, scaling,
        feature selection, dimensionality reduction — producing model-ready artifacts
        with full lineage and provenance.
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
            {result.preprocessing_registry_snapshot_version && (
              <div style={styles.field}><strong>Registry:</strong> {result.preprocessing_registry_snapshot_version}</div>
            )}
          </div>

          {/* NEW: Preprocessing Plan */}
          {result.preprocessing_plan && (
            <Section title="Preprocessing Plan (LLM-Generated)">
              <div style={{ marginBottom: '8px' }}>
                <strong>Plan Version:</strong> {result.preprocessing_plan.plan_version}
                {result.preprocessing_plan.plan_id && (
                  <span style={{ marginLeft: '16px' }}><strong>Plan ID:</strong> {result.preprocessing_plan.plan_id}</span>
                )}
              </div>

              {/* Global Policy */}
              {result.preprocessing_plan.global_policy && (
                <div style={{ marginBottom: '6px' }}>
                  <strong>Global Policy:</strong>
                  <div style={{ marginLeft: '12px', fontSize: '12px' }}>
                    {result.preprocessing_plan.global_policy.leakage_prevention && (
                      <div>
                        <strong>Leakage Prevention:</strong>{' '}
                        scope={result.preprocessing_plan.global_policy.leakage_prevention.fit_transform_scope}
                        , target_excluded={result.preprocessing_plan.global_policy.leakage_prevention.target_column_excluded ? 'Yes' : 'No'}
                        , id_excluded={result.preprocessing_plan.global_policy.leakage_prevention.id_columns_excluded ? 'Yes' : 'No'}
                        , target_aware={result.preprocessing_plan.global_policy.leakage_prevention.target_aware_selection_allowed ? 'Yes' : 'No'}
                      </div>
                    )}
                    {result.preprocessing_plan.global_policy.variant_strategy && (
                      <div>
                        <strong>Variant Strategy:</strong>{' '}
                        mode={result.preprocessing_plan.global_policy.variant_strategy.mode}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Capability Groups */}
              {result.preprocessing_plan.capability_groups_used && result.preprocessing_plan.capability_groups_used.length > 0 && (
                <div style={{ marginBottom: '6px' }}>
                  <strong>Capability Groups Used:</strong>{' '}
                  {result.preprocessing_plan.capability_groups_used.map((g, i) => (
                    <Badge key={i} label={g} color="#1565c0" />
                  ))}
                </div>
              )}

              {/* Operation Sequence */}
              {result.preprocessing_plan.operation_sequence && result.preprocessing_plan.operation_sequence.length > 0 && (
                <div>
                  <strong>Operation Sequence ({result.preprocessing_plan.operation_sequence.length} ops):</strong>
                  <table style={styles.smallTable}>
                    <thead>
                      <tr>
                        <th style={styles.th}>#</th>
                        <th style={styles.th}>Capability</th>
                        <th style={styles.th}>Scope</th>
                        <th style={styles.th}>Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.preprocessing_plan.operation_sequence.map((op, i) => (
                        <tr key={i} style={styles.tableRow}>
                          <td style={styles.td}>{op.step_order}</td>
                          <td style={styles.td}>
                            <Badge label={op.capability_id} color="#2e7d32" />
                            {op.operation_id && <div style={{ fontSize: '10px', color: '#999' }}>{op.operation_id}</div>}
                          </td>
                          <td style={styles.td}>{op.execution_scope}</td>
                          <td style={styles.td}>{renderRationale(op.decision_rationale)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Column Policies */}
              {result.preprocessing_plan.column_policies && result.preprocessing_plan.column_policies.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong>Column Policies:</strong>{' '}
                  {result.preprocessing_plan.column_policies.map((cp, i) => (
                    <Badge
                      key={i}
                      label={`${cp.column_name}: ${cp.action}`}
                      color={cp.action === 'drop' ? '#c62828' : cp.action === 'transform' ? '#ff9800' : '#2e7d32'}
                    />
                  ))}
                </div>
              )}

              {/* Rejected Operations */}
              {result.preprocessing_plan.rejected_operations && result.preprocessing_plan.rejected_operations.length > 0 && (
                <div style={{ marginTop: '6px' }}>
                  <strong style={{ color: '#c62828' }}>Rejected Operations:</strong>
                  {result.preprocessing_plan.rejected_operations.map((ro, i) => (
                    <div key={i} style={{ fontSize: '11px', marginLeft: '8px', color: '#888' }}>
                      {ro.capability_id}: {ro.reason}
                    </div>
                  ))}
                </div>
              )}

              {/* Warnings for Downstream */}
              {result.preprocessing_plan.warnings_for_downstream && result.preprocessing_plan.warnings_for_downstream.length > 0 && (
                <div style={{ marginTop: '6px', padding: '6px', backgroundColor: '#fff3e0', borderRadius: '4px', fontSize: '11px' }}>
                  <strong>Downstream Warnings:</strong>
                  {result.preprocessing_plan.warnings_for_downstream.map((w, i) => (
                    <div key={i}>⚠ {w}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* NEW: Execution Report */}
          {result.execution_report && result.execution_report.operation_results && result.execution_report.operation_results.length > 0 && (
            <Section title="Execution Report">
              <table style={styles.smallTable}>
                <thead>
                  <tr>
                    <th style={styles.th}>Operation</th>
                    <th style={styles.th}>Capability</th>
                    <th style={styles.th}>Group</th>
                    <th style={styles.th}>Status</th>
                    <th style={styles.th}>Affected</th>
                    <th style={styles.th}>Removed</th>
                    <th style={styles.th}>Warnings</th>
                  </tr>
                </thead>
                <tbody>
                  {result.execution_report.operation_results.map((op, i) => (
                    <tr key={i} style={styles.tableRow}>
                      <td style={styles.td}>{op.operation_id}</td>
                      <td style={styles.td}><Badge label={op.capability_id} color="#1976d2" /></td>
                      <td style={styles.td}>{op.capability_group}</td>
                      <td style={styles.td}>
                        <span style={{
                          color: op.status === 'success' ? '#2e7d32' : op.status === 'failed' ? '#c62828' : '#ff9800',
                          fontWeight: 600, fontSize: '11px',
                        }}>
                          {op.status}
                        </span>
                      </td>
                      <td style={styles.td}>{op.affected_features.length}</td>
                      <td style={styles.td}>{op.removed_features.length}</td>
                      <td style={styles.td}>
                        {op.warnings && op.warnings.length > 0 && (
                          <span style={{ color: '#e65100', fontSize: '10px' }}>
                            {op.warnings.length} warning(s)
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* Validation Summary (Legacy) */}
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

          {/* Column Filtering (Legacy) */}
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

          {/* Feature Group Validation (Legacy) */}
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

          {/* Preprocessing Execution (Legacy) */}
          {result.preprocessing_execution && (
            <Section title="Preprocessing Execution (Legacy)">
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

          {/* NEW: Removed Features */}
          {result.removed_features && result.removed_features.length > 0 && (
            <Section title={`Removed Features (${result.removed_features.length})`}>
              <table style={styles.smallTable}>
                <thead>
                  <tr>
                    <th style={styles.th}>Feature</th>
                    <th style={styles.th}>Reason</th>
                    <th style={styles.th}>Source Group</th>
                  </tr>
                </thead>
                <tbody>
                  {result.removed_features.map((rf, i) => (
                    <tr key={i} style={styles.tableRow}>
                      <td style={styles.td}><span style={{ color: '#c62828', fontWeight: 600 }}>{rf.feature_name}</span></td>
                      <td style={styles.td}>{rf.reason}</td>
                      <td style={styles.td}>{rf.source_feature_group || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* NEW: Feature Lineage */}
          {result.feature_lineage_map && Object.keys(result.feature_lineage_map).length > 0 && (
            <Section title="Feature Lineage">
              <table style={styles.smallTable}>
                <thead>
                  <tr>
                    <th style={styles.th}>Feature</th>
                    <th style={styles.th}>Imputed</th>
                    <th style={styles.th}>Scaled</th>
                    <th style={styles.th}>Transformed</th>
                    <th style={styles.th}>Selected</th>
                    <th style={styles.th}>Reduced</th>
                    <th style={styles.th}>Interpretable</th>
                    <th style={styles.th}>Removed</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.feature_lineage_map).map(([key, linfo]: [string, any]) => (
                    <tr key={key} style={{ ...styles.tableRow, opacity: linfo.removed ? 0.5 : 1 }}>
                      <td style={styles.td}>{key}</td>
                      <td style={styles.td}>{linfo.imputed ? <Badge label="Yes" color="#1565c0" /> : '—'}</td>
                      <td style={styles.td}>{linfo.scaled ? <Badge label="Yes" color="#ff9800" /> : '—'}</td>
                      <td style={styles.td}>{linfo.transformed ? <Badge label="Yes" color="#00838f" /> : '—'}</td>
                      <td style={styles.td}>{linfo.selected ? 'Yes' : <span style={{ color: '#c62828' }}>No</span>}</td>
                      <td style={styles.td}>{linfo.reduced ? <Badge label="Yes" color="#9e9e9e" /> : '—'}</td>
                      <td style={styles.td}>{linfo.is_interpretable ? 'Yes' : <span style={{ color: '#ff9800' }}>No</span>}</td>
                      <td style={styles.td}>{linfo.removed ? <span style={{ color: '#c62828' }}>Yes</span> : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {/* NEW: Explainability Report */}
          {result.explainability_preservation_report && (
            <Section title="Explainability Preservation">
              <div style={styles.grid2Col}>
                <div>
                  <strong>Original Features:</strong> {result.explainability_preservation_report.total_original_features}
                </div>
                <div>
                  <strong>Retained:</strong> {result.explainability_preservation_report.total_retained_features}
                </div>
                <div>
                  <strong>Interpretable:</strong> {result.explainability_preservation_report.total_interpretable_features}
                </div>
                <div>
                  <strong>Reduced:</strong> {result.explainability_preservation_report.total_reduced_features}
                </div>
                <div>
                  <strong>Score:</strong>{' '}
                  <span style={{
                    color: result.explainability_preservation_report.interpretability_score >= 0.8 ? '#2e7d32' :
                           result.explainability_preservation_report.interpretability_score >= 0.5 ? '#ff9800' : '#c62828',
                    fontWeight: 600,
                  }}>
                    {(result.explainability_preservation_report.interpretability_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
              {result.explainability_preservation_report.notes && result.explainability_preservation_report.notes.length > 0 && (
                <div style={{ marginTop: '4px', fontSize: '11px', color: '#555' }}>
                  {result.explainability_preservation_report.notes.map((n, i) => (
                    <div key={i}>• {n}</div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* NEW: Model-Ready Artifacts */}
          {result.model_ready_artifacts && result.model_ready_artifacts.length > 0 && (
            <Section title="Model-Ready Artifacts">
              {result.model_ready_artifacts.map((a, i) => (
                <div key={i} style={{ marginBottom: '6px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
                  <div><strong>Artifact ID:</strong> {a.artifact_id}</div>
                  <div><strong>Variant:</strong> {a.variant_name} | <strong>Usage:</strong> {a.usage}</div>
                  <div><strong>Path:</strong> {a.path}</div>
                  <div><strong>Samples:</strong> {a.row_count} | <strong>Features:</strong> {a.feature_count}</div>
                  <div style={{ fontSize: '10px', color: '#999' }}>Hash: {a.artifact_hash}</div>
                </div>
              ))}
            </Section>
          )}

          {/* NEW: Preprocessor Artifacts */}
          {result.preprocessor_artifacts && result.preprocessor_artifacts.length > 0 && (
            <Section title="Preprocessor Artifacts">
              {result.preprocessor_artifacts.map((a, i) => (
                <div key={i} style={{ marginBottom: '4px' }}>
                  <strong>{a.variant_name}:</strong> {a.artifact_id} (usage: {a.usage})
                </div>
              ))}
            </Section>
          )}

          {/* NEW: Provenance */}
          {result.preprocessing_provenance && (
            <Section title="Preprocessing Provenance">
              <div>
                <strong>Registry Snapshot:</strong>{' '}
                {result.preprocessing_provenance.registry_snapshot_version}
              </div>
              <div>
                <strong>Input Hash:</strong>{' '}
                {result.preprocessing_provenance.input_feature_artifact_hash}
              </div>
              <div>
                <strong>Output Hash:</strong>{' '}
                {result.preprocessing_provenance.output_artifact_hash}
              </div>
              {result.preprocessing_provenance.random_seed != null && (
                <div><strong>Random Seed:</strong> {result.preprocessing_provenance.random_seed}</div>
              )}
              {result.preprocessing_provenance.dependency_versions && Object.keys(result.preprocessing_provenance.dependency_versions).length > 0 && (
                <div style={{ fontSize: '11px', color: '#888' }}>
                  <strong>Dependencies:</strong> {JSON.stringify(result.preprocessing_provenance.dependency_versions)}
                </div>
              )}
              {result.preprocessing_provenance.created_at && (
                <div style={{ fontSize: '11px', color: '#888' }}>
                  Created: {result.preprocessing_provenance.created_at}
                </div>
              )}
            </Section>
          )}

          {/* NEW: Model Search Context Input */}
          {result.model_search_context_input && (
            <Section title="Model Search Context Input">
              <div>
                <strong>Ready for Model Search:</strong>{' '}
                <span style={{ color: result.model_search_context_input.model_ready_matrix_path ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.model_search_context_input.model_ready_matrix_path ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Default Variant: {result.model_search_context_input.default_variant_id || '—'}</div>
              {result.model_search_context_input.feature_summary && (
                <div style={{ fontSize: '11px', color: '#888' }}>
                  Summary: {JSON.stringify(result.model_search_context_input.feature_summary)}
                </div>
              )}
            </Section>
          )}

          {/* Model Ready Artifact (Legacy) */}
          {result.model_ready_artifact && (
            <Section title="Model Ready Artifact (Legacy)">
              <div>Artifact ID: {result.model_ready_artifact.artifact_id}</div>
              <div>Storage: {result.model_ready_artifact.storage_type}</div>
              <div>Samples: {result.model_ready_artifact.n_samples}</div>
              <div>Features: {result.model_ready_artifact.n_features}</div>
              <div>Target: {result.model_ready_artifact.target_column}</div>
            </Section>
          )}

          {/* Model Search Input (Legacy) */}
          {result.model_search_input && (
            <Section title="Model Search Input (Legacy)">
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
    marginTop: '24px', padding: '16px', backgroundColor: '#f3f4f6',
    border: '1px solid #9e9e9e', borderRadius: '8px',
  },
  title: { margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600, color: '#333' },
  description: { margin: '0 0 16px 0', fontSize: '14px', color: '#666' },
  buttonRow: { display: 'flex', gap: '12px', marginBottom: '16px' },
  runButton: {
    padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px', backgroundColor: '#6c757d', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  errorBox: {
    marginBottom: '16px', padding: '12px', backgroundColor: '#ffebee',
    border: '1px solid #f44336', borderRadius: '4px', color: '#c62828', fontSize: '14px',
  },
  resultBox: {
    padding: '16px', backgroundColor: '#e8f5e9', border: '1px solid #4caf50', borderRadius: '4px',
  },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  fieldRow: { display: 'flex', flexWrap: 'wrap', gap: '24px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  section: {
    marginTop: '12px', padding: '10px', backgroundColor: '#fff',
    borderRadius: '4px', border: '1px solid #e0e0e0',
  },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    cursor: 'pointer',
  },
  sectionTitle: {
    fontSize: '13px', fontWeight: 600, color: '#555',
    textTransform: 'uppercase' as const, display: 'block', marginBottom: '6px',
  },
  sectionContent: {
    fontSize: '13px', color: '#333', display: 'flex',
    flexDirection: 'column' as const, gap: '3px',
  },
  badge: {
    display: 'inline-block', color: '#fff', padding: '1px 8px',
    borderRadius: '10px', fontSize: '11px', marginLeft: '4px', marginBottom: '2px',
  },
  rationaleBox: {
    fontSize: '11px', color: '#777', padding: '4px 6px',
    backgroundColor: '#fafafa', borderRadius: '4px', display: 'flex',
    flexDirection: 'column', gap: '1px',
  },
  grid2Col: {
    display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2px 16px',
    fontSize: '12px',
  },
  smallTable: {
    width: '100%', borderCollapse: 'collapse', marginTop: '4px', fontSize: '11px',
  },
  th: {
    textAlign: 'left', padding: '4px 6px', borderBottom: '2px solid #e0e0e0',
    backgroundColor: '#f5f5f5', fontWeight: 600, fontSize: '11px',
  },
  tableRow: { borderBottom: '1px solid #f0f0f0' },
  td: { padding: '4px 6px', verticalAlign: 'top', fontSize: '11px' },
  warningSection: {
    marginTop: '12px', padding: '10px', backgroundColor: '#fff3e0',
    borderRadius: '4px', border: '1px solid #ffcc02', fontSize: '13px',
  },
  warningItem: { marginTop: '4px', marginLeft: '8px', fontSize: '12px' },
  errorSection: {
    marginTop: '12px', padding: '10px', backgroundColor: '#ffebee',
    borderRadius: '4px', border: '1px solid #f44336', fontSize: '13px',
  },
  errorItem: { marginTop: '4px', marginLeft: '8px', fontSize: '12px' },
  jsonSection: { marginTop: '16px' },
  pre: {
    backgroundColor: '#fff', padding: '12px', borderRadius: '4px',
    overflow: 'auto', fontSize: '12px', marginTop: '8px', maxHeight: '400px',
  },
};

export default FeaturePreprocessingPanel;
