import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { PreprocessingSummary } from '../types';

interface Props {
  summary: PreprocessingSummary;
}

const modeTag = (mode?: string | null) => {
  if (!mode || mode === 'none') return null;
  const color = mode === 'fold_safe' ? 'purple' : 'green';
  const label = mode === 'fold_safe' ? 'Fold-Safe' : 'Global';
  return <Tag color={color} style={{ marginLeft: 4 }}>{label}</Tag>;
};

const boolTag = (value: boolean, mode?: string | null) => (
  <span>
    <Tag color={value ? 'blue' : 'default'}>
      {value ? 'Executed' : 'Not Executed'}
    </Tag>
    {value && modeTag(mode)}
  </span>
);

const PreprocessingSummaryCard: React.FC<Props> = ({ summary }) => {
  const foldDeferred = summary.fold_safe_deferred as Record<string, unknown> | undefined;
  const hasFoldOps = Boolean(foldDeferred?.has_deferred);
  const nDeferred = Number(foldDeferred?.n_deferred_operations) || 0;

  return (
    <Card title="Preprocessing Summary" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Imputation">
          {boolTag(summary.imputation_executed, summary.imputation_execution_mode)}
        </Descriptions.Item>
        <Descriptions.Item label="Scaling">
          {boolTag(summary.scaling_executed, summary.scaling_execution_mode)}
        </Descriptions.Item>
        <Descriptions.Item label="Feature Selection">
          {boolTag(summary.feature_selection_executed, summary.feature_selection_execution_mode)}
        </Descriptions.Item>
        <Descriptions.Item label="Categorical Encoding">
          {boolTag(summary.categorical_encoding_executed)}
        </Descriptions.Item>
        <Descriptions.Item label="Pipeline Artifact ID" span={2}>
          {summary.preprocessing_pipeline_artifact_id || <Tag>N/A</Tag>}
        </Descriptions.Item>
        {hasFoldOps && (
          <Descriptions.Item label="Fold-Safe Ops" span={2}>
            <Tag color="purple">{nDeferred} operation(s) deferred to CV fold execution</Tag>
          </Descriptions.Item>
        )}
      </Descriptions>
    </Card>
  );
};

export default PreprocessingSummaryCard;
