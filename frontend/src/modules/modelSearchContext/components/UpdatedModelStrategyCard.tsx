import React from 'react';
import { Card, Descriptions, Tag } from 'antd';

interface Props {
  modelStrategy: Record<string, unknown>;
}

const UpdatedModelStrategyCard: React.FC<Props> = ({ modelStrategy }) => {
  const families = (modelStrategy?.candidate_model_families as string[]) || [];
  const baselines = (modelStrategy?.baseline_models as string[]) || [];
  const bias = modelStrategy?.preferred_model_bias as string | undefined;
  const excluded = (modelStrategy?.excluded_model_families as string[]) || [];

  if (!families.length && !baselines.length && !bias) {
    return (
      <Card title="Updated Model Strategy" size="small" style={{ marginBottom: 16 }}>
        <Tag>No model strategy data</Tag>
      </Card>
    );
  }

  return (
    <Card title="Updated Model Strategy" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={1}>
        <Descriptions.Item label="Candidate Families">
          {families.length > 0 ? families.map((m) => <Tag key={m} color="blue">{m}</Tag>) : <Tag>None</Tag>}
        </Descriptions.Item>
        <Descriptions.Item label="Baseline Models">
          {baselines.length > 0 ? baselines.map((m) => <Tag key={m} color="geekblue">{m}</Tag>) : <Tag>None</Tag>}
        </Descriptions.Item>
        {bias && (
          <Descriptions.Item label="Preference">
            <Tag color="purple">{bias}</Tag>
          </Descriptions.Item>
        )}
        {excluded.length > 0 && (
          <Descriptions.Item label="Excluded">
            {excluded.map((m) => <Tag key={m} color="red">{m}</Tag>)}
          </Descriptions.Item>
        )}
      </Descriptions>
    </Card>
  );
};

export default UpdatedModelStrategyCard;
