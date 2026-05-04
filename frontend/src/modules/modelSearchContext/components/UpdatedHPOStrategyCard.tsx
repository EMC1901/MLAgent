import React from 'react';
import { Card, Descriptions, Tag } from 'antd';

interface Props {
  hpoStrategy: Record<string, unknown>;
}

const UpdatedHPOStrategyCard: React.FC<Props> = ({ hpoStrategy }) => {
  const enabled = hpoStrategy?.enabled as boolean | undefined;
  const method = hpoStrategy?.search_method as string | undefined;
  const budget = hpoStrategy?.budget_level as string | undefined;
  const trials = hpoStrategy?.max_trials as number | undefined;

  if (!method && !budget && trials === undefined) {
    return (
      <Card title="Updated HPO Strategy" size="small" style={{ marginBottom: 16 }}>
        <Tag>No HPO strategy data</Tag>
      </Card>
    );
  }

  return (
    <Card title="Updated HPO Strategy" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Enabled">
          <Tag color={enabled !== false ? 'success' : 'default'}>
            {enabled !== false ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Search Method">
          <Tag color="cyan">{method || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Budget Level">
          <Tag color={budget === 'low' ? 'orange' : budget === 'high' ? 'green' : 'blue'}>
            {budget || 'N/A'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Max Trials">
          <Tag>{trials ?? 'N/A'}</Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default UpdatedHPOStrategyCard;
