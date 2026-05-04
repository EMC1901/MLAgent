import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { ValidationSummary } from '../types';

interface Props {
  summary: ValidationSummary;
}

const ValidationSummaryCard: React.FC<Props> = ({ summary }) => {
  return (
    <Card title="Validation Summary" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={3}>
        <Descriptions.Item label="Model Ready">
          <Tag color={summary.is_model_ready ? 'success' : 'error'}>
            {summary.is_model_ready ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Samples">{summary.n_samples}</Descriptions.Item>
        <Descriptions.Item label="Raw Features">{summary.n_raw_features}</Descriptions.Item>
        <Descriptions.Item label="Valid Before Preprocessing">
          {summary.n_valid_features_before_preprocessing}
        </Descriptions.Item>
        <Descriptions.Item label="After Preprocessing">
          {summary.n_features_after_preprocessing}
        </Descriptions.Item>
        <Descriptions.Item label="Dropped Features">
          <Tag color="orange">{summary.n_dropped_features}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Target Column">{summary.target_column}</Descriptions.Item>
        <Descriptions.Item label="Task Type">{summary.task_type}</Descriptions.Item>
        <Descriptions.Item label=" ">{null}</Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default ValidationSummaryCard;
