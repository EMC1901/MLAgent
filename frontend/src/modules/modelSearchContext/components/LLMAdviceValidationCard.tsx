import React from 'react';
import { Card, Descriptions, Tag, Alert } from 'antd';
import { SystemValidationResult } from '../types';

interface Props {
  validation: SystemValidationResult;
}

const LLMAdviceValidationCard: React.FC<Props> = ({ validation }) => {
  return (
    <Card title="LLM Advice Validation" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Is Valid">
          <Tag color={validation.is_valid ? 'success' : 'error'}>
            {validation.is_valid ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Fallback Applied">
          <Tag color={validation.fallback_applied ? 'warning' : 'default'}>
            {validation.fallback_applied ? 'Yes' : 'No'}
          </Tag>
        </Descriptions.Item>
      </Descriptions>
      {validation.rejected_suggestions.length > 0 && (
        <Alert
          type="warning"
          message="Rejected Suggestions"
          description={validation.rejected_suggestions.map((s, i) => (
            <div key={i} style={{ marginBottom: 4 }}>{i + 1}. {s}</div>
          ))}
          style={{ marginTop: 12 }}
        />
      )}
    </Card>
  );
};

export default LLMAdviceValidationCard;
