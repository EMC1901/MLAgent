import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Statistic, Row, Col, Table } from 'antd';
import { createMetricEvaluation, rerunMetricEvaluation } from '../../../api/metricEvaluationApi';
import { MetricEvaluationResponse } from '../types';
import { STATUS_COLORS, STATUS_LABELS, DIRECTION_LABELS, ROLE_COLORS } from '../constants';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface MetricEvaluationPanelProps {
  taskId: string;
  initialResult?: MetricEvaluationResponse;
}

const MetricEvaluationPanel: React.FC<MetricEvaluationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MetricEvaluationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await createMetricEvaluation(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to evaluate metrics.');
    } finally { setLoading(false); }
  };

  const handleRerun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await rerunMetricEvaluation(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run metric evaluation.');
    } finally { setLoading(false); }
  };

  const rankingColumns = [
    { title: 'Rank', dataIndex: 'rank', key: 'rank', render: (v: number) => <strong>#{v}</strong> },
    {
      title: 'Model', dataIndex: 'model_id', key: 'model',
      render: (v: string, r: any) => <>{v}{r.rank === 1 && <StatusBadge label="BEST" color="success" />}</>,
    },
    { title: 'Family', dataIndex: 'model_family', key: 'family', render: (v: string) => v || '-' },
    { title: 'Best Trial', dataIndex: 'best_trial_id', key: 'trial', render: (v: string) => v ? <code style={{ fontSize: 11 }}>{v}</code> : '-' },
    { title: result?.primary_metric || 'Metric', dataIndex: 'primary_metric_value', key: 'metric', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'vs Baseline', dataIndex: 'improvement_over_best_baseline', key: 'vsBaseline', render: (v: number) => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(6)}` : 'N/A' },
    { title: 'Improve %', dataIndex: 'improvement_percentage', key: 'improve', render: (v: number) => v != null ? `${v >= 0 ? '+' : ''}${v.toFixed(2)}%` : 'N/A' },
    { title: 'Reason', dataIndex: 'ranking_reason', key: 'reason', render: (v: string) => <span style={{ fontSize: 11, color: '#666' }}>{v}</span> },
  ];

  const trialColumns = [
    { title: 'Model', dataIndex: 'model_id', key: 'model' },
    { title: 'Role', dataIndex: 'pipeline_role', key: 'role', render: (v: string) => <StatusBadge label={v || '-'} color={ROLE_COLORS[v] || 'default'} /> },
    { title: 'Type', dataIndex: 'trial_type', key: 'type', render: (v: string) => <span style={{ fontSize: 11 }}>{v || '-'}</span> },
    { title: 'Folds', dataIndex: 'n_folds', key: 'folds' },
    { title: 'Mean', dataIndex: 'primary_metric_mean', key: 'mean', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'Std', dataIndex: 'primary_metric_std', key: 'std', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'Min', dataIndex: 'primary_metric_min', key: 'min', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'Max', dataIndex: 'primary_metric_max', key: 'max', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'Rank', dataIndex: 'rank', key: 'rank', render: (v: number) => v != null ? `#${v}` : '-' },
    { title: 'Best', dataIndex: 'is_best_trial', key: 'best', render: (v: boolean) => v ? <StatusBadge label="BEST" color="success" /> : '' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v: string) => <StatusBadge label={v} color={v === 'evaluated' ? 'success' : 'error'} /> },
  ];

  const foldColumns = [
    { title: 'Trial', dataIndex: 'trial_id', key: 'trial', render: (v: string) => <code style={{ fontSize: 11 }}>{v?.substring(0, 12)}...</code> },
    { title: 'Model', dataIndex: 'model_id', key: 'model' },
    { title: 'Fold', dataIndex: 'fold_index', key: 'fold', render: (v: number) => `Fold ${v}` },
    { title: 'Samples', dataIndex: 'n_samples', key: 'samples' },
    { title: result?.primary_metric || 'Metric', dataIndex: 'primary_metric_value', key: 'metric', render: (v: number) => v != null ? v.toFixed(6) : 'N/A' },
    { title: 'Status', dataIndex: 'status', key: 'status', render: (v: string) => <StatusBadge label={v} color={v === 'evaluated' ? 'success' : 'error'} /> },
  ];

  const tabItems = [
    {
      key: 'summary', label: 'Summary',
      children: result ? (
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Row gutter={[12, 12]}>
            <Col span={8}>
              <Statistic title="Trials Evaluated" value={result.n_trials_evaluated} />
            </Col>
            <Col span={8}>
              <Statistic title="Failed" value={result.n_trials_failed} valueStyle={{ color: '#c62828' }} />
            </Col>
            <Col span={8}>
              <Statistic title="Models Evaluated" value={result.n_models_evaluated} valueStyle={{ color: '#1565c0' }} />
            </Col>
          </Row>
          <Card size="small" title="Best Model Candidate">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Best Model">{result.best_model_id || 'N/A'}</Descriptions.Item>
              <Descriptions.Item label="Best Trial"><code>{result.best_trial_id || 'N/A'}</code></Descriptions.Item>
              <Descriptions.Item label="Best Pipeline Spec"><code>{result.best_pipeline_spec_id || 'N/A'}</code></Descriptions.Item>
            </Descriptions>
            {result.metric_summary && (
              <>
                <Descriptions column={3} size="small" style={{ marginTop: 8 }}>
                  <Descriptions.Item label={`Best ${result.primary_metric}`}>
                    {result.metric_summary.best_metric_value?.toFixed(6) ?? 'N/A'}
                  </Descriptions.Item>
                  <Descriptions.Item label={`Mean ${result.primary_metric}`}>
                    {result.metric_summary.mean_metric_value?.toFixed(6) ?? 'N/A'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Std">
                    {result.metric_summary.std_metric_value?.toFixed(6) ?? 'N/A'}
                  </Descriptions.Item>
                </Descriptions>
              </>
            )}
          </Card>
        </Space>
      ) : <EmptyState description="Run evaluation to see summary." />,
    },
    {
      key: 'ranking', label: `Model Ranking${result?.model_ranking ? ` (${result.model_ranking.length})` : ''}`,
      children: result?.model_ranking?.length ? (
        <Table
          dataSource={result.model_ranking.map((m, i) => ({ ...m, key: i }))}
          columns={rankingColumns}
          size="small" scroll={{ x: 900 }} pagination={false}
          rowClassName={(record) => record.rank === 1 ? 'ant-table-row-success' : ''}
        />
      ) : <EmptyState description="No model ranking data available." />,
    },
    {
      key: 'trials', label: `Trial Metrics${result?.trial_metric_results ? ` (${result.trial_metric_results.length})` : ''}`,
      children: result?.trial_metric_results?.length ? (
        <Table
          dataSource={result.trial_metric_results.map((t, i) => ({ ...t, key: i }))}
          columns={trialColumns}
          size="small" scroll={{ x: 950 }} pagination={false}
          rowClassName={(record) => record.is_best_trial ? 'ant-table-row-success' : record.status === 'failed' ? 'ant-table-row-error' : ''}
        />
      ) : <EmptyState description="No trial metrics available." />,
    },
    {
      key: 'folds', label: `Fold Metrics${result?.fold_metric_results ? ` (${result.fold_metric_results.length})` : ''}`,
      children: result?.fold_metric_results?.length ? (
        <Table
          dataSource={result.fold_metric_results.map((f, i) => ({ ...f, key: i }))}
          columns={foldColumns} size="small" pagination={false}
          rowClassName={(record) => record.status === 'failed' ? 'ant-table-row-error' : ''}
        />
      ) : <EmptyState description="No fold metrics available." />,
    },
    {
      key: 'baseline', label: 'Baseline',
      children: result?.baseline_comparison ? (
        result.baseline_comparison.baseline_available ? (
          <Card size="small" title="Baseline Comparison">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Best Baseline">
                {result.baseline_comparison.best_baseline_model_id || 'N/A'}
                {' ('}{result.baseline_comparison.best_baseline_metric_value?.toFixed(6) ?? 'N/A'}{')'}
              </Descriptions.Item>
              <Descriptions.Item label="Best Candidate">
                {result.baseline_comparison.best_candidate_model_id || 'N/A'}
                {' ('}{result.baseline_comparison.best_candidate_metric_value?.toFixed(6) ?? 'N/A'}{')'}
              </Descriptions.Item>
              <Descriptions.Item label="Absolute Improvement">
                <span style={{ color: result.baseline_comparison.candidate_beats_baseline ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.baseline_comparison.absolute_improvement?.toFixed(6) ?? 'N/A'}
                </span>
              </Descriptions.Item>
              <Descriptions.Item label="Relative Improvement">
                {result.baseline_comparison.relative_improvement_percentage?.toFixed(2) ?? 'N/A'}%
              </Descriptions.Item>
              <Descriptions.Item label="Candidate Beats Baseline">
                <span style={{ color: result.baseline_comparison.candidate_beats_baseline ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.baseline_comparison.candidate_beats_baseline ? 'Yes' : 'No'}
                </span>
              </Descriptions.Item>
            </Descriptions>
            {result.baseline_comparison.comparison_notes?.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <strong>Comparison Notes:</strong>
                <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                  {result.baseline_comparison.comparison_notes.map((note, i) => <li key={i}>{note}</li>)}
                </ul>
              </div>
            )}
          </Card>
        ) : <EmptyState description="No baseline available for comparison." />
      ) : <EmptyState description="No baseline comparison data." />,
    },
    {
      key: 'json', label: 'Full JSON',
      children: result ? <JsonViewer data={result} /> : <EmptyState description="Run evaluation to see JSON output." />,
    },
  ];

  return (
    <PanelContainer
      title="Metric Evaluation"
      description="Evaluate model metrics from upstream Pipeline Execution results. Computes fold-level, trial-level, and model-level metrics, generates model rankings and baseline comparisons."
      accentColor={pipelineAccent.metricEvaluation}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          {loading ? 'Evaluating...' : 'Run Metric Evaluation'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Evaluation
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Evaluation ID">{result.metric_evaluation_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || 'default'} />
                </Descriptions.Item>
                <Descriptions.Item label="Pipeline Exec">{result.pipeline_execution_id}</Descriptions.Item>
                <Descriptions.Item label="Task Type">{result.task_type || 'N/A'}</Descriptions.Item>
                <Descriptions.Item label="Primary Metric">
                  <StatusBadge label={result.primary_metric || 'N/A'} />
                </Descriptions.Item>
                <Descriptions.Item label="Direction">
                  {DIRECTION_LABELS[result.metric_direction] || result.metric_direction}
                </Descriptions.Item>
                <Descriptions.Item label="Ready for Diagnosis">
                  <span style={{ color: result.ready_for_result_diagnosis ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                    {result.ready_for_result_diagnosis ? 'Yes' : 'No'}
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
          <EmptyState description="No metric evaluation yet. Click &quot;Run Metric Evaluation&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default MetricEvaluationPanel;
