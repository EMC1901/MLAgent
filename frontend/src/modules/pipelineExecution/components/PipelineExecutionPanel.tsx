import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Statistic, Row, Col, Table } from 'antd';
import {
  createPipelineExecution,
  rerunPipelineExecution,
} from '../../../api/pipelineExecutionApi';
import { PipelineExecutionResponse, PipelineRunResultDTO, TrialResultDTO } from '../types';
import {
  STATUS_COLORS,
  TRIAL_STATUS_COLORS,
  ROLE_COLORS,
  TRIAL_TYPE_COLORS,
} from '../constants';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface PipelineExecutionPanelProps {
  taskId: string;
  initialResult?: PipelineExecutionResponse;
}

const PipelineExecutionPanel: React.FC<PipelineExecutionPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineExecutionResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

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

  const runColumns: Array<{ title: string; dataIndex?: string; key: string; render?: any }> = [
    { title: 'Run ID', dataIndex: 'pipeline_run_id', key: 'runId', render: (v: string) => <code>{v}</code> },
    {
      title: 'Role', dataIndex: 'pipeline_role', key: 'role',
      render: (v: string) => <StatusBadge label={v} color={ROLE_COLORS[v]} />,
    },
    { title: 'Model', dataIndex: 'model_id', key: 'model' },
    { title: 'Family', dataIndex: 'model_family', key: 'family', render: (v: string) => v || '-' },
    {
      title: 'HPO', dataIndex: 'hpo_enabled', key: 'hpo',
      render: (v: boolean) => <StatusBadge label={v ? 'Yes' : 'No'} color={v ? 'success' : 'default'} />,
    },
    { title: 'Planned', dataIndex: 'n_trials_planned', key: 'planned' },
    { title: 'Completed', dataIndex: 'n_trials_completed', key: 'completed', render: (v: number) => <span style={{ color: '#2e7d32' }}>{v}</span> },
    { title: 'Failed', dataIndex: 'n_trials_failed', key: 'failed', render: (v: number) => <span style={{ color: '#c62828' }}>{v}</span> },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (v: string) => <StatusBadge label={v} color={STATUS_COLORS[v]} />,
    },
    { title: 'Duration', dataIndex: 'duration_seconds', key: 'duration', render: (v: number) => `${v.toFixed(1)}s` },
  ];

  const trialColumns: Array<{ title: string; dataIndex?: string; key: string; render?: any }> = [
    { title: 'Model', dataIndex: 'model_id', key: 'model' },
    {
      title: 'Type', dataIndex: 'trial_type', key: 'type',
      render: (v: string) => <StatusBadge label={v} color={TRIAL_TYPE_COLORS[v]} />,
    },
    {
      title: 'Params', dataIndex: 'params', key: 'params',
      render: (params: Record<string, unknown>) => (
        <span style={{ fontSize: 11 }}>
          {Object.entries(params || {}).slice(0, 3).map(([k, v]) => `${k}=${v}`).join(', ') || '-'}
        </span>
      ),
    },
    { title: 'Folds', dataIndex: 'fold_results', key: 'folds', render: (v: unknown[]) => v?.length || 0 },
    {
      title: 'Status', dataIndex: 'status', key: 'status',
      render: (v: string) => <StatusBadge label={v} color={TRIAL_STATUS_COLORS[v]} />,
    },
    {
      title: 'Prediction', key: 'prediction',
      render: (_: unknown, r: TrialResultDTO) =>
        (r.prediction_artifact_paths && r.prediction_artifact_paths.length > 0)
          ? <span style={{ fontSize: 11, color: '#2e7d32' }}>Saved ({r.prediction_artifact_paths.length})</span>
          : '-',
    },
    {
      title: 'Model Path', key: 'modelPath',
      render: (_: unknown, r: TrialResultDTO) =>
        (r.model_artifact_paths && r.model_artifact_paths.length > 0)
          ? <span style={{ fontSize: 11, color: '#1565c0' }}>Saved ({r.model_artifact_paths.length})</span>
          : '-',
    },
    { title: 'Duration', dataIndex: 'duration_seconds', key: 'duration', render: (v: number) => `${v.toFixed(1)}s` },
    {
      title: 'Error', dataIndex: 'error_message', key: 'error',
      render: (v: string) => v
        ? <span style={{ fontSize: 11, color: '#c62828' }}>{v.substring(0, 60)}</span>
        : '-',
    },
  ];

  const tabItems = [
    {
      key: 'summary',
      label: 'Summary',
      children: result ? (
        <Card size="small" title="Execution Progress">
          <Row gutter={[12, 12]}>
            <Col span={8}>
              <Statistic title="Pipeline Specs" value={result.n_pipeline_specs} />
            </Col>
            <Col span={8}>
              <Statistic title="Trials Planned" value={result.n_trials_planned} />
            </Col>
            <Col span={8}>
              <Statistic title="Completed" value={result.n_trials_completed} valueStyle={{ color: '#2e7d32' }} />
            </Col>
            <Col span={8}>
              <Statistic title="Failed" value={result.n_trials_failed} valueStyle={{ color: '#c62828' }} />
            </Col>
            <Col span={8}>
              <Statistic title="Models Trained" value={result.n_models_trained} valueStyle={{ color: '#1565c0' }} />
            </Col>
            <Col span={8}>
              <Statistic title="Duration" value={`${result.duration_seconds.toFixed(1)}s`} />
            </Col>
          </Row>
        </Card>
      ) : (
        <EmptyState description="No execution data available." />
      ),
    },
    {
      key: 'runs',
      label: `Pipeline Runs${result ? ` (${result.pipeline_run_results?.length || 0})` : ''}`,
      children: result?.pipeline_run_results?.length ? (
        <Card size="small">
          <Table<PipelineRunResultDTO>
            columns={runColumns}
            dataSource={result.pipeline_run_results.map((pr, i) => ({ ...pr, key: i }))}
            size="small"
            scroll={{ x: 900 }}
            pagination={false}
          />
        </Card>
      ) : (
        <EmptyState description="No pipeline runs available." />
      ),
    },
    {
      key: 'trials',
      label: `Trial Results${result ? ` (${result.trial_results?.length || 0})` : ''}`,
      children: result?.trial_results?.length ? (
        <Card size="small">
          <Table<TrialResultDTO>
            columns={trialColumns}
            dataSource={result.trial_results.map((t, i) => ({ ...t, key: i }))}
            size="small"
            scroll={{ x: 950 }}
            pagination={false}
            rowClassName={(record) => record.status === 'failed' ? 'ant-table-row-error' : ''}
          />
        </Card>
      ) : (
        <EmptyState description="No trial results available." />
      ),
    },
    {
      key: 'json',
      label: 'Full JSON',
      children: result ? <JsonViewer data={result} /> : <EmptyState description="Run training to see JSON output." />,
    },
  ];

  return (
    <PanelContainer
      title="Pipeline Execution and Training"
      description="Execute model training and HPO trials from the upstream Pipeline Generation output. Training is performed by the system Controlled Executor using only registered models."
      accentColor={pipelineAccent.pipelineExecution}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRunTraining} loading={loading}>
          {loading ? 'Training in Progress...' : 'Run Training'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Training
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Execution ID">{result.pipeline_execution_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={result.status} color={STATUS_COLORS[result.status]} />
                </Descriptions.Item>
                <Descriptions.Item label="Pipeline Generation">{result.pipeline_generation_id}</Descriptions.Item>
                <Descriptions.Item label="Ready for Metric Eval">
                  <span style={{ color: result.ready_for_metric_evaluation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                    {result.ready_for_metric_evaluation ? 'Yes' : 'No'}
                  </span>
                </Descriptions.Item>
              </Descriptions>
            </Card>

            {result.warnings && result.warnings.length > 0 && <WarningBox warnings={result.warnings} />}
            {result.error_message && <ErrorBox message={result.error_message} />}

            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No pipeline execution result yet. Click &quot;Run Training&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default PipelineExecutionPanel;
