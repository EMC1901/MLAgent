import React from 'react';
import {
  FeaturePreprocessingResponse,
  OperationResult,
  RemovedFeature,
  FeatureLineageEntry,
} from '../types';
import { ExecutionTabStyles as s } from './styles';

const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
  <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
);

interface ExecutionTabProps {
  result: FeaturePreprocessingResponse;
}

const ExecutionTab: React.FC<ExecutionTabProps> = ({ result }) => {
  const execOps: OperationResult[] = result.execution_report?.operation_results || [];
  const executedOps = execOps.filter((o) => o.status === 'success');
  const deferredOps = execOps.filter((o) => o.status === 'deferred_to_fold');
  const nDeferred: number =
    (result.model_search_context_input?.feature_summary?.n_deferred_fold_ops as number) ?? deferredOps.length;
  const foldSpecPath: string | null =
    (result.model_search_context_input?.available_variants?.[0] as Record<string, unknown>)?.fold_pipeline_spec_path as string ?? null;

  const getExecStatusColor = (status: string): string => {
    switch (status) {
      case 'success': return '#2e7d32';
      case 'failed': return '#c62828';
      case 'deferred_to_fold': return '#7b1fa2';
      default: return '#ff9800';
    }
  };

  const getExecStatusLabel = (status: string): string => {
    switch (status) {
      case 'deferred_to_fold': return 'Deferred (Fold-Safe)';
      case 'success': return 'Executed';
      default: return status;
    }
  };

  return (
    <div>
      {/* Two-Phase Execution Summary */}
      {execOps.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Two-Phase Execution Summary</h4>
          <div style={{ display: 'flex', gap: '12px', marginBottom: deferredOps.length > 0 ? '10px' : '0' }}>
            <div style={{ ...s.phaseBlock, backgroundColor: '#e3f2fd', borderColor: '#90caf9' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#1565c0', marginBottom: '4px' }}>
                Phase 1 &mdash; Global
              </div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#1565c0', lineHeight: 1.1, marginBottom: '2px' }}>
                {executedOps.length}
              </div>
              <div style={{ fontSize: '11px', color: '#555' }}>operations on full dataset</div>
              <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                Analysis &middot; Filtering &middot; Leakage Detection &middot; Correlation
              </div>
            </div>
            <div style={{ ...s.phaseBlock, backgroundColor: '#f3e5f5', borderColor: '#ce93d8' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#7b1fa2', marginBottom: '4px' }}>
                Phase 2 &mdash; Fold-Safe
              </div>
              <div style={{ fontSize: '28px', fontWeight: 700, color: '#7b1fa2', lineHeight: 1.1, marginBottom: '2px' }}>
                {nDeferred}
              </div>
              <div style={{ fontSize: '11px', color: '#555' }}>operations deferred per CV fold</div>
              <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
                Imputation &middot; Scaling &middot; Transforms &middot; Feature Selection &middot; PCA
              </div>
              {foldSpecPath && (
                <div style={{ fontSize: '10px', color: '#7b1fa2', marginTop: '6px', wordBreak: 'break-all' }}>
                  Spec: {foldSpecPath}
                </div>
              )}
            </div>
          </div>
          {deferredOps.length > 0 && (
            <div>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#555', marginBottom: '4px' }}>
                Deferred Fold Operations:
              </div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                {deferredOps.map((op, i) => (
                  <Badge key={i} label={op.capability_id} color="#7b1fa2" />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Execution Report Table */}
      {execOps.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Execution Report</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ ...s.table, minWidth: '800px' }}>
              <thead>
                <tr>
                  <th style={{ ...s.th, width: '18%' }}>Operation</th>
                  <th style={{ ...s.th, width: '18%' }}>Capability</th>
                  <th style={{ ...s.th, width: '14%' }}>Group</th>
                  <th style={{ ...s.th, width: '14%' }}>Status</th>
                  <th style={{ ...s.th, width: '8%' }}>Affected</th>
                  <th style={{ ...s.th, width: '8%' }}>Removed</th>
                  <th style={{ ...s.th, width: '20%' }}>Warnings</th>
                </tr>
              </thead>
              <tbody>
                {execOps.map((op, i) => {
                  const isDeferred = op.status === 'deferred_to_fold';
                  const statusColor = getExecStatusColor(op.status);
                  const statusLabel = getExecStatusLabel(op.status);
                  return (
                    <tr key={i} style={{
                      ...s.tableRow,
                      backgroundColor: isDeferred ? '#f3e5f5' : 'transparent',
                    }}>
                      <td style={s.td}>{op.operation_id}</td>
                      <td style={s.td}>
                        <Badge label={op.capability_id} color={isDeferred ? '#7b1fa2' : '#1976d2'} />
                      </td>
                      <td style={s.td}>{op.capability_group}</td>
                      <td style={s.td}>
                        <span style={{ color: statusColor, fontWeight: 600, fontSize: '12px' }}>
                          {statusLabel}
                        </span>
                      </td>
                      <td style={s.td}>{op.affected_features.length}</td>
                      <td style={s.td}>{op.removed_features.length}</td>
                      <td style={s.td}>
                        {op.warnings && op.warnings.length > 0 && (
                          <span style={{ color: '#e65100', fontSize: '11px' }}>
                            {op.warnings.length} warning(s)
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '2px solid #e0e0e0', fontWeight: 600, fontSize: '12px' }}>
                  <td style={{ ...s.td, paddingTop: '8px' }} colSpan={4}>
                    <span style={{ color: '#2e7d32' }}>
                      Executed: {execOps.filter((o) => o.status === 'success').length}
                    </span>
                    {' | '}
                    <span style={{ color: '#7b1fa2' }}>
                      Deferred: {execOps.filter((o) => o.status === 'deferred_to_fold').length}
                    </span>
                    {' | '}
                    <span style={{ color: '#c62828' }}>
                      Failed: {execOps.filter((o) => o.status === 'failed').length}
                    </span>
                  </td>
                  <td style={{ ...s.td, paddingTop: '8px' }} colSpan={3}>
                    Total: {execOps.length} ops
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Validation Summary */}
      {result.validation_summary && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Validation Summary</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Model Ready:</strong>{' '}
              <span style={{ color: result.validation_summary.is_model_ready ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.validation_summary.is_model_ready ? 'Yes' : 'No'}
              </span>
            </div>
            <div style={s.field}><strong>Samples:</strong> {result.validation_summary.n_samples}</div>
            <div style={s.field}><strong>Raw Features:</strong> {result.validation_summary.n_raw_features}</div>
            <div style={s.field}><strong>Valid Before:</strong> {result.validation_summary.n_valid_features_before_preprocessing}</div>
            <div style={s.field}><strong>After Preprocessing:</strong> {result.validation_summary.n_features_after_preprocessing}</div>
            <div style={s.field}><strong>Dropped:</strong> {result.validation_summary.n_dropped_features}</div>
            <div style={s.field}><strong>Target:</strong> {result.validation_summary.target_column || '—'}</div>
            <div style={s.field}><strong>Task Type:</strong> {result.validation_summary.task_type || '—'}</div>
          </div>
        </div>
      )}

      {/* Column Filtering */}
      {result.column_validation && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Column Filtering</h4>
          {result.column_validation.retained_features && result.column_validation.retained_features.length > 0 && (
            <div style={s.field}><strong>Retained:</strong> {result.column_validation.retained_features.length} features</div>
          )}
          {result.column_validation.dropped_invalid_features && result.column_validation.dropped_invalid_features.length > 0 && (
            <div style={s.field}>
              <strong>Invalid Features:</strong>{' '}
              {result.column_validation.dropped_invalid_features.map((f, i) => (
                <Badge key={i} label={f.name} color="#c62828" />
              ))}
            </div>
          )}
          {result.column_validation.dropped_all_missing_features && result.column_validation.dropped_all_missing_features.length > 0 && (
            <div style={s.field}>
              <strong>All-Missing:</strong>{' '}
              {result.column_validation.dropped_all_missing_features.map((f, i) => (
                <Badge key={i} label={f.name} color="#c62828" />
              ))}
            </div>
          )}
          {result.column_validation.dropped_constant_features && result.column_validation.dropped_constant_features.length > 0 && (
            <div style={s.field}>
              <strong>Constant:</strong>{' '}
              {result.column_validation.dropped_constant_features.map((f, i) => (
                <Badge key={i} label={f.name} color="#ff9800" />
              ))}
            </div>
          )}
          {result.column_validation.dropped_high_missing_features && result.column_validation.dropped_high_missing_features.length > 0 && (
            <div style={s.field}>
              <strong>High-Missing:</strong>{' '}
              {result.column_validation.dropped_high_missing_features.map((f, i) => (
                <Badge key={i} label={f.name} color="#ff9800" />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Feature Group Validation */}
      {result.feature_group_validation && result.feature_group_validation.groups && result.feature_group_validation.groups.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Group Validation</h4>
          {result.feature_group_validation.groups.map((g, i) => (
            <div key={i} style={{ marginBottom: '4px', fontSize: '13px' }}>
              <strong>{g.group_name}:</strong>{' '}
              <span style={{ color: g.status === 'retained' ? '#2e7d32' : g.status === 'dropped' ? '#c62828' : '#ff9800', fontWeight: 600 }}>
                {g.status}
              </span>
              {' '}({g.n_valid_features}/{g.n_raw_features} valid)
              {g.reason && <span style={{ fontSize: '11px', color: '#888' }}> — {g.reason}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Preprocessing Execution */}
      {result.preprocessing_execution && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Preprocessing Execution</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Imputation:</strong>{' '}
              {result.preprocessing_execution.imputation.executed
                ? (
                  <span>
                    <Badge label={`Executed (${result.preprocessing_execution.imputation.strategy})`} color="#2e7d32" />
                    {result.preprocessing_execution.imputation.execution_mode === 'fold_safe' && (
                      <Badge label="Fold-Safe" color="#7b1fa2" />
                    )}
                  </span>
                )
                : <Badge label="Not Executed" color="#9e9e9e" />}
            </div>
            <div style={s.field}>
              <strong>Scaling:</strong>{' '}
              {result.preprocessing_execution.scaling.executed
                ? (
                  <span>
                    <Badge label={`Executed (${result.preprocessing_execution.scaling.strategy})`} color="#2e7d32" />
                    {result.preprocessing_execution.scaling.execution_mode === 'fold_safe' && (
                      <Badge label="Fold-Safe" color="#7b1fa2" />
                    )}
                  </span>
                )
                : <Badge label="Not Executed" color="#9e9e9e" />}
            </div>
            <div style={s.field}>
              <strong>Categorical Encoding:</strong>{' '}
              {result.preprocessing_execution.categorical_encoding.executed
                ? <Badge label="Executed" color="#2e7d32" />
                : <Badge label="None" color="#9e9e9e" />}
            </div>
            <div style={s.field}>
              <strong>Feature Selection:</strong>{' '}
              {result.preprocessing_execution.feature_selection.executed
                ? (
                  <span>
                    <Badge label={`Executed (${result.preprocessing_execution.feature_selection.strategy})${result.preprocessing_execution.feature_selection.columns_dropped.length > 0 ? ` - ${result.preprocessing_execution.feature_selection.columns_dropped.length} dropped` : ''}`} color="#2e7d32" />
                    {result.preprocessing_execution.feature_selection.execution_mode === 'fold_safe' && (
                      <Badge label="Fold-Safe" color="#7b1fa2" />
                    )}
                  </span>
                )
                : <Badge label="None" color="#9e9e9e" />}
            </div>
          </div>
          {/* Fold-Safe Deferred Summary */}
          {result.preprocessing_execution.fold_safe_deferred?.has_deferred && (
            <div style={{ marginTop: '10px', padding: '8px 12px', backgroundColor: '#f3e5f5', borderRadius: '6px', border: '1px solid #ce93d8' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#7b1fa2', marginBottom: '4px' }}>
                Fold-Safe Deferred ({result.preprocessing_execution.fold_safe_deferred.n_deferred_operations} ops)
              </div>
              {result.preprocessing_execution.fold_safe_deferred.operations_by_group && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                  {Object.entries(result.preprocessing_execution.fold_safe_deferred.operations_by_group).map(([group, ops]) => (
                    <span key={group} style={{ fontSize: '11px', color: '#555' }}>
                      <strong>{group}:</strong> {(ops as string[]).join(', ')}
                    </span>
                  ))}
                </div>
              )}
              {result.preprocessing_execution.fold_safe_deferred.fold_spec_path && (
                <div style={{ fontSize: '10px', color: '#999', marginTop: '4px', wordBreak: 'break-all' }}>
                  Spec: {result.preprocessing_execution.fold_safe_deferred.fold_spec_path}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Removed Features */}
      {(result.removed_features && result.removed_features.length > 0) && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Removed Features ({result.removed_features.length})</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ ...s.table, minWidth: '500px' }}>
              <thead>
                <tr>
                  <th style={s.th}>Feature</th>
                  <th style={s.th}>Reason</th>
                  <th style={s.th}>Source Group</th>
                </tr>
              </thead>
              <tbody>
                {result.removed_features.map((rf: RemovedFeature, i: number) => (
                  <tr key={i} style={s.tableRow}>
                    <td style={s.td}><span style={{ color: '#c62828', fontWeight: 600 }}>{rf.feature_name}</span></td>
                    <td style={s.td}>{rf.reason}</td>
                    <td style={s.td}>{rf.source_feature_group || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Feature Lineage */}
      {result.feature_lineage_map && Object.keys(result.feature_lineage_map).length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Lineage</h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ ...s.table, minWidth: '700px' }}>
              <thead>
                <tr>
                  <th style={s.th}>Feature</th>
                  <th style={s.th}>Imputed</th>
                  <th style={s.th}>Scaled</th>
                  <th style={s.th}>Transformed</th>
                  <th style={s.th}>Selected</th>
                  <th style={s.th}>Reduced</th>
                  <th style={s.th}>Interpretable</th>
                  <th style={s.th}>Removed</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.feature_lineage_map).map(([key, linfo]) => {
                  const info = linfo as FeatureLineageEntry;
                  return (
                    <tr key={key} style={{ ...s.tableRow, opacity: info.removed ? 0.5 : 1 }}>
                      <td style={s.td}>{key}</td>
                      <td style={s.td}>{info.imputed ? <Badge label="Yes" color="#1565c0" /> : '—'}</td>
                      <td style={s.td}>{info.scaled ? <Badge label="Yes" color="#ff9800" /> : '—'}</td>
                      <td style={s.td}>{info.transformed ? <Badge label="Yes" color="#00838f" /> : '—'}</td>
                      <td style={s.td}>{info.selected ? 'Yes' : <span style={{ color: '#c62828' }}>No</span>}</td>
                      <td style={s.td}>{info.reduced ? <Badge label="Yes" color="#9e9e9e" /> : '—'}</td>
                      <td style={s.td}>{info.is_interpretable ? 'Yes' : <span style={{ color: '#ff9800' }}>No</span>}</td>
                      <td style={s.td}>{info.removed ? <span style={{ color: '#c62828' }}>Yes</span> : '—'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Explainability */}
      {result.explainability_preservation_report && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Explainability Preservation</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Original Features:</strong> {result.explainability_preservation_report.total_original_features}</div>
            <div style={s.field}><strong>Retained:</strong> {result.explainability_preservation_report.total_retained_features}</div>
            <div style={s.field}><strong>Interpretable:</strong> {result.explainability_preservation_report.total_interpretable_features}</div>
            <div style={s.field}><strong>Reduced:</strong> {result.explainability_preservation_report.total_reduced_features}</div>
            <div style={s.field}>
              <strong>Score:</strong>{' '}
              <span style={{
                color: (result.explainability_preservation_report.interpretability_score ?? 0) >= 0.8 ? '#2e7d32' :
                       (result.explainability_preservation_report.interpretability_score ?? 0) >= 0.5 ? '#ff9800' : '#c62828',
                fontWeight: 600,
              }}>
                {((result.explainability_preservation_report.interpretability_score ?? 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Model Ready Artifact (Legacy) */}
      {result.model_ready_artifact && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Model Ready Artifact (Legacy)</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Artifact ID:</strong> {result.model_ready_artifact.artifact_id || '—'}</div>
            <div style={s.field}><strong>Storage:</strong> {result.model_ready_artifact.storage_type}</div>
            <div style={s.field}><strong>Samples:</strong> {result.model_ready_artifact.n_samples}</div>
            <div style={s.field}><strong>Features:</strong> {result.model_ready_artifact.n_features}</div>
            <div style={s.field}><strong>Target:</strong> {result.model_ready_artifact.target_column || '—'}</div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExecutionTab;
