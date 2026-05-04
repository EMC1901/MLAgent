import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { PreprocessingSummary } from '../types';

interface Props {
  summary: PreprocessingSummary;
}

const boolTag = (value: boolean, label?: string) => (
  <Tag color={value ? 'blue' : 'default'}>
    {value ? (label || 'Executed') : 'Not Executed'}
  </Tag>
);

const PreprocessingSummaryCard: React.FC<Props> = ({ summary }) => {
  return (
    <Card title="Preprocessing Summary" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Imputation">{boolTag(summary.imputation_executed)}</Descriptions.Item>
        <Descriptions.Item label="Scaling">{boolTag(summary.scaling_executed)}</Descriptions.Item>
        <Descriptions.Item label="Feature Selection">{boolTag(summary.feature_selection_executed)}</Descriptions.Item>
        <Descriptions.Item label="Categorical Encoding">{boolTag(summary.categorical_encoding_executed)}</Descriptions.Item>
        <Descriptions.Item label="Pipeline Artifact ID" span={2}>
          {summary.preprocessing_pipeline_artifact_id || <Tag>N/A</Tag>}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default PreprocessingSummaryCard;
