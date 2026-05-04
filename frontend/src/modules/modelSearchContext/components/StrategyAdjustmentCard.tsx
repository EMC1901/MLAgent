import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { StrategyAdjustment } from '../types';

interface Props {
  adjustment: StrategyAdjustment;
}

const adjTag = (adjusted: boolean) => (
  <Tag color={adjusted ? 'blue' : 'default'}>
    {adjusted ? 'Adjusted' : 'Unchanged'}
  </Tag>
);

const StrategyAdjustmentCard: React.FC<Props> = ({ adjustment }) => {
  return (
    <Card title="Strategy Adjustments" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Model Strategy">{adjTag(adjustment.model_strategy_adjusted)}</Descriptions.Item>
        <Descriptions.Item label="HPO Strategy">{adjTag(adjustment.hpo_strategy_adjusted)}</Descriptions.Item>
        <Descriptions.Item label="Validation Strategy">{adjTag(adjustment.validation_strategy_adjusted)}</Descriptions.Item>
        <Descriptions.Item label="Evaluation Strategy">{adjTag(adjustment.evaluation_strategy_adjusted)}</Descriptions.Item>
        {adjustment.adjustment_reasons.length > 0 && (
          <Descriptions.Item label="Reasons" span={2}>
            {adjustment.adjustment_reasons.map((r, i) => (
              <Tag key={i} color="purple">{r}</Tag>
            ))}
          </Descriptions.Item>
        )}
      </Descriptions>
    </Card>
  );
};

export default StrategyAdjustmentCard;
