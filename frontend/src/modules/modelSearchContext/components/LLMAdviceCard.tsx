import React from 'react';
import { Card, Descriptions, Tag, Progress } from 'antd';
import { LLMStrategyAdvice } from '../types';

interface Props {
  advice: LLMStrategyAdvice;
}

const LLMAdviceCard: React.FC<Props> = ({ advice }) => {
  const confidencePct = Math.round((advice.confidence_score || 0) * 100);

  return (
    <Card title="LLM Strategy Advice" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Confidence" span={2}>
          <Progress percent={confidencePct} size="small" status={confidencePct >= 70 ? 'success' : 'normal'} />
        </Descriptions.Item>
        <Descriptions.Item label="Candidate Models" span={2}>
          {advice.candidate_model_families.length > 0 ? (
            advice.candidate_model_families.map((m) => <Tag key={m} color="blue">{m}</Tag>)
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Baseline Models" span={2}>
          {advice.baseline_models.length > 0 ? (
            advice.baseline_models.map((m) => <Tag key={m} color="geekblue">{m}</Tag>)
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Model Bias">
          <Tag color="purple">{advice.preferred_model_bias || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="HPO Method">
          <Tag color="cyan">{advice.hpo_search_method || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="HPO Budget">
          <Tag color={advice.hpo_budget_level === 'low' ? 'orange' : advice.hpo_budget_level === 'high' ? 'green' : 'blue'}>
            {advice.hpo_budget_level}
          </Tag>
        </Descriptions.Item>
        <Descriptions.Item label="Max Trials">{advice.max_trials}</Descriptions.Item>
        <Descriptions.Item label="Validation Strategy">
          <Tag>{advice.validation_split_strategy || 'N/A'}</Tag>
        </Descriptions.Item>
        <Descriptions.Item label="CV Splits">{advice.n_splits}</Descriptions.Item>
        {advice.adjustment_reasons.length > 0 && (
          <Descriptions.Item label="Adjustment Reasons" span={2}>
            {advice.adjustment_reasons.map((r, i) => (
              <Tag key={i} color="orange">{r}</Tag>
            ))}
          </Descriptions.Item>
        )}
        {advice.risk_notes.length > 0 && (
          <Descriptions.Item label="Risk Notes" span={2}>
            {advice.risk_notes.map((r, i) => (
              <Tag key={i} color="red">{r}</Tag>
            ))}
          </Descriptions.Item>
        )}
      </Descriptions>
    </Card>
  );
};

export default LLMAdviceCard;
