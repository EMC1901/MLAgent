import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs, Table, Popconfirm } from 'antd';
import {
  PlayCircleOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import {
  createIterationDecision, rerunIterationDecision,
  adoptRevisedPlan, checkNeedsFreshDecision,
} from '../../../api/iterationDecisionApi';
import { createFeatureEngineering } from '../../../api/featureEngineeringApi';
import { createFeaturePreprocessing } from '../../../api/featurePreprocessingApi';
import { createModelSearchContext } from '../../../api/modelSearchContextApi';
import { createPipelineGeneration } from '../../../api/pipelineGenerationApi';
import { createPipelineExecution } from '../../../api/pipelineExecutionApi';
import { createMetricEvaluation } from '../../../api/metricEvaluationApi';
import {
  IterationDecisionResponse, DecisionReasoning, EvidenceBundle,
  IterationPlan, RevisedWorkflowPlan, IterationRerunPlan,
  SystemChecks, StopRationale, AdoptRevisedPlanResult,
} from '../types';
import {
  STATUS_COLORS, STATUS_LABELS, DECISION_COLORS, DECISION_LABELS,
  CONFIDENCE_COLORS, CONFIDENCE_LABELS, COMPLETION_COLORS,
  GAP_MAGNITUDE_COLORS, IMPROVEMENT_COLORS,
  STAGE_LABELS, STAGE_COLORS, ACTION_LABELS, ACTION_COLORS,
  DIMENSION_LABELS, DIMENSION_COLORS, STOP_CATEGORY_LABELS,
} from '../constants';
import {
  PanelContainer, StatusBadge, WarningBox, ErrorBox,
  JsonViewer, EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';
import { Alert } from 'antd';

interface IterationDecisionPanelProps {
  taskId: string;
  initialResult?: IterationDecisionResponse;
  onRerunComplete?: () => void;
}

const IterationDecisionPanel: React.FC<IterationDecisionPanelProps> = ({ taskId, initialResult, onRerunComplete }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<IterationDecisionResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('decision');
  const [adopting, setAdopting] = useState(false);
  const [adoptResult, setAdoptResult] = useState<AdoptRevisedPlanResult | null>(null);
  const [rerunProgress, setRerunProgress] = useState<string[]>([]);
  const [rerunError, setRerunError] = useState<string | null>(null);

  const handleRun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      let forceRerun = false;
      try {
        const freshCheck = await checkNeedsFreshDecision(taskId);
        if (freshCheck.success && freshCheck.data.needs_fresh) forceRerun = true;
      } catch { /* proceed */ }
      const response = await createIterationDecision(taskId, { force_rerun: forceRerun });
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run iteration decision.');
    } finally { setLoading(false); }
  };

  const handleRerun = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const response = await rerunIterationDecision(taskId);
      if (response.success) setResult(response.data);
      else setError(response.message);
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run iteration decision.');
    } finally { setLoading(false); }
  };

  const handleAdoptAndRerun = async () => {
    if (!result?.iteration_decision_id) return;
    setAdopting(true); setRerunError(null); setRerunProgress([]); setAdoptResult(null);
    try {
      setRerunProgress(['Adopting revised plan...']);
      const adoptResp = await adoptRevisedPlan(result.iteration_decision_id);
      if (!adoptResp.success || !adoptResp.data.adopted) {
        setRerunError(adoptResp.message || 'Failed to adopt revised plan.');
        setAdopting(false); return;
      }
      setAdoptResult(adoptResp.data);
      setRerunProgress(prev => [...prev, 'Plan adopted as ' + adoptResp.data.adopted_workflow_plan_id]);

      const stages = adoptResp.data.rerun_stages || [];
      const STAGE_API: Record<string, (taskId: string) => Promise<any>> = {
        workflow_planning: async () => null,
        feature_engineering: createFeatureEngineering,
        feature_preprocessing: createFeaturePreprocessing,
        model_search_context: createModelSearchContext,
        pipeline_generation: createPipelineGeneration,
        pipeline_execution: createPipelineExecution,
        metric_evaluation: createMetricEvaluation,
      };

      let hasError = false;
      for (let i = 0; i < stages.length; i++) {
        const stage = stages[i];
        if (stage === 'workflow_planning') continue;
        const apiFn = STAGE_API[stage];
        if (!apiFn) { setRerunProgress(prev => [...prev, `${stage}: skipped (no handler)`]); continue; }
        setRerunProgress(prev => [...prev, `Running ${stage} (${i + 1}/${stages.length})...`]);
        try {
          const resp = await apiFn(taskId);
          setRerunProgress(prev => [...prev, `${stage}: ${resp.success ? 'completed successfully' : resp.message || 'completed with issues'}`]);
        } catch (err: any) {
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
          setRerunProgress(prev => [...prev, `${stage}: FAILED - ${msg || err.message}`]);
          setRerunError(`Rerun stopped at ${stage}: ${msg || err.message}`);
          hasError = true; break;
        }
      }
      if (!hasError) {
        setRerunProgress(prev => [...prev, 'All stages completed. Run Iteration Decision again to evaluate.']);
        onRerunComplete?.();
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setRerunError(msg || err.message || 'Adopt & Rerun failed.');
    } finally { setAdopting(false); }
  };

  const evidenceColumns = [
    { title: 'Type', dataIndex: 'evidence_type', key: 'type', render: (v: string) => <StatusBadge label={v} /> },
    { title: 'Source Module', dataIndex: 'source_module', key: 'module' },
    { title: 'Source Field', dataIndex: 'source_field', key: 'field' },
    { title: 'Value', dataIndex: 'value', key: 'value', render: (v: unknown) => typeof v === 'object' ? JSON.stringify(v) : String(v ?? '-') },
    { title: 'Interpretation', dataIndex: 'interpretation', key: 'interp' },
  ];

  const stageChangeColumns = [
    { title: 'Stage', dataIndex: 'stage', key: 'stage', render: (v: string) => <StatusBadge label={STAGE_LABELS[v] || v} color={STAGE_COLORS[v]} /> },
    { title: 'Action', dataIndex: 'action', key: 'action', render: (v: string) => <StatusBadge label={ACTION_LABELS[v] || v} color={ACTION_COLORS[v]} /> },
    { title: 'Description', dataIndex: 'description', key: 'desc' },
    { title: 'Rationale', dataIndex: 'rationale', key: 'rationale' },
  ];

  const tabItems = [
    { key: 'decision', label: 'Decision', children: result ? (
      <Card size="small" title="Iteration Decision">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Decision">
            <StatusBadge label={DECISION_LABELS[result.decision || ''] || result.decision || 'N/A'} color={DECISION_COLORS[result.decision || '']} />
          </Descriptions.Item>
          <Descriptions.Item label="Confidence">
            <StatusBadge label={CONFIDENCE_LABELS[result.decision_confidence || ''] || result.decision_confidence || 'N/A'} color={CONFIDENCE_COLORS[result.decision_confidence || '']} />
          </Descriptions.Item>
          <Descriptions.Item label="Status">
            <StatusBadge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status]} />
          </Descriptions.Item>
          <Descriptions.Item label="Iteration">#{result.iteration_index}</Descriptions.Item>
          <Descriptions.Item label="Ready for Iteration">
            <span style={{ color: result.ready_for_iteration ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {result.ready_for_iteration ? 'Yes' : 'No'}
            </span>
          </Descriptions.Item>
        </Descriptions>
      </Card>
    ) : <EmptyState description="Run decision to see result." /> },
    { key: 'reasoning', label: 'Reasoning', children: result?.reasoning ? (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small" title="Task Completion Assessment">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Completion">
              <StatusBadge label={result.reasoning.task_completion.completion_level} color={COMPLETION_COLORS[result.reasoning.task_completion.completion_level]} />
            </Descriptions.Item>
            <Descriptions.Item label="Target Metric">{result.reasoning.task_completion.target_metric || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="Physics Constraints">
              <span style={{ color: result.reasoning.task_completion.physics_constraints_satisfied ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.reasoning.task_completion.physics_constraints_satisfied ? 'Satisfied' : 'Violated'}
              </span>
            </Descriptions.Item>
          </Descriptions>
          {result.reasoning.task_completion.gap_description && <p style={{ marginTop: 8, fontSize: 14 }}>{result.reasoning.task_completion.gap_description}</p>}
          {result.reasoning.task_completion.physics_violations?.length > 0 && <WarningBox warnings={result.reasoning.task_completion.physics_violations} />}
        </Card>
        <Card size="small" title="Performance Assessment">
          <p style={{ fontSize: 14, lineHeight: 1.5 }}>{result.reasoning.performance_assessment || 'N/A'}</p>
        </Card>
        <Card size="small" title="Gap Analysis">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Primary Gap">{result.reasoning.gap_analysis.primary_gap || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="Magnitude">
              <StatusBadge label={result.reasoning.gap_analysis.gap_magnitude} color={GAP_MAGNITUDE_COLORS[result.reasoning.gap_analysis.gap_magnitude]} />
            </Descriptions.Item>
          </Descriptions>
          {result.reasoning.gap_analysis.contributing_factors?.length > 0 && (
            <div style={{ marginTop: 8 }}><strong>Contributing Factors:</strong><ul style={{ paddingLeft: 20 }}>{result.reasoning.gap_analysis.contributing_factors.map((f, i) => <li key={i}>{f}</li>)}</ul></div>
          )}
        </Card>
        <Card size="small" title="Root Cause Analysis">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Primary Cause">{result.reasoning.root_cause.primary_root_cause || 'N/A'}</Descriptions.Item>
            <Descriptions.Item label="Dimension">
              <StatusBadge label={DIMENSION_LABELS[result.reasoning.root_cause.dimension] || result.reasoning.root_cause.dimension} color={DIMENSION_COLORS[result.reasoning.root_cause.dimension]} />
            </Descriptions.Item>
            {result.reasoning.root_cause.upstream_stage_at_fault && (
              <Descriptions.Item label="Stage at Fault">
                <StatusBadge label={STAGE_LABELS[result.reasoning.root_cause.upstream_stage_at_fault] || result.reasoning.root_cause.upstream_stage_at_fault} color={STAGE_COLORS[result.reasoning.root_cause.upstream_stage_at_fault]} />
              </Descriptions.Item>
            )}
          </Descriptions>
          {result.reasoning.root_cause.causal_chain && <p style={{ marginTop: 8, fontSize: 14 }}><strong>Causal Chain:</strong> {result.reasoning.root_cause.causal_chain}</p>}
        </Card>
        <Card size="small" title="Improvement Potential">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Estimate">
              <StatusBadge label={result.reasoning.improvement_potential.estimate} color={IMPROVEMENT_COLORS[result.reasoning.improvement_potential.estimate]} />
            </Descriptions.Item>
            <Descriptions.Item label="Effort">{result.reasoning.improvement_potential.estimated_effort || 'N/A'}</Descriptions.Item>
          </Descriptions>
          {result.reasoning.improvement_potential.key_levers?.length > 0 && (
            <div style={{ marginTop: 8 }}><strong>Key Levers:</strong><ul style={{ paddingLeft: 20 }}>{result.reasoning.improvement_potential.key_levers.map((l, i) => <li key={i}>{l}</li>)}</ul></div>
          )}
        </Card>
        <Card size="small" title="Final Reasoning Summary">
          <p style={{ fontSize: 14, lineHeight: 1.5 }}>{result.reasoning.final_reasoning_summary || 'N/A'}</p>
        </Card>
      </Space>
    ) : <EmptyState description="No decision reasoning available." /> },
    { key: 'evidence', label: 'Evidence', children: result?.evidence_bundle ? (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {(['ml_performance', 'materials', 'workflow_quality', 'history_trends'] as const).map(section => {
          const items = result.evidence_bundle![section];
          const labels: Record<string, string> = { ml_performance: 'ML Performance', materials: 'Materials Science', workflow_quality: 'Workflow Quality', history_trends: 'History Trend' };
          return items && items.length > 0 ? (
            <Card key={section} size="small" title={`${labels[section]} Evidence (${items.length})`}>
              <Table dataSource={items.map((e, i) => ({ ...e, key: i }))} columns={evidenceColumns} size="small" pagination={false} />
            </Card>
          ) : null;
        })}
      </Space>
    ) : <EmptyState description="No evidence available." /> },
    { key: 'iteration_plan', label: 'Iteration Plan', children: result?.iteration_plan ? (
      <Card size="small" title="Iteration Plan">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Rerun From">
            <StatusBadge label={STAGE_LABELS[result.iteration_plan.rerun_from_stage] || result.iteration_plan.rerun_from_stage} color={STAGE_COLORS[result.iteration_plan.rerun_from_stage]} />
          </Descriptions.Item>
          <Descriptions.Item label="Remaining Iterations">{result.iteration_plan.estimated_remaining_iterations}</Descriptions.Item>
        </Descriptions>
        {result.iteration_plan.stage_changes?.length > 0 && (
          <Table
            dataSource={result.iteration_plan.stage_changes.map((sc, i) => ({ ...sc, key: i }))}
            columns={stageChangeColumns} size="small" pagination={false} style={{ marginTop: 8 }}
          />
        )}
      </Card>
    ) : <EmptyState description="No iteration plan available." /> },
    { key: 'revised_plan', label: 'Revised Plan', children: result?.revised_workflow_plan ? (
      <Card size="small" title="Revised Workflow Plan">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Status">{result.revised_workflow_plan.status}</Descriptions.Item>
          <Descriptions.Item label="Planning Mode">{result.revised_workflow_plan.planning_mode}</Descriptions.Item>
        </Descriptions>
        {result.revised_workflow_plan.llm_reasoning_summary && (
          <Card size="small" style={{ marginTop: 8 }}><strong>AI Reasoning:</strong><p style={{ marginTop: 4, fontSize: 14 }}>{result.revised_workflow_plan.llm_reasoning_summary}</p></Card>
        )}
      </Card>
    ) : <EmptyState description="No revised workflow plan." /> },
    { key: 'rerun_plan', label: 'Rerun Plan', children: result?.iteration_rerun_plan ? (
      <Card size="small" title="Iteration Rerun Plan">
        <Descriptions column={2} size="small">
          <Descriptions.Item label="Next Iteration">#{result.iteration_rerun_plan.next_iteration_index}</Descriptions.Item>
          <Descriptions.Item label="Entry Point">
            {result.iteration_rerun_plan.rerun_from_stage ? <StatusBadge label={STAGE_LABELS[result.iteration_rerun_plan.rerun_from_stage] || result.iteration_rerun_plan.rerun_from_stage} color={STAGE_COLORS[result.iteration_rerun_plan.rerun_from_stage]} /> : 'N/A'}
          </Descriptions.Item>
          <Descriptions.Item label="Stop If No Gain">
            <span style={{ color: result.iteration_rerun_plan.stop_after_next_iteration_if_no_gain ? '#c62828' : '#2e7d32', fontWeight: 600 }}>
              {result.iteration_rerun_plan.stop_after_next_iteration_if_no_gain ? 'Yes' : 'No'}
            </span>
          </Descriptions.Item>
        </Descriptions>
        <div style={{ marginTop: 8 }}>
          <strong>Rerun Stages: </strong>
          <Space wrap size={[4, 4]}>
            {(result.iteration_rerun_plan.rerun_stages || []).map(s => <StatusBadge key={s} label={STAGE_LABELS[s] || s} color={STAGE_COLORS[s]} />)}
          </Space>
        </div>
      </Card>
    ) : <EmptyState description="No rerun plan." /> },
    { key: 'stop', label: 'Stop Rationale', children: result?.stop_rationale ? (
      <Card size="small" title="Stop Rationale">
        <Descriptions column={1} size="small">
          <Descriptions.Item label="Category">{STOP_CATEGORY_LABELS[result.stop_rationale.category] || result.stop_rationale.category}</Descriptions.Item>
        </Descriptions>
        <p style={{ marginTop: 8, fontSize: 14 }}><strong>Primary Reason:</strong> {result.stop_rationale.primary_reason}</p>
        {result.stop_rationale.supporting_reasons?.length > 0 && (
          <div style={{ marginTop: 8 }}><strong>Supporting Reasons:</strong><ul style={{ paddingLeft: 20 }}>{result.stop_rationale.supporting_reasons.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
        )}
      </Card>
    ) : <EmptyState description="No stop rationale." /> },
    { key: 'system', label: 'System Checks', children: result?.system_checks ? (
      <Card size="small" title="System Checks">
        {[
          { label: 'ML Checks', items: ['weak_baseline_improvement', 'high_fold_variance', 'all_models_weak', 'hpo_budget_limited', 'candidate_underperforms_baseline', 'unstable_best_model'] },
          { label: 'Data Checks', items: ['small_sample_warning', 'feature_count_low', 'many_features_dropped'] },
          { label: 'Materials Checks', items: ['physics_constraint_violated', 'feature_materials_relevance_low', 'chemical_space_coverage_low'] },
          { label: 'Guard Checks', items: ['max_iterations_reached', 'no_improvement_trend', 'repeated_root_cause'] },
        ].map(group => (
          <Card key={group.label} size="small" style={{ marginBottom: 8 }} title={group.label}>
            <Descriptions column={2} size="small">
              {group.items.filter(key => (result.system_checks as any)[key] !== undefined).map(key => (
                <Descriptions.Item key={key} label={key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}>
                  <span style={{ color: (result.system_checks as any)[key] ? '#c62828' : '#4caf50', fontWeight: 600 }}>
                    {(result.system_checks as any)[key] ? 'TRIGGERED' : 'OK'}
                  </span>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        ))}
        {result.system_checks.warnings?.length > 0 && <WarningBox warnings={result.system_checks.warnings} />}
      </Card>
    ) : null },
    { key: 'json', label: 'Full JSON', children: result ? <JsonViewer data={result} /> : <EmptyState description="Run decision to see JSON output." /> },
  ];

  return (
    <PanelContainer
      title="Iteration Decision"
      description="Unified AI-based decision maker. Reviews materials task completion, model training results, and all upstream context to decide: ITERATE or STOP."
      accentColor={pipelineAccent.iterationDecision}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          {loading ? 'Deciding...' : 'Run Iteration Decision'}
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Decision
        </Button>
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Decision ID">{result.iteration_decision_id}</Descriptions.Item>
                <Descriptions.Item label="Status">
                  <StatusBadge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status]} />
                </Descriptions.Item>
                <Descriptions.Item label="Decision">
                  <StatusBadge label={DECISION_LABELS[result.decision || ''] || result.decision || 'N/A'} color={DECISION_COLORS[result.decision || '']} />
                </Descriptions.Item>
                <Descriptions.Item label="Iteration">#{result.iteration_index}</Descriptions.Item>
              </Descriptions>
            </Card>

            {result.warnings && result.warnings.length > 0 && <WarningBox warnings={result.warnings} />}
            {result.error_message && <ErrorBox message={result.error_message} />}

            {result.decision === 'iterate' && result.ready_for_iteration && (
              <Alert
                type="warning"
                message="Iterate: Adopt Revised Plan & Rerun Pipeline"
                description={
                  <Space direction="vertical" style={{ width: '100%' }} size="middle">
                    <span>The system recommends iteration. Adopting the revised plan creates a new WorkflowPlan and re-executes pipeline stages.</span>
                    {result.iteration_rerun_plan && (
                      <div>
                        <strong>Rerun Stages: </strong>
                        <Space wrap size={[4, 4]}>
                          {(result.iteration_rerun_plan.rerun_stages || []).map(s => (
                            <StatusBadge key={s} label={STAGE_LABELS[s] || s} color={STAGE_COLORS[s]} />
                          ))}
                        </Space>
                      </div>
                    )}
                    <Popconfirm
                      title="This will create a new WorkflowPlan and re-execute pipeline stages. Continue?"
                      onConfirm={handleAdoptAndRerun}
                      okText="Yes, Adopt & Rerun"
                      cancelText="Cancel"
                      okButtonProps={{ danger: true }}
                    >
                      <Button
                        type="primary"
                        danger
                        icon={<PlayCircleOutlined />}
                        loading={adopting}
                        size="large"
                      >
                        {adopting ? 'Adopting...' : 'Adopt & Rerun'}
                      </Button>
                    </Popconfirm>
                    {adoptResult && (
                      <Alert type="success" message={`Plan Adopted: ${adoptResult.adopted_workflow_plan_id}`} />
                    )}
                    {rerunProgress.length > 0 && (
                      <Card size="small" title="Rerun Progress">
                        <ul style={{ paddingLeft: 20, margin: 0 }}>
                          {rerunProgress.map((msg, i) => (
                            <li key={i} style={{
                              color: msg.includes('FAILED') ? '#c62828' : msg.includes('completed') ? '#2e7d32' : '#333',
                              fontSize: 13, marginBottom: 2,
                            }}>{msg}</li>
                          ))}
                        </ul>
                      </Card>
                    )}
                    {rerunError && <ErrorBox message={rerunError} />}
                    {!adopting && rerunProgress.some(m => m.includes('All stages completed')) && !rerunError && (
                      <Alert type="success" message="Pipeline re-execution complete. Run Iteration Decision again to evaluate the new results." />
                    )}
                  </Space>
                }
                showIcon
                icon={<ExclamationCircleOutlined />}
                style={{ marginBottom: 16 }}
              />
            )}

            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}
        {!result && !error && !loading && (
          <EmptyState description="No iteration decision yet. Click &quot;Run Iteration Decision&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default IterationDecisionPanel;
