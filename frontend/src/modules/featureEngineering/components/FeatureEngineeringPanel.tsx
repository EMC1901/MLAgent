import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Table } from 'antd';
import { createFeatureEngineering, rerunFeatureEngineering } from '../../../api/featureEngineeringApi';
import { FeatureEngineeringResponse, PerFeatureSummary } from '../types';
import {
  PanelContainer, StatusBadge, WarningBox, ErrorBox,
  JsonViewer, EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface FeatureEngineeringPanelProps {
  taskId: string;
  initialResult?: FeatureEngineeringResponse;
}

const STATUS_COLORS: Record<string, string> = {
  completed: 'success', completed_with_warning: 'warning', failed: 'error',
};

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

  const execColumns = [
    { title: 'Action', dataIndex: 'action_id', key: 'action' },
    { title: 'Capability', dataIndex: 'capability_id', key: 'capability', render: (v: string) => <StatusBadge label={v} /> },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v: string) => <span style={{ color: v === 'success' ? '#2e7d32' : v === 'failed' ? '#c62828' : '#ff9800', fontWeight: 600 }}>{v}</span> },
    { title: 'Features', dataIndex: 'generated_feature_count', key: 'features' },
    { title: 'Error', dataIndex: 'error_message', key: 'error', render: (v: string) => v || '—' },
  ];

  const perFeatureColumns = [
    { title: 'Feature', dataIndex: 'feature_name', key: 'name' },
    { title: 'Type', dataIndex: 'dtype', key: 'dtype' },
    { title: 'Missing%', dataIndex: 'missing_ratio', key: 'missing', render: (v: number) => v != null ? `${(v * 100).toFixed(1)}%` : '—' },
    { title: 'Variance', dataIndex: 'variance', key: 'var', render: (v: number) => v != null ? v.toExponential(2) : '—' },
    { title: 'Skewness', dataIndex: 'skewness', key: 'skew', render: (v: number) => v != null ? v.toFixed(2) : '—' },
    { title: 'Group', dataIndex: 'source_feature_group', key: 'group' },
  ];

  const tabItems = [
    {
      key: 'summary', label: 'Summary',
      children: result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {result.feature_generation && (
            <Card size="small" title="Feature Generation">
              {result.feature_generation.selected_featurizers?.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <strong>Selected: </strong>
                  <Space wrap size={[4, 4]}>
                    {result.feature_generation.selected_featurizers.map((f, i) => <StatusBadge key={i} label={f} color="success" />)}
                  </Space>
                </div>
              )}
              {result.feature_generation.semantic_featurizers?.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <strong>Semantic: </strong>
                  <Space wrap size={[4, 4]}>
                    {result.feature_generation.semantic_featurizers.map((f, i) => <StatusBadge key={i} label={f} color="#1565c0" />)}
                  </Space>
                </div>
              )}
              {result.feature_generation.fallback_featurizers?.length > 0 && (
                <div style={{ marginBottom: 8 }}>
                  <strong>Fallback: </strong>
                  <Space wrap size={[4, 4]}>
                    {result.feature_generation.fallback_featurizers.map((f, i) => <StatusBadge key={i} label={f} color="warning" />)}
                  </Space>
                </div>
              )}
              {result.feature_generation.executed_featurizers?.map((ef, i) => (
                <div key={i} style={{ fontSize: 13, marginTop: 4 }}>
                  <strong>{ef.display_name || ef.name}:</strong>{' '}
                  <span style={{ color: ef.status === 'success' ? '#2e7d32' : ef.status === 'failed' ? '#c62828' : '#ff9800' }}>{ef.status}</span>
                  {' '}({ef.n_features_generated} features, {ef.failed_sample_count} failed{ef.execution_time_ms != null ? `, ${ef.execution_time_ms}ms` : ''})
                </div>
              ))}
            </Card>
          )}
          {result.feature_matrix && (
            <Card size="small" title="Feature Matrix">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Samples">{result.feature_matrix.n_samples}</Descriptions.Item>
                <Descriptions.Item label="Features">{result.feature_matrix.n_features}</Descriptions.Item>
                <Descriptions.Item label="Target Column">{result.feature_matrix.target_column}</Descriptions.Item>
                <Descriptions.Item label="Artifact ID">{result.feature_matrix.artifact_id}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
          {result.feature_schema && (
            <Card size="small" title="Feature Schema">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Numeric">{result.feature_schema.numeric_feature_count}</Descriptions.Item>
                <Descriptions.Item label="Categorical">{result.feature_schema.categorical_feature_count}</Descriptions.Item>
                <Descriptions.Item label="Constant">{result.feature_schema.constant_feature_count}</Descriptions.Item>
                <Descriptions.Item label="All-missing">{result.feature_schema.all_missing_feature_count}</Descriptions.Item>
              </Descriptions>
              {result.feature_schema.feature_groups?.length > 0 && (
                <Card size="small" style={{ marginTop: 8 }}>
                  <strong>Feature Groups:</strong>
                  {result.feature_schema.feature_groups.map((g, i) => (
                    <div key={i} style={{ fontSize: 12 }}>
                      <strong>{g.group_name}:</strong>{' '}
                      <span style={{ color: g.status === 'success' ? '#2e7d32' : '#9e9e9e' }}>{g.status}</span> ({g.n_features} features)
                    </div>
                  ))}
                </Card>
              )}
            </Card>
          )}
        </Space>
      ) : <EmptyState description="Run feature engineering to see summary." />,
    },
    {
      key: 'quality', label: 'Feature Quality',
      children: result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {result.feature_quality && (
            <Card size="small" title="Feature Quality">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Valid Matrix">{result.feature_quality.is_valid_feature_matrix ? 'Yes' : 'No'}</Descriptions.Item>
                <Descriptions.Item label="Total Missing">{result.feature_quality.missing_values?.total_missing}</Descriptions.Item>
              </Descriptions>
              {result.feature_quality.dropped_features?.length > 0 && <p><strong>Dropped:</strong> {result.feature_quality.dropped_features.join(', ')}</p>}
              {result.feature_quality.constant_features?.length > 0 && <p><strong>Constant:</strong> {result.feature_quality.constant_features.join(', ')}</p>}
            </Card>
          )}
          {result.feature_quality_profile && (
            <Card size="small" title="Quality Profile">
              {result.feature_quality_profile.global_summary && (
                <Card size="small" style={{ marginBottom: 8 }}>
                  <strong>Global Summary:</strong>
                  <Descriptions column={3} size="small" style={{ marginTop: 8 }}>
                    <Descriptions.Item label="Rows">{result.feature_quality_profile.global_summary.row_count}</Descriptions.Item>
                    <Descriptions.Item label="Features">{result.feature_quality_profile.global_summary.feature_count}</Descriptions.Item>
                    <Descriptions.Item label="Numeric">{result.feature_quality_profile.global_summary.numeric_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="Categorical">{result.feature_quality_profile.global_summary.categorical_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="Missing Ratio">{(result.feature_quality_profile.global_summary.missing_value_ratio * 100).toFixed(2)}%</Descriptions.Item>
                    <Descriptions.Item label="Constant">{result.feature_quality_profile.global_summary.constant_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="Near-Constant">{result.feature_quality_profile.global_summary.near_constant_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="Low Info">{result.feature_quality_profile.global_summary.low_information_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="High Missing">{result.feature_quality_profile.global_summary.high_missing_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="High Skew">{result.feature_quality_profile.global_summary.high_skewness_feature_count}</Descriptions.Item>
                    <Descriptions.Item label="High Corr Pairs">{result.feature_quality_profile.global_summary.high_correlation_pair_count}</Descriptions.Item>
                  </Descriptions>
                </Card>
              )}
              {result.feature_quality_profile.per_feature_summary?.length > 0 && (
                <Card size="small" title={`Per-Feature Summary (${result.feature_quality_profile.per_feature_summary.length})`}>
                  <Table<PerFeatureSummary>
                    dataSource={result.feature_quality_profile.per_feature_summary.slice(0, 50).map((f, i) => ({ ...f, key: i }))}
                    columns={perFeatureColumns} size="small" pagination={false}
                  />
                </Card>
              )}
              {result.feature_quality_profile.quality_warnings?.length > 0 && (
                <WarningBox warnings={result.feature_quality_profile.quality_warnings.map(w => `[${w.severity}] ${w.message}`)} style={{ marginTop: 8, marginBottom: 0 }} />
              )}
            </Card>
          )}
        </Space>
      ) : <EmptyState description="Run feature engineering to see quality data." />,
    },
    {
      key: 'execution', label: 'Execution & Downstream',
      children: result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {(result.execution_report?.action_results?.length ?? 0) > 0 && (
            <Card size="small" title="Execution Report">
              <Table dataSource={result.execution_report!.action_results!.map((a, i) => ({ ...a, key: i }))} columns={execColumns} size="small" pagination={false} />
            </Card>
          )}
          {result.preprocessing_requirements && (
            <Card size="small" title="Preprocessing Requirements">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Scaling">{result.preprocessing_requirements.scaling_required ? 'Yes' : 'No'}</Descriptions.Item>
                <Descriptions.Item label="Imputation">{result.preprocessing_requirements.imputation_required ? 'Yes' : 'No'}</Descriptions.Item>
                <Descriptions.Item label="Feature Selection">{result.preprocessing_requirements.feature_selection_required ? 'Yes' : 'No'}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
          {result.downstream_input && (
            <Card size="small" title="Downstream Input">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Ready for Pipeline Gen">{result.downstream_input.ready_for_pipeline_generation ? 'Yes' : 'No'}</Descriptions.Item>
                <Descriptions.Item label="Task Type">{result.downstream_input.task_type}</Descriptions.Item>
                <Descriptions.Item label="Primary Metric">{result.downstream_input.primary_metric}</Descriptions.Item>
                <Descriptions.Item label="Target Column">{result.downstream_input.target_column}</Descriptions.Item>
                <Descriptions.Item label="Feature Count">{result.downstream_input.feature_columns?.length}</Descriptions.Item>
              </Descriptions>
            </Card>
          )}
        </Space>
      ) : <EmptyState description="Run feature engineering to see execution data." />,
    },
    {
      key: 'json', label: 'Full JSON',
      children: result ? <JsonViewer data={result} /> : <EmptyState description="Run feature engineering to see JSON output." />,
    },
  ];

  return (
    <PanelContainer
      title="Automated Feature Engineering"
      description="Convert raw material input into ML-ready feature matrices based on the workflow plan's feature strategy."
      accentColor={pipelineAccent.featureEngineering}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          {loading ? 'Running...' : 'Run Feature Engineering'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Feature Engineering
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}
        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="FE ID">{result.feature_engineering_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={result.status} color={STATUS_COLORS[result.status] || 'default'} />
                </Descriptions.Item>
                <Descriptions.Item label="Input Modality">{result.input_modality}</Descriptions.Item>
                <Descriptions.Item label="Feature Type">{result.feature_type}</Descriptions.Item>
                {result.executed_feature_strategy_id && <Descriptions.Item label="Feat Strategy">{result.executed_feature_strategy_id}</Descriptions.Item>}
              </Descriptions>
            </Card>
            {result.warnings?.length > 0 && <WarningBox warnings={result.warnings} />}
            {result.errors?.length > 0 && <ErrorBox message={result.errors.join('; ')} />}
            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}
        {!result && !error && !loading && (
          <EmptyState description="No feature engineering result yet. Click &quot;Run Feature Engineering&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default FeatureEngineeringPanel;
