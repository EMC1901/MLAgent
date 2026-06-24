import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Statistic, Row, Col, Table } from 'antd';
import { createPipelineGeneration, rerunPipelineGeneration } from '../../../api/pipelineGenerationApi';
import { PipelineGenerationResponse } from '../types';
import { STATUS_COLORS, PRIORITY_COLORS, ROLE_COLORS } from '../constants';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

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
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await createPipelineGeneration(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to generate pipeline.');
    } finally { setLoading(false); }
  };

  const handleRerun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await rerunPipelineGeneration(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run pipeline generation.');
    } finally { setLoading(false); }
  };

  const specColumns = [
    { title: 'Spec ID', dataIndex: 'pipeline_spec_id', key: 'specId', render: (v: string) => <code>{v}</code> },
    { title: 'Role', dataIndex: 'pipeline_role', key: 'role', render: (v: string) => <StatusBadge label={v} color={ROLE_COLORS[v]} /> },
    { title: 'Model', key: 'model', render: (_: unknown, r: any) => r.model_display_name || r.model_id },
    { title: 'Family', dataIndex: 'model_family', key: 'family', render: (v: string) => v || '-' },
    { title: 'Priority', dataIndex: 'priority', key: 'priority', render: (v: string) => <StatusBadge label={v} color={PRIORITY_COLORS[v]} /> },
    { title: 'HPO', dataIndex: 'hpo_enabled', key: 'hpo', render: (v: boolean) => <StatusBadge label={v ? 'Yes' : 'No'} color={v ? 'success' : 'default'} /> },
    { title: 'Exec Ready', dataIndex: 'execution_ready', key: 'execReady', render: (v: boolean) => <span style={{ color: v ? '#2e7d32' : '#c62828', fontWeight: 600 }}>{v ? 'Yes' : 'No'}</span> },
  ];

  const bindingColumns = [
    { title: 'Model', dataIndex: 'model_id', key: 'model' },
    { title: 'Registry', dataIndex: 'model_registry_valid', key: 'registry', render: (v: boolean) => <StatusBadge label={v ? 'Valid' : 'Invalid'} color={v ? 'success' : 'error'} /> },
    { title: 'HPO Valid', dataIndex: 'hpo_registry_valid', key: 'hpo', render: (v: boolean) => <StatusBadge label={v ? 'Valid' : 'N/A'} color={v ? 'success' : 'default'} /> },
    { title: 'Val. Strategy', dataIndex: 'validation_strategy_valid', key: 'val', render: (v: boolean) => <StatusBadge label={v ? 'Valid' : 'Invalid'} color={v ? 'success' : 'error'} /> },
    { title: 'Metric Valid', dataIndex: 'metric_valid', key: 'metric', render: (v: boolean) => <StatusBadge label={v ? 'Valid' : 'Invalid'} color={v ? 'success' : 'error'} /> },
  ];

  const reviewChecklistColumns = [
    { title: 'Dimension', dataIndex: 'dimension', key: 'dimension' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v: string) => <StatusBadge label={v} color={v === 'pass' ? 'success' : v === 'warning' ? 'warning' : 'default'} /> },
    { title: 'Comment', dataIndex: 'comment', key: 'comment' },
  ];

  const tabItems = [
    {
      key: 'summary', label: 'Summary',
      children: result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          {result.pipeline_bundle && (
            <Card size="small" title="Pipeline Bundle Summary">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Bundle ID">
                  <StatusBadge label={result.pipeline_bundle.bundle_id} color="#1565c0" />
                </Descriptions.Item>
                <Descriptions.Item label="Task Type">
                  <StatusBadge label={result.pipeline_bundle.task_type || 'N/A'} color="#1565c0" />
                </Descriptions.Item>
                <Descriptions.Item label="Target Column">{result.pipeline_bundle.target_column}</Descriptions.Item>
                <Descriptions.Item label="Primary Metric">
                  <StatusBadge label={result.pipeline_bundle.primary_metric || 'N/A'} />
                </Descriptions.Item>
                <Descriptions.Item label="Metric Direction">{result.pipeline_bundle.metric_direction}</Descriptions.Item>
                <Descriptions.Item label="Pipeline Specs">{result.n_pipeline_specs} total</Descriptions.Item>
                <Descriptions.Item label="Baselines">{result.n_baseline_specs}</Descriptions.Item>
                <Descriptions.Item label="HPO">{result.n_hpo_specs}</Descriptions.Item>
                {result.pipeline_bundle.feature_columns.length > 0 && (
                  <Descriptions.Item label="Feature Columns">{result.pipeline_bundle.feature_columns.length} columns</Descriptions.Item>
                )}
              </Descriptions>
            </Card>
          )}
          {result.pipeline_validation_result && (
            <Card size="small" title="Pipeline Validation">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Overall Valid">
                  <span style={{ color: result.pipeline_validation_result.is_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                    {result.pipeline_validation_result.is_valid ? 'Yes' : 'No'}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="Structure">
                  <StatusBadge label={result.pipeline_validation_result.structure_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.structure_valid ? 'success' : 'error'} />
                </Descriptions.Item>
                <Descriptions.Item label="Registry">
                  <StatusBadge label={result.pipeline_validation_result.registry_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.registry_valid ? 'success' : 'error'} />
                </Descriptions.Item>
                <Descriptions.Item label="Artifact">
                  <StatusBadge label={result.pipeline_validation_result.artifact_valid ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.artifact_valid ? 'success' : 'error'} />
                </Descriptions.Item>
                <Descriptions.Item label="Task Compat">
                  <StatusBadge label={result.pipeline_validation_result.task_type_compatible ? 'Pass' : 'Fail'} color={result.pipeline_validation_result.task_type_compatible ? 'success' : 'error'} />
                </Descriptions.Item>
              </Descriptions>
              {result.pipeline_validation_result.errors.length > 0 && (
                <ErrorBox message={result.pipeline_validation_result.errors.join('; ')} style={{ marginTop: 8, marginBottom: 0 }} />
              )}
              {result.pipeline_validation_result.warnings.length > 0 && (
                <WarningBox warnings={result.pipeline_validation_result.warnings} style={{ marginTop: 8, marginBottom: 0 }} />
              )}
            </Card>
          )}
        </Space>
      ) : <EmptyState description="Run pipeline generation to see summary." />,
    },
    {
      key: 'specs', label: `Pipeline Specs${result ? ` (${result.pipeline_specs?.length || 0})` : ''}`,
      children: result?.pipeline_specs?.length ? (
        <Table
          dataSource={result.pipeline_specs.map((s, i) => ({ ...s, key: i }))}
          columns={specColumns}
          size="small" scroll={{ x: 800 }} pagination={false}
        />
      ) : <EmptyState description="No pipeline specs available." />,
    },
    {
      key: 'binding', label: 'Component Binding',
      children: result?.component_binding_result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Card size="small">
            <div>
              <strong>All Valid: </strong>
              <span style={{ color: result.component_binding_result.all_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.component_binding_result.all_valid ? 'Yes' : 'No'}
              </span>
            </div>
          </Card>
          {result.component_binding_result.bindings.length > 0 && (
            <Table
              dataSource={result.component_binding_result.bindings.map((b, i) => ({ ...b, key: i }))}
              columns={bindingColumns} size="small" pagination={false}
            />
          )}
          {result.component_binding_result.errors.length > 0 && (
            <ErrorBox message={result.component_binding_result.errors.join('; ')} style={{ marginBottom: 0 }} />
          )}
        </Space>
      ) : <EmptyState description="No component binding results available." />,
    },
    {
      key: 'review', label: 'AI Review',
      children: result?.llm_advisory_review ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Card size="small" title="AI Advisory Review">
            <p style={{ fontSize: 12, color: '#888', fontStyle: 'italic', marginBottom: 8 }}>
              Non-blocking machine learning risk notes. System Validator determines execution readiness.
            </p>
            <Descriptions column={3} size="small">
              <Descriptions.Item label="Impact">
                <StatusBadge
                  label={result.llm_advisory_review.execution_impact === 'non_blocking' ? 'Non-blocking' : result.llm_advisory_review.execution_impact}
                  color={result.llm_advisory_review.execution_impact === 'non_blocking' ? 'success' : 'warning'}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Risk Level">
                <StatusBadge label={result.llm_advisory_review.risk_level}
                  color={result.llm_advisory_review.risk_level === 'none' ? 'success' : result.llm_advisory_review.risk_level === 'low' ? 'processing' : result.llm_advisory_review.risk_level === 'medium' ? 'warning' : 'error'} />
              </Descriptions.Item>
              <Descriptions.Item label="Confidence">
                <StatusBadge label={result.llm_advisory_review.confidence_level}
                  color={result.llm_advisory_review.confidence_level === 'high' ? 'success' : 'warning'} />
              </Descriptions.Item>
            </Descriptions>
            {result.llm_advisory_review.checklist.length > 0 && (
              <Table
                dataSource={result.llm_advisory_review.checklist.map((c, i) => ({ ...c, key: i }))}
                columns={reviewChecklistColumns} size="small" pagination={false} style={{ marginTop: 8 }}
              />
            )}
          </Card>
        </Space>
      ) : <EmptyState description="No AI advisory review available." />,
    },
    {
      key: 'json', label: 'Full JSON',
      children: result ? <JsonViewer data={result} /> : <EmptyState description="Run generation to see JSON output." />,
    },
  ];

  return (
    <PanelContainer
      title="Executable Pipeline Generation"
      description="Convert the Model Search Plan into validated, registry-bound Pipeline Specs and Execution Input ready for the downstream Pipeline Execution module."
      accentColor={pipelineAccent.pipelineGeneration}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleGenerate} loading={loading}>
          {loading ? 'Generating Pipeline...' : 'Generate Pipeline'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Generation
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="PG ID">{result.pipeline_generation_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={result.status} color={STATUS_COLORS[result.status] || 'default'} />
                </Descriptions.Item>
                <Descriptions.Item label="Ready for Execution">
                  <span style={{ color: result.ready_for_execution ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                    {result.ready_for_execution ? 'Yes' : 'No'}
                  </span>
                </Descriptions.Item>
                <Descriptions.Item label="Generation Mode">{result.generation_mode}</Descriptions.Item>
              </Descriptions>
            </Card>

            {result.warnings && result.warnings.length > 0 && <WarningBox warnings={result.warnings} />}
            {result.error_message && <ErrorBox message={result.error_message} />}

            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No pipeline generated yet. Click &quot;Generate Pipeline&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default PipelineGenerationPanel;
