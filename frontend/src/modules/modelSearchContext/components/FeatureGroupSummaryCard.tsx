import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, WarningOutlined } from '@ant-design/icons';
import { FeatureGroupSummary } from '../types';

interface Props {
  summary: FeatureGroupSummary;
}

const FeatureGroupSummaryCard: React.FC<Props> = ({ summary }) => {
  return (
    <Card title="Feature Group Summary" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={1}>
        <Descriptions.Item label="Retained Groups">
          {summary.retained_groups.length > 0 ? (
            <span>
              {summary.retained_groups.map((g) => (
                <Tag key={g} icon={<CheckCircleOutlined />} color="success">{g}</Tag>
              ))}
            </span>
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Dropped Groups">
          {summary.dropped_groups.length > 0 ? (
            <span>
              {summary.dropped_groups.map((g) => (
                <Tag key={g} icon={<CloseCircleOutlined />} color="error">{g}</Tag>
              ))}
            </span>
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
        {summary.partially_retained_groups.length > 0 && (
          <Descriptions.Item label="Partially Retained">
            <span>
              {summary.partially_retained_groups.map((g) => (
                <Tag key={g} icon={<WarningOutlined />} color="warning">{g}</Tag>
              ))}
            </span>
          </Descriptions.Item>
        )}
        <Descriptions.Item label="Low Feature Warning">
          <Tag color={summary.low_effective_feature_warning ? 'warning' : 'success'}>
            {summary.low_effective_feature_warning ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default FeatureGroupSummaryCard;
