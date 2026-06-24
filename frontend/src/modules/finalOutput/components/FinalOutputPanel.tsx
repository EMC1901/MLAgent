import React, { useState, useMemo } from 'react';
import { Button, Space, Card, Descriptions, List, Tag, Spin, Typography } from 'antd';
import {
  FileTextOutlined,
  CheckCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import {
  createFinalOutput,
  rerunFinalOutput,
  downloadArtifactZip,
} from '../../../api/finalOutputApi';
import { FinalOutputResponse } from '../types';
import { STATUS_COLORS, STATUS_LABELS } from '../constants';
import { PanelContainer, StatusBadge, WarningBox, ErrorBox, EmptyState } from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

const { Text } = Typography;

interface FinalOutputPanelProps {
  taskId: string;
  initialResult?: FinalOutputResponse;
}

const topicFileLabels: Record<string, string> = {
  task_specification: 'Task Specification — how the system understood the task',
  dataset_profile: 'Dataset Profile — scale, target distribution, missing values, quality',
  workflow_plan: 'Workflow Plan — feature, preprocessing, model, validation, metric strategies',
  model_ready_feature_summary: 'Model-Ready Feature Summary — final feature count, dropped/kept features',
  candidate_model_plan: 'Candidate Model Plan — candidate and excluded models',
  hpo_plan: 'HPO Plan — search method, trial count, search space',
  pipeline_specs: 'Pipeline Specs — proof that workflow is executable',
  training_evaluation_results: 'Training / Evaluation Results — performance report',
  interpretability_analysis: 'Interpretability Analysis — feature importance, SHAP, material insights',
  final_output_package: 'Final Output Package — proof that reports, model, logs, reproducibility files are generated',
};

const FinalOutputPanel: React.FC<FinalOutputPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FinalOutputResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const runAction = async (action: 'create' | 'rerun') => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = action === 'create'
        ? await createFinalOutput(taskId)
        : await rerunFinalOutput(taskId);
      if (response.success) {
        setResult(response.data);
        const foId = response.data?.final_output_id;
        if (foId) {
          downloadArtifactZip(foId);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || `Failed to ${action === 'create' ? 'generate' : 're-generate'} final output.`);
    } finally {
      setLoading(false);
    }
  };

  const downloadedFiles = useMemo(() => {
    const topics = result?.topic_files;
    if (!topics || topics.length === 0) return [];
    return topics.map((t) => ({
      name: topicFileLabels[t.topic] || t.topic,
      path: t.file,
    }));
  }, [result]);

  return (
    <PanelContainer
      title="Final Output"
      description="Generate a consolidated output package including all reports, trained models, logs, and reproducibility files."
      accentColor={pipelineAccent.finalOutput}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={() => runAction('create')} loading={loading} disabled={!taskId}>
          {loading ? 'Generating...' : 'Generate Final Output'}
        </Button>
        <Button onClick={() => runAction('rerun')} loading={loading} disabled={!taskId}>
          Re-generate Output
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Card size="small">
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Status">
                  <StatusBadge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status]} />
                </Descriptions.Item>
                <Descriptions.Item label="Output ID">
                  <Text code>{result.final_output_id}</Text>
                </Descriptions.Item>
                <Descriptions.Item label="Ready for Delivery">
                  {result.ready_for_delivery ? (
                    <Tag icon={<CheckCircleOutlined />} color="success">Ready</Tag>
                  ) : (
                    <Tag icon={<WarningOutlined />} color="default">Not Ready</Tag>
                  )}
                </Descriptions.Item>
              </Descriptions>
            </Card>

            <Card size="small" title="Downloaded Files">
              {downloadedFiles.length === 0 ? (
                <EmptyState description="No artifact information available." />
              ) : (
                <List
                  size="small"
                  dataSource={downloadedFiles}
                  renderItem={(f) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<FileTextOutlined style={{ fontSize: 18, color: '#1976d2' }} />}
                        title={<Text strong>{f.name}</Text>}
                        description={<Text type="secondary" code style={{ fontSize: 12 }}>{f.path}</Text>}
                      />
                    </List.Item>
                  )}
                />
              )}
            </Card>

            {result.warnings && result.warnings.length > 0 && <WarningBox warnings={result.warnings} />}
            {result.error_message && <ErrorBox message={result.error_message} />}
          </Space>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No final output generated yet. Click &quot;Generate Final Output&quot; to produce a complete deliverable package." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default FinalOutputPanel;
