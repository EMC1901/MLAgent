import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { ModelSearchContextInput } from '../types';

interface Props {
  input: ModelSearchContextInput;
}

const ModelSearchContextJsonViewer: React.FC<Props> = ({ input }) => {
  return (
    <Card title="Model Search Context Input" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Ready for Pipeline Generation">
          <Tag color={input.ready_for_pipeline_generation ? 'success' : 'error'}>
            {input.ready_for_pipeline_generation ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Task Type">
          <Tag>{input.task_type || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Target Column">{input.target_column || 'N/A'}</Descriptions.Item>
        <Descriptions.Item label="Primary Metric">
          <Tag color="blue">{input.primary_metric || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Feature Columns" span={2}>
          {input.feature_columns.length > 0
            ? `${input.feature_columns.length} columns: ${input.feature_columns.slice(0, 10).join(', ')}${input.feature_columns.length > 10 ? '...' : ''}`
            : 'None'}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default ModelSearchContextJsonViewer;
