import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs } from 'antd';
import { createInterpretation, rerunInterpretation } from '../../../api/taskInterpretationApi';
import { TaskInterpretationResponse } from '../types';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

const STATUS_COLORS: Record<string, string> = {
  interpreted: 'success',
  interpreted_with_warning: 'warning',
  failed: 'error',
  blocked: 'default',
};

interface TaskInterpretationPanelProps {
  taskId: string;
  initialResult?: TaskInterpretationResponse;
}

const TaskInterpretationPanel: React.FC<TaskInterpretationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskInterpretationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('interpretation');

  const handleRunInterpretation = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createInterpretation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run interpretation.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunInterpretation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run interpretation.');
    } finally {
      setLoading(false);
    }
  };

  const renderInterpretation = () => {
    if (!result) return <EmptyState description="No interpretation result available." />;

    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small" title="Interpretation Result">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Interpretation ID">{result.interpretation_id}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <StatusBadge label={result.status} color={STATUS_COLORS[result.status]} />
            </Descriptions.Item>
            <Descriptions.Item label="Task Type">{result.interpreted_task_type || '-'}</Descriptions.Item>
            <Descriptions.Item label="Input Modality">{result.interpreted_input_modality || '-'}</Descriptions.Item>
            <Descriptions.Item label="Material Domain">{result.interpreted_material_domain || '-'}</Descriptions.Item>
            <Descriptions.Item label="Confidence Score">{result.confidence_score ?? '-'}</Descriptions.Item>
          </Descriptions>
        </Card>

        {result.interpreted_prediction_target && (
          <Card size="small" title="Prediction Target">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Normalized">
                {result.interpreted_prediction_target.normalized_target}
              </Descriptions.Item>
              <Descriptions.Item label="Category">
                {result.interpreted_prediction_target.target_category}
              </Descriptions.Item>
              <Descriptions.Item label="Unit">
                {result.interpreted_prediction_target.target_unit || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Description">
                {result.interpreted_prediction_target.target_description || '-'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {result.modeling_intent && (
          <Card size="small" title="Modeling Intent">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Primary Goal">{result.modeling_intent.primary_goal}</Descriptions.Item>
              <Descriptions.Item label="Secondary Goals">
                {result.modeling_intent.secondary_goals?.join(', ') || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Optimization">
                {result.modeling_intent.optimization_direction}
              </Descriptions.Item>
              <Descriptions.Item label="Preferred Metric">
                {result.modeling_intent.preferred_metric}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {result.dataset_intent && (
          <Card size="small" title="Dataset Intent">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Reference">
                {result.dataset_intent.dataset_reference || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Expected Input">
                {result.dataset_intent.expected_input_columns?.join(', ') || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Target Column">
                {result.dataset_intent.expected_target_column || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Requires Structure File">
                {result.dataset_intent.requires_structure_file ? 'Yes' : 'No'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {result.planning_hint && (
          <Card size="small" title="Planning Hint">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Task Family">{result.planning_hint.task_family}</Descriptions.Item>
              <Descriptions.Item label="Input Representation">
                {result.planning_hint.input_representation}
              </Descriptions.Item>
              <Descriptions.Item label="Feature Engineering">
                {result.planning_hint.requires_feature_engineering ? 'Yes' : 'No'}
              </Descriptions.Item>
              <Descriptions.Item label="Interpretability Required">
                {result.planning_hint.requires_model_interpretability ? 'Yes' : 'No'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {result.constraint_interpretation && (
          <Card size="small" title="Constraint Interpretation">
            {result.constraint_interpretation.hard_constraints &&
              result.constraint_interpretation.hard_constraints.length > 0 && (
                <Descriptions.Item label="Hard">
                  {result.constraint_interpretation.hard_constraints.join(', ')}
                </Descriptions.Item>
              )}
            {result.constraint_interpretation.soft_constraints &&
              result.constraint_interpretation.soft_constraints.length > 0 && (
                <Descriptions.Item label="Soft">
                  {result.constraint_interpretation.soft_constraints.join(', ')}
                </Descriptions.Item>
              )}
            {result.constraint_interpretation.potential_conflicts &&
              result.constraint_interpretation.potential_conflicts.length > 0 && (
                <Descriptions.Item label="Conflicts">
                  {result.constraint_interpretation.potential_conflicts.join(', ')}
                </Descriptions.Item>
              )}
          </Card>
        )}

        {result.recommended_defaults && (
          <Card size="small" title="Recommended Defaults">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Metric">
                {result.recommended_defaults.evaluation_metric}
              </Descriptions.Item>
              <Descriptions.Item label="Validation">
                {result.recommended_defaults.validation_strategy}
              </Descriptions.Item>
              <Descriptions.Item label="Baseline Required">
                {result.recommended_defaults.baseline_requirement ? 'Yes' : 'No'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {result.ambiguities && result.ambiguities.length > 0 && (
          <WarningBox warnings={result.ambiguities.map(a => `[${a.severity}] ${a.field}: ${a.message}`)} />
        )}

        {result.llm_reasoning_summary && (
          <Card size="small" title="AI Reasoning">
            <p style={{ margin: 0, color: '#333', fontSize: 14, lineHeight: 1.5 }}>
              {result.llm_reasoning_summary}
            </p>
          </Card>
        )}
      </Space>
    );
  };

  const tabItems = [
    { key: 'interpretation', label: 'Interpretation', children: renderInterpretation() },
    {
      key: 'json',
      label: 'Full JSON',
      children: result ? (
        <JsonViewer data={result} />
      ) : (
        <EmptyState description="Run interpretation to see JSON output." />
      ),
    },
  ];

  return (
    <PanelContainer
      title="AI Task Interpretation"
      description="Run AI-based semantic interpretation on the submitted task specification."
      accentColor={pipelineAccent.interpretation}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRunInterpretation} loading={loading}>
          {loading ? 'Running...' : 'Run Interpretation'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Interpretation
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            {result.warnings && result.warnings.length > 0 && (
              <WarningBox warnings={result.warnings} />
            )}
            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No interpretation result yet. Click &quot;Run Interpretation&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default TaskInterpretationPanel;
