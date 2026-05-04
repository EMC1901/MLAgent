import React, { useState } from 'react';
import {
  Card,
  Button,
  Descriptions,
  Tag,
  Spin,
  Alert,
  Space,
  message,
} from 'antd';
import {
  PlayCircleOutlined,
  RedoOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import {
  FeaturePreprocessingResponse,
} from '../types';
import {
  createFeaturePreprocessing,
  getLatestFeaturePreprocessingByTaskId,
  rerunFeaturePreprocessing,
} from '../../../api/featurePreprocessingApi';
import { STATUS_LABELS, STATUS_COLORS } from '../constants';
import ValidationSummaryCard from './ValidationSummaryCard';
import ColumnFilteringCard from './ColumnFilteringCard';
import PreprocessingExecutionCard from './PreprocessingExecutionCard';
import ModelReadyArtifactCard from './ModelReadyArtifactCard';

interface Props {
  taskId: string;
}

const FeaturePreprocessingPanel: React.FC<Props> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<FeaturePreprocessingResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await createFeaturePreprocessing(taskId);
      if (resp.success) {
        setData(resp.data);
        message.success('Feature preprocessing completed.');
      } else {
        setError(resp.message);
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail?.message || e?.message || 'Unknown error';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await rerunFeaturePreprocessing(taskId);
      if (resp.success) {
        setData(resp.data);
        message.success('Feature preprocessing re-run completed.');
      } else {
        setError(resp.message);
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail?.message || e?.message || 'Unknown error';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await getLatestFeaturePreprocessingByTaskId(taskId);
      if (resp.success) {
        setData(resp.data);
      } else {
        setError(resp.message);
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail?.message || e?.message || 'Unknown error';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card
      title="Feature Preprocessing"
      extra={
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh
          </Button>
          {data ? (
            <Button
              icon={<RedoOutlined />}
              onClick={handleRerun}
              loading={loading}
            >
              Re-run
            </Button>
          ) : null}
          <Button
            type="primary"
            icon={<PlayCircleOutlined />}
            onClick={handleRun}
            loading={loading}
          >
            Run
          </Button>
        </Space>
      }
    >
      {error && (
        <Alert type="error" message={error} closable style={{ marginBottom: 16 }} />
      )}

      {loading && <Spin tip="Running feature preprocessing..." />}

      {data && !loading && (
        <>
          <Descriptions bordered size="small" column={2} style={{ marginBottom: 16 }}>
            <Descriptions.Item label="Preprocessing ID">
              {data.preprocessing_id}
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Tag color={STATUS_COLORS[data.status] || 'default'}>
                {STATUS_LABELS[data.status] || data.status}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="FE ID">
              {data.feature_engineering_id}
            </Descriptions.Item>
            <Descriptions.Item label="Ready for Model Search">
              <Tag color={data.model_search_input?.ready_for_model_search ? 'success' : 'error'}>
                {data.model_search_input?.ready_for_model_search ? 'Yes' : 'No'}
              </Tag>
            </Descriptions.Item>
          </Descriptions>

          {data.validation_summary && (
            <ValidationSummaryCard summary={data.validation_summary} />
          )}
          {data.column_validation && (
            <ColumnFilteringCard validation={data.column_validation} />
          )}
          {data.preprocessing_execution && (
            <PreprocessingExecutionCard execution={data.preprocessing_execution} />
          )}
          {data.model_ready_artifact && (
            <ModelReadyArtifactCard
              artifact={data.model_ready_artifact}
              pipelineArtifact={data.preprocessing_pipeline_artifact}
              preprocessingId={data.preprocessing_id}
            />
          )}

          {data.warnings && data.warnings.length > 0 && (
            <Alert
              type="warning"
              message="Warnings"
              description={data.warnings.join('; ')}
              style={{ marginTop: 16 }}
            />
          )}
          {data.errors && data.errors.length > 0 && (
            <Alert
              type="error"
              message="Errors"
              description={data.errors.join('; ')}
              style={{ marginTop: 16 }}
            />
          )}
        </>
      )}

      {!data && !loading && !error && (
        <Alert
          type="info"
          message="No preprocessing data yet. Click Run to start."
        />
      )}
    </Card>
  );
};

export default FeaturePreprocessingPanel;
