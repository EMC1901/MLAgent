import React, { useState } from 'react';
import { createFeatureEngineering, rerunFeatureEngineering } from '../../../api/featureEngineeringApi';
import { FeatureEngineeringResponse, PerFeatureSummary } from '../types';

interface FeatureEngineeringPanelProps {
  taskId: string;
  initialResult?: FeatureEngineeringResponse;
}

const FeatureEngineeringPanel: React.FC<FeatureEngineeringPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FeatureEngineeringResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await createFeatureEngineering(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run feature engineering.');
    } finally { setLoading(false); }
  };

  const handleRerun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await rerunFeatureEngineering(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run feature engineering.');
    } finally { setLoading(false); }
  };

  const getStatusColor = (status: string) => {
    switch (status) { case 'completed': return '#4caf50'; case 'completed_with_warning': return '#ff9800'; case 'failed': return '#f44336'; default: return '#9e9e9e'; }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const renderSummary = () => (
    <div>
      {result?.feature_generation && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Generation</h4>
          {result.feature_generation.selected_featurizers?.length > 0 && (
            <div style={s.field}><strong>Selected:</strong>{' '}
              {result.feature_generation.selected_featurizers.map((f, i) => <Badge key={i} label={f} color="#2e7d32" />)}</div>
          )}
          {result.feature_generation.semantic_featurizers?.length > 0 && (
            <div style={s.field}><strong>Semantic:</strong>{' '}
              {result.feature_generation.semantic_featurizers.map((f, i) => <Badge key={i} label={f} color="#1565c0" />)}</div>
          )}
          {result.feature_generation.fallback_featurizers?.length > 0 && (
            <div style={s.field}><strong>Fallback:</strong>{' '}
              {result.feature_generation.fallback_featurizers.map((f, i) => <Badge key={i} label={f} color="#ff9800" />)}</div>
          )}
          {result.feature_generation.executed_featurizers?.map((ef, i) => (
            <div key={i} style={{ marginTop: '4px', fontSize: '13px' }}>
              <strong>{ef.display_name || ef.name}:</strong>{' '}
              <span style={{ color: ef.status === 'success' ? '#2e7d32' : ef.status === 'failed' ? '#c62828' : '#ff9800' }}>{ef.status}</span>
              {' '}({ef.n_features_generated} features, {ef.failed_sample_count} failed{ef.execution_time_ms != null ? `, ${ef.execution_time_ms}ms` : ''})
            </div>
          ))}
        </div>
      )}

      {result?.feature_matrix && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Matrix</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Samples:</strong> {result.feature_matrix.n_samples}</div>
            <div style={s.field}><strong>Features:</strong> {result.feature_matrix.n_features}</div>
            <div style={s.field}><strong>Target Column:</strong> {result.feature_matrix.target_column}</div>
            <div style={s.field}><strong>Artifact ID:</strong> {result.feature_matrix.artifact_id}</div>
          </div>
        </div>
      )}

      {result?.feature_schema && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Schema</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Numeric:</strong> {result.feature_schema.numeric_feature_count}</div>
            <div style={s.field}><strong>Categorical:</strong> {result.feature_schema.categorical_feature_count}</div>
            <div style={s.field}><strong>Constant:</strong> {result.feature_schema.constant_feature_count}</div>
            <div style={s.field}><strong>All-missing:</strong> {result.feature_schema.all_missing_feature_count}</div>
          </div>
          {result.feature_schema.feature_groups?.length > 0 && (
            <div style={s.subCard}><strong>Feature Groups:</strong>
              {result.feature_schema.feature_groups.map((g, i) => (
                <div key={i} style={{ fontSize: '12px' }}><strong>{g.group_name}:</strong>{' '}
                  <span style={{ color: g.status === 'success' ? '#2e7d32' : '#9e9e9e' }}>{g.status}</span> ({g.n_features} features)</div>
              ))}</div>
          )}
        </div>
      )}
    </div>
  );

  const renderQuality = () => (
    <div>
      {result?.feature_quality && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Quality</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Valid Matrix:</strong> {result.feature_quality.is_valid_feature_matrix ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Total Missing:</strong> {result.feature_quality.missing_values?.total_missing}</div>
          </div>
          {result.feature_quality.dropped_features?.length > 0 && <div style={s.field}><strong>Dropped:</strong> {result.feature_quality.dropped_features.join(', ')}</div>}
          {result.feature_quality.constant_features?.length > 0 && <div style={s.field}><strong>Constant:</strong> {result.feature_quality.constant_features.join(', ')}</div>}
        </div>
      )}

      {result?.feature_quality_profile && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Quality Profile</h4>
          {result.feature_quality_profile.global_summary && (
            <div style={s.subCard}>
              <strong>Global Summary:</strong>
              <div style={{ ...s.grid, fontSize: '12px' }}>
                <div>Rows: {result.feature_quality_profile.global_summary.row_count}</div>
                <div>Features: {result.feature_quality_profile.global_summary.feature_count}</div>
                <div>Numeric: {result.feature_quality_profile.global_summary.numeric_feature_count}</div>
                <div>Categorical: {result.feature_quality_profile.global_summary.categorical_feature_count}</div>
                <div>Missing Ratio: {(result.feature_quality_profile.global_summary.missing_value_ratio * 100).toFixed(2)}%</div>
                <div>Constant: {result.feature_quality_profile.global_summary.constant_feature_count}</div>
                <div>Near-Constant: {result.feature_quality_profile.global_summary.near_constant_feature_count}</div>
                <div>Low Info: {result.feature_quality_profile.global_summary.low_information_feature_count}</div>
                <div>High Missing: {result.feature_quality_profile.global_summary.high_missing_feature_count}</div>
                <div>High Skewness: {result.feature_quality_profile.global_summary.high_skewness_feature_count}</div>
                <div>High Corr Pairs: {result.feature_quality_profile.global_summary.high_correlation_pair_count}</div>
              </div>
            </div>
          )}
          {result.feature_quality_profile.per_feature_summary?.length > 0 && (
            <div style={s.subCard}>
              <strong>Per-Feature Summary ({result.feature_quality_profile.per_feature_summary.length}):</strong>
              <table style={{ ...s.innerTable, marginTop: '8px' }}>
                <thead><tr><th style={s.th}>Feature</th><th style={s.th}>Type</th><th style={s.th}>Missing%</th><th style={s.th}>Variance</th><th style={s.th}>Skewness</th><th style={s.th}>Group</th></tr></thead>
                <tbody>
                  {result.feature_quality_profile.per_feature_summary.slice(0, 50).map((f: PerFeatureSummary, i: number) => (
                    <tr key={i}>
                      <td style={s.td}>{f.feature_name}</td><td style={s.td}>{f.dtype}</td>
                      <td style={s.td}>{f.missing_ratio != null ? (f.missing_ratio * 100).toFixed(1) + '%' : '—'}</td>
                      <td style={s.td}>{f.variance != null ? f.variance.toExponential(2) : '—'}</td>
                      <td style={s.td}>{f.skewness != null ? f.skewness.toFixed(2) : '—'}</td>
                      <td style={s.td}>{f.source_feature_group}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {result.feature_quality_profile.quality_warnings?.length > 0 && (
            <div style={s.warningBox}><strong>Quality Warnings:</strong>
              <ul style={s.list}>{result.feature_quality_profile.quality_warnings.map((w, i) => <li key={i}>[{w.severity}] {w.message}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderExecutionAndDownstream = () => (
    <div>
      {(result?.execution_report?.action_results?.length ?? 0) > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Execution Report</h4>
          <table style={{ ...s.innerTable, tableLayout: 'fixed' }}>
            <thead><tr><th style={s.th}>Action</th><th style={s.th}>Capability</th><th style={s.th}>Status</th><th style={s.th}>Features</th><th style={s.th}>Error</th></tr></thead>
            <tbody>
              {result?.execution_report?.action_results?.map((a, i) => (
                <tr key={i}>
                  <td style={s.td}>{a.action_id}</td>
                  <td style={s.td}><Badge label={a.capability_id} color="#1976d2" /></td>
                  <td style={s.td}><span style={{ color: a.status === 'success' ? '#2e7d32' : a.status === 'failed' ? '#c62828' : '#ff9800', fontWeight: 600 }}>{a.status}</span></td>
                  <td style={s.td}>{a.generated_feature_count}</td>
                  <td style={s.td}>{a.error_message || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {result?.feature_preprocessing_decision_input && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Preprocessing Decision Input</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Task Type:</strong> {(result.feature_preprocessing_decision_input.task_context as any)?.task_type || '—'}</div>
            <div style={s.field}><strong>Dataset:</strong> {(result.feature_preprocessing_decision_input.dataset_context as any)?.row_count || 0} rows</div>
            <div style={s.field}><strong>Feature Matrix:</strong> {(result.feature_preprocessing_decision_input.feature_matrix_context as any)?.feature_count || 0} features</div>
          </div>
        </div>
      )}

      {result?.preprocessing_requirements && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Preprocessing Requirements</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Scaling:</strong> {result.preprocessing_requirements.scaling_required ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Imputation:</strong> {result.preprocessing_requirements.imputation_required ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Feature Selection:</strong> {result.preprocessing_requirements.feature_selection_required ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}

      {result?.downstream_input && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Downstream Input</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Ready for Pipeline Gen:</strong> {result.downstream_input.ready_for_pipeline_generation ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Task Type:</strong> {result.downstream_input.task_type}</div>
            <div style={s.field}><strong>Primary Metric:</strong> {result.downstream_input.primary_metric}</div>
            <div style={s.field}><strong>Target Column:</strong> {result.downstream_input.target_column}</div>
            <div style={s.field}><strong>Feature Count:</strong> {result.downstream_input.feature_columns?.length}</div>
          </div>
        </div>
      )}
    </div>
  );

  const renderTab = (tabId: string, label: string) => (
    <button key={tabId} onClick={() => setActiveTab(tabId)} style={{
      ...s.tabButton,
      backgroundColor: activeTab === tabId ? '#1976d2' : '#e0e0e0',
      color: activeTab === tabId ? '#fff' : '#333',
    }}>{label}</button>
  );

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'quality', label: 'Feature Quality' },
    { id: 'execution', label: 'Execution & Downstream' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Automated Feature Engineering</h3>
      <p style={s.description}>
        Convert raw material input into ML-ready feature matrices based on the
        workflow plan&rsquo;s feature strategy.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Running...' : 'Run Feature Engineering'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Feature Engineering'}
        </button>
      </div>

      {error && <div style={s.errorBox}><strong>Error:</strong> {error}</div>}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Feature Engineering Result</h4>

          <div style={s.fieldRow}>
            <div style={s.field}><strong>FE ID:</strong> {result.feature_engineering_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={result.status} color={getStatusColor(result.status)} />
            </div>
            <div style={s.field}><strong>Input Modality:</strong> {result.input_modality}</div>
            <div style={s.field}><strong>Feature Type:</strong> {result.feature_type}</div>
            {result.executed_feature_strategy_id && <div style={s.field}><strong>Feat Strategy:</strong> {result.executed_feature_strategy_id}</div>}
          </div>

          {result.warnings?.length > 0 && (
            <div style={s.warningBox}><strong>Warnings:</strong>
              <ul style={s.list}>{result.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}

          {result.errors?.length > 0 && (
            <div style={s.errorBox}><strong>Errors:</strong>
              <ul style={s.list}>{result.errors.map((e, i) => <li key={i}>{e}</li>)}</ul>
            </div>
          )}

          <div style={s.tabBar}>{tabs.map(t => renderTab(t.id, t.label))}</div>

          <div style={s.tabContent}>
            {activeTab === 'summary' && renderSummary()}
            {activeTab === 'quality' && renderQuality()}
            {activeTab === 'execution' && renderExecutionAndDownstream()}
            {activeTab === 'json' && (
              <div style={s.card}><h4 style={s.cardTitle}>Full JSON</h4><pre style={s.json}>{JSON.stringify(result, null, 2)}</pre></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: { marginTop: '24px', padding: '16px', border: '1px solid #e0e0e0', borderRadius: '8px', backgroundColor: '#fafafa' },
  title: { margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600 },
  description: { margin: '0 0 16px 0', color: '#666', fontSize: '13px', lineHeight: 1.5 },
  buttonRow: { display: 'flex', gap: '8px', marginBottom: '16px' },
  runButton: { padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' },
  rerunButton: { padding: '10px 20px', backgroundColor: '#f57c00', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' },
  errorBox: { padding: '12px', backgroundColor: '#ffebee', border: '1px solid #f44336', borderRadius: '4px', color: '#c62828', marginBottom: '16px' },
  resultBox: { padding: '16px', backgroundColor: '#fff', border: '1px solid #e0e0e0', borderRadius: '8px' },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  fieldRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  badge: { display: 'inline-block', padding: '2px 8px', borderRadius: '12px', color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px' },
  warningBox: { padding: '12px', backgroundColor: '#fff3e0', border: '1px solid #ff9800', borderRadius: '4px', color: '#e65100', marginBottom: '16px' },
  list: { margin: '4px 0', paddingLeft: '20px' },
  tabBar: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' },
  tabButton: { padding: '6px 14px', border: 'none', borderRadius: '16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' },
  tabContent: { minHeight: '200px', maxHeight: '60vh', overflowY: 'auto' as const },
  card: { padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px', marginBottom: '12px', border: '1px solid #e0e0e0', overflowX: 'auto' as const },
  subCard: { padding: '10px', backgroundColor: '#fff', borderRadius: '4px', marginBottom: '8px', border: '1px solid #eee', marginTop: '8px', overflowX: 'auto' as const },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  innerTable: { width: '100%', borderCollapse: 'collapse' as const, fontSize: '12px' },
  th: { textAlign: 'left' as const, padding: '6px 8px', borderBottom: '2px solid #e0e0e0', fontWeight: 600, backgroundColor: '#fafafa', whiteSpace: 'nowrap' as const, fontSize: '12px' },
  td: { padding: '6px 8px', borderBottom: '1px solid #eee', verticalAlign: 'top' as const, wordBreak: 'break-word' as const, fontSize: '12px' },
  json: { backgroundColor: '#263238', color: '#aed581', padding: '12px', borderRadius: '4px', overflow: 'auto', fontSize: '11px' },
};

export default FeatureEngineeringPanel;
