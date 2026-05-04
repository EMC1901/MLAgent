import React from 'react';
import { Card, Table, Tag, Space } from 'antd';
import { ColumnValidation, DroppedFeature } from '../types';
import { DROP_REASON_LABELS } from '../constants';

interface Props {
  validation: ColumnValidation;
}

const FEATURE_COLUMNS = [
  {
    title: 'Feature Name',
    dataIndex: 'name',
    key: 'name',
    ellipsis: true,
  },
  {
    title: 'Reason',
    dataIndex: 'reason',
    key: 'reason',
    render: (reason: string) => (
      <Tag>{DROP_REASON_LABELS[reason] || reason}</Tag>
    ),
  },
  {
    title: 'Action',
    dataIndex: 'action',
    key: 'action',
    render: (action: string) => (
      <Tag color="red">{action}</Tag>
    ),
  },
];

const ColumnFilteringCard: React.FC<Props> = ({ validation }) => {
  const allDropped: (DroppedFeature & { category: string })[] = [
    ...validation.dropped_invalid_features.map((d) => ({ ...d, category: 'Invalid' })),
    ...validation.dropped_all_missing_features.map((d) => ({ ...d, category: 'All Missing' })),
    ...validation.dropped_constant_features.map((d) => ({ ...d, category: 'Constant' })),
    ...validation.dropped_high_missing_features.map((d) => ({ ...d, category: 'High Missing' })),
  ];

  const totalDropped =
    validation.dropped_invalid_features.length +
    validation.dropped_all_missing_features.length +
    validation.dropped_constant_features.length +
    validation.dropped_high_missing_features.length;

  return (
    <Card title={`Column Filtering (${totalDropped} dropped, ${validation.retained_features.length} retained)`} size="small" style={{ marginBottom: 16 }}>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Space>
          <Tag color="red">Invalid: {validation.dropped_invalid_features.length}</Tag>
          <Tag color="orange">All Missing: {validation.dropped_all_missing_features.length}</Tag>
          <Tag color="gold">Constant: {validation.dropped_constant_features.length}</Tag>
          <Tag color="volcano">High Missing: {validation.dropped_high_missing_features.length}</Tag>
        </Space>
        {allDropped.length > 0 && (
          <Table
            dataSource={allDropped.map((d, i) => ({ ...d, key: i }))}
            columns={[
              ...FEATURE_COLUMNS,
              {
                title: 'Category',
                dataIndex: 'category',
                key: 'category',
                render: (cat: string) => <Tag>{cat}</Tag>,
              },
            ]}
            size="small"
            pagination={false}
            scroll={{ y: 200 }}
          />
        )}
      </Space>
    </Card>
  );
};

export default ColumnFilteringCard;
