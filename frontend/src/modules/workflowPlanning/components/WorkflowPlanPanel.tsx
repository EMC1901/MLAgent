import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Table } from 'antd';
import { createWorkflowPlan, rerunWorkflowPlan } from '../../../api/workflowPlanningApi';
import { WorkflowPlanResponse, FeatureStrategy, DecisionRationale, SelectedFeatureAction, RejectedFeatureAction, SelectedModelAction, RejectedModelAction, ModelDecisionRationale } from '../types';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface WorkflowPlanPanelProps {
  taskId: string;
  initialResult?: WorkflowPlanResponse;
}

const STATUS_COLORS: Record<string, string> = {
  planned: 'success',
  planned_with_warning: 'warning',
  failed: 'error',
};

const WorkflowPlanPanel: React.FC<WorkflowPlanPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowPlanResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRunPlanning = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await createWorkflowPlan(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run workflow planning.');
    } finally { setLoading(false); }
  };

  const handleRerun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await rerunWorkflowPlan(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run workflow planning.');
    } finally { setLoading(false); }
  };

  const renderRationale = (r: DecisionRationale | null | undefined) => {
    if (!r) return <span style={{ color: '#999', fontSize: 12 }}>No rationale</span>;
    return (
      <div style={{ fontSize: 12, color: '#777', display: 'flex', flexDirection: 'column', gap: 1 }}>
        {r.reason && <div><strong>Reason:</strong> {r.reason}</div>}
        {r.material_science_basis && <div><strong>Basis:</strong> {r.material_science_basis}</div>}
        {r.expected_benefit && <div><strong>Benefit:</strong> {r.expected_benefit}</div>}
        {r.risk && <div><strong>Risk:</strong> {r.risk}</div>}
        {r.fallback && <div><strong>Fallback:</strong> {r.fallback}</div>}
        {r.evidence && r.evidence.length > 0 && <div><strong>Evidence:</strong> {r.evidence.join('; ')}</div>}
      </div>
    );
  };

  const renderModelRationale = (r: ModelDecisionRationale | null | undefined) => {
    if (!r) return <span style={{ color: '#999', fontSize: 12 }}>No rationale</span>;
    return (
      <div style={{ fontSize: 12, color: '#777', display: 'flex', flexDirection: 'column', gap: 1 }}>
        {r.reason && <div><strong>Reason:</strong> {r.reason}</div>}
        {r.expected_performance && <div><strong>Expected Perf:</strong> {r.expected_performance}</div>}
        {r.risk && <div><strong>Risk:</strong> {r.risk}</div>}
        {r.fallback && <div><strong>Fallback:</strong> {r.fallback}</div>}
      </div>
    );
  };

  const renderSummary = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {result?.task_summary && (
        <Card size="small" title="Task Summary">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Type">{result.task_summary.task_type}</Descriptions.Item>
            <Descriptions.Item label="Input Modality">{result.task_summary.input_modality}</Descriptions.Item>
            <Descriptions.Item label="Prediction Target">{result.task_summary.prediction_target}</Descriptions.Item>
            <Descriptions.Item label="Material Domain">{result.task_summary.material_domain}</Descriptions.Item>
            <Descriptions.Item label="Primary Goal">{result.task_summary.primary_goal}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
      {result?.data_strategy && (
        <Card size="small" title="Data Strategy">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Target Column">{result.data_strategy.target_column}</Descriptions.Item>
            <Descriptions.Item label="Input Columns">{result.data_strategy.input_columns?.join(', ')}</Descriptions.Item>
            <Descriptions.Item label="Duplicate Handling">{result.data_strategy.duplicate_handling}</Descriptions.Item>
            <Descriptions.Item label="Missing Value Strategy">{result.data_strategy.missing_value_strategy}</Descriptions.Item>
          </Descriptions>
          {result.data_strategy.target_handling && (
            <p style={{ marginTop: 8 }}>
              <strong>Target Handling:</strong>{' '}
              {result.data_strategy.target_handling.requires_transformation_check
                ? `Transform (${result.data_strategy.target_handling.recommended_transformation})`
                : 'No transformation needed'}
            </p>
          )}
        </Card>
      )}
      {result?.preprocessing_intent && (
        <Card size="small" title="Preprocessing Intent">
          {result.preprocessing_intent.high_level_goals?.length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <strong>High-Level Goals:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {result.preprocessing_intent.high_level_goals.map((g, i) => <li key={i}>{g}</li>)}
              </ul>
            </div>
          )}
          {result.preprocessing_intent.risks_to_check_after_feature_engineering?.length > 0 && (
            <div>
              <strong>Risks to Check:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {result.preprocessing_intent.risks_to_check_after_feature_engineering.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </Card>
      )}
    </Space>
  );

  const renderFeatureStrategy = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {result?.feature_strategy && (
        <Card size="small" title="Feature Strategy">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Feature Type">{result.feature_strategy.feature_type}</Descriptions.Item>
            <Descriptions.Item label="Structure Features">{result.feature_strategy.requires_structure_features ? 'Yes' : 'No'}</Descriptions.Item>
            <Descriptions.Item label="Feature Selection">{result.feature_strategy.feature_selection_required ? 'Yes' : 'No'}</Descriptions.Item>
            <Descriptions.Item label="Feature Scaling">{result.feature_strategy.feature_scaling_required ? 'Yes' : 'No'}</Descriptions.Item>
          </Descriptions>

          {(result.feature_strategy.selected_feature_actions?.length ?? 0) > 0 && (
            <Card size="small" style={{ marginTop: 12, overflow: 'hidden' }}>
              <strong style={{ color: '#2e7d32' }}>Selected Feature Actions:</strong>
              <Table<SelectedFeatureAction>
                dataSource={result.feature_strategy.selected_feature_actions?.map((a, i) => ({ ...a, key: i })) || []}
                columns={[
                  { title: 'Action', dataIndex: 'action_id', key: 'action', width: 100 },
                  { title: 'Capability', dataIndex: 'capability_id', key: 'capability', width: 140, render: (v: string) => <StatusBadge label={v} color="success" /> },
                  { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 80 },
                  { title: 'Output Group', dataIndex: 'output_feature_group', key: 'group', width: 120 },
                  { title: 'Rationale', key: 'rationale', render: (_: unknown, r: SelectedFeatureAction) => renderRationale(r.decision_rationale) },
                ]}
                size="small"
                pagination={false}
                scroll={{ x: 800 }}
                style={{ marginTop: 8 }}
              />
            </Card>
          )}

          {(result.feature_strategy.rejected_feature_actions?.length ?? 0) > 0 && (
            <Card size="small" style={{ marginTop: 12 }}>
              <strong style={{ color: '#c62828' }}>Rejected Feature Actions:</strong>
              {result.feature_strategy.rejected_feature_actions?.map((a: RejectedFeatureAction, i: number) => (
                <div key={i} style={{ fontSize: 12, marginLeft: 8 }}>{a.capability_id}: {a.reason}</div>
              ))}
            </Card>
          )}

          {(result.feature_strategy.executable_featurizers?.length ?? 0) > 0 && (
            <div style={{ marginTop: 8 }}>
              <strong>Executable Featurizers: </strong>
              <Space wrap size={[4, 4]}>
                {result.feature_strategy.executable_featurizers?.map((f, i) => <StatusBadge key={i} label={f} color="success" />)}
              </Space>
            </div>
          )}
        </Card>
      )}
    </Space>
  );

  const renderModelStrategy = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {result?.model_strategy && (
        <Card size="small" title="Model Strategy">
          <p><strong>Preferred Bias:</strong> {result.model_strategy.preferred_model_bias}</p>

          {result.model_strategy.model_selection_rationale_summary && (
            <Card size="small" style={{ marginBottom: 8 }}>
              <strong>Selection Rationale:</strong>
              <p style={{ marginTop: 4, color: '#333', fontSize: 14, lineHeight: 1.5 }}>
                {result.model_strategy.model_selection_rationale_summary}
              </p>
            </Card>
          )}

          {(result.model_strategy.selected_model_actions?.length ?? 0) > 0 && (
            <Card size="small" style={{ marginBottom: 8, overflow: 'hidden' }}>
              <strong style={{ color: '#2e7d32' }}>Selected Models:</strong>
              <Table<SelectedModelAction>
                dataSource={result.model_strategy.selected_model_actions?.map((a, i) => ({ ...a, key: i })) || []}
                columns={[
                  { title: 'Action', dataIndex: 'action_id', key: 'action', width: 100 },
                  { title: 'Family', dataIndex: 'model_family', key: 'family', width: 120, render: (v: string) => <StatusBadge label={v} color="#1565c0" /> },
                  { title: 'Priority', dataIndex: 'priority', key: 'priority', width: 80 },
                  { title: 'Expected Perf', key: 'perf', width: 130, render: (_: unknown, r: SelectedModelAction) => r.decision_rationale?.expected_performance || '-' },
                  { title: 'Rationale', key: 'rationale', render: (_: unknown, r: SelectedModelAction) => renderModelRationale(r.decision_rationale) },
                ]}
                size="small"
                pagination={false}
                scroll={{ x: 700 }}
                style={{ marginTop: 8 }}
              />
            </Card>
          )}

          {(result.model_strategy.rejected_model_actions?.length ?? 0) > 0 && (
            <Card size="small" style={{ marginBottom: 8 }}>
              <strong style={{ color: '#c62828' }}>Rejected Models:</strong>
              {result.model_strategy.rejected_model_actions?.map((a: RejectedModelAction, i: number) => (
                <div key={i} style={{ fontSize: 12, marginLeft: 8 }}>
                  <StatusBadge label={a.model_family} color="error" /> {a.reason}
                </div>
              ))}
            </Card>
          )}

          {(!result.model_strategy.selected_model_actions || result.model_strategy.selected_model_actions.length === 0) && (
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Candidate Models">
                <Space wrap size={[4, 4]}>
                  {result.model_strategy.candidate_model_families?.map((m, i) => <StatusBadge key={i} label={m} color="#1565c0" />)}
                </Space>
              </Descriptions.Item>
              <Descriptions.Item label="Baseline Models">
                <Space wrap size={[4, 4]}>
                  {result.model_strategy.baseline_models?.map((m, i) => <StatusBadge key={i} label={m} color="#6a1b9a" />)}
                </Space>
              </Descriptions.Item>
            </Descriptions>
          )}
        </Card>
      )}
    </Space>
  );

  const renderValidationAndMore = () => (
    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
      {result?.validation_strategy && (
        <Card size="small" title="Validation Strategy">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Split">{result.validation_strategy.split_strategy}</Descriptions.Item>
            <Descriptions.Item label="n_splits">{result.validation_strategy.n_splits}</Descriptions.Item>
            {result.validation_strategy.test_size != null && <Descriptions.Item label="Test Size">{result.validation_strategy.test_size}</Descriptions.Item>}
            <Descriptions.Item label="Stratification">{result.validation_strategy.stratification_required ? 'Yes' : 'No'}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
      {result?.evaluation_strategy && (
        <Card size="small" title="Evaluation Strategy">
          <Descriptions column={1} size="small">
            <Descriptions.Item label="Primary Metric">{result.evaluation_strategy.primary_metric}</Descriptions.Item>
            <Descriptions.Item label="Secondary">{result.evaluation_strategy.secondary_metrics?.join(', ')}</Descriptions.Item>
            <Descriptions.Item label="Direction">{result.evaluation_strategy.metric_direction}</Descriptions.Item>
          </Descriptions>
        </Card>
      )}
      {result?.hpo_strategy && (
        <Card size="small" title="HPO Strategy">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Enabled">{result.hpo_strategy.enabled ? 'Yes' : 'No'}</Descriptions.Item>
            {result.hpo_strategy.enabled && (
              <>
                <Descriptions.Item label="Search Method">{result.hpo_strategy.search_method}</Descriptions.Item>
                <Descriptions.Item label="Budget">{result.hpo_strategy.budget_level} ({result.hpo_strategy.max_trials} trials)</Descriptions.Item>
              </>
            )}
          </Descriptions>
        </Card>
      )}
      {result?.interpretability_strategy && (
        <Card size="small" title="Interpretability Strategy">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Enabled">{result.interpretability_strategy.enabled ? 'Yes' : 'No'}</Descriptions.Item>
            {result.interpretability_strategy.enabled && (
              <>
                <Descriptions.Item label="Priority">{result.interpretability_strategy.priority}</Descriptions.Item>
                <Descriptions.Item label="Methods">
                  <Space wrap size={[4, 4]}>
                    {result.interpretability_strategy.methods?.map((m, i) => <StatusBadge key={i} label={m} color="#00838f" />)}
                  </Space>
                </Descriptions.Item>
              </>
            )}
          </Descriptions>
        </Card>
      )}

      {result?.pipeline_generation_input && (
        <Card size="small" title="Pipeline Generation Input">
          <Space direction="vertical">
            {result.pipeline_generation_input.pipeline_steps?.map((step, i) => (
              <Space key={i}>
                <span style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: 20, height: 20, borderRadius: '50%', backgroundColor: '#1976d2',
                  color: '#fff', fontSize: 11, fontWeight: 600,
                }}>
                  {i + 1}
                </span>
                <span>{step}</span>
              </Space>
            ))}
          </Space>
        </Card>
      )}

      {result?.workflow_rationale && (
        <Card size="small" title="Workflow Rationale">
          {result.workflow_rationale.overall_reasoning_summary && (
            <p style={{ color: '#333', fontSize: 14, lineHeight: 1.5 }}>
              {result.workflow_rationale.overall_reasoning_summary}
            </p>
          )}
          {result.workflow_rationale.key_assumptions?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <strong>Key Assumptions:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {result.workflow_rationale.key_assumptions.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            </div>
          )}
          {result.workflow_rationale.known_risks?.length > 0 && (
            <div style={{ marginTop: 8 }}>
              <strong>Known Risks:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {result.workflow_rationale.known_risks.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </Card>
      )}

      {result?.execution_hints && (
        <Card size="small" title="Execution Hints">
          {result.execution_hints.module_order?.length > 0 && (
            <div>
              <strong>Module Order: </strong>
              <Space wrap size={[4, 4]}>
                {result.execution_hints.module_order.map((m, i) => (
                  <StatusBadge key={i} label={`${i + 1}. ${m}`} color="#00838f" />
                ))}
              </Space>
            </div>
          )}
        </Card>
      )}

      {result?.llm_reasoning_summary && (
        <Card size="small" title="AI Reasoning Summary">
          <p style={{ color: '#333', fontSize: 14, lineHeight: 1.5 }}>{result.llm_reasoning_summary}</p>
        </Card>
      )}
    </Space>
  );

  const tabItems = [
    { key: 'summary', label: 'Summary', children: renderSummary() },
    { key: 'features', label: 'Feature Strategy', children: renderFeatureStrategy() },
    { key: 'model', label: 'Model Strategy', children: renderModelStrategy() },
    { key: 'planning', label: 'Validation & More', children: renderValidationAndMore() },
    {
      key: 'json',
      label: 'Full JSON',
      children: result ? <JsonViewer data={result} /> : <EmptyState description="Run planning to see JSON output." />,
    },
  ];

  return (
    <PanelContainer
      title="AI-guided Workflow Planning"
      description="Generate a structured machine learning workflow plan based on task specification, task interpretation, and dataset profiling results."
      accentColor={pipelineAccent.workflowPlan}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRunPlanning} loading={loading}>
          {loading ? 'Planning...' : 'Run Workflow Planning'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Planning
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Plan ID">{result.workflow_plan_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={result.status} color={STATUS_COLORS[result.status] || 'default'} />
                </Descriptions.Item>
                <Descriptions.Item label="Confidence">{result.confidence_score}</Descriptions.Item>
                {result.fe_registry_snapshot_version && (
                  <Descriptions.Item label="Registry">{result.fe_registry_snapshot_version}</Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            {result.planning_warnings && result.planning_warnings.length > 0 && (
              <WarningBox warnings={result.planning_warnings} />
            )}
            {result.planning_assumptions && result.planning_assumptions.length > 0 && (
              <Card size="small" style={{ marginBottom: 16, backgroundColor: '#e3f2fd', border: '1px solid #90caf9' }}>
                <strong style={{ color: '#1565c0' }}>Planning Assumptions:</strong>
                <ul style={{ margin: '4px 0', paddingLeft: 20, color: '#1565c0' }}>
                  {result.planning_assumptions.map((a, i) => <li key={i}>{a}</li>)}
                </ul>
              </Card>
            )}

            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No workflow plan yet. Click &quot;Run Workflow Planning&quot; to generate one." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default WorkflowPlanPanel;
