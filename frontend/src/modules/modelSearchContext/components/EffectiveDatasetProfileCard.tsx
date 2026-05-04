import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { DatasetEffectiveProfile } from '../types';

interface Props {
  profile: DatasetEffectiveProfile;
}

const EffectiveDatasetProfileCard: React.FC<Props> = ({ profile }) => {
  const reductionPct = (profile.feature_reduction_ratio * 100).toFixed(1);

  return (
    <Card title="Effective Dataset Profile" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={3}>
        <Descriptions.Item label="Samples">{profile.n_samples}</Descriptions.Item>
        <Descriptions.Item label="Raw Features">{profile.n_raw_features}</Descriptions.Item>
        <Descriptions.Item label="Final Features">
          <Tag color={profile.n_final_features < 20 ? 'orange' : 'blue'}>
            {profile.n_final_features}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Dropped Features">
          <Tag color="red">{profile.n_dropped_features}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Reduction Ratio">
          <Tag color={profile.feature_reduction_ratio > 0.8 ? 'orange' : 'default'}>
            {reductionPct}%
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Target Column">{profile.target_column}</Descriptions.Item>
        <Descriptions.Item label="Task Type">{profile.task_type}</Descriptions.Item>
        <Descriptions.Item label=" ">{null}</Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default EffectiveDatasetProfileCard;
