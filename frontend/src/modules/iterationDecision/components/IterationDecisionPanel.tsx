import React, { useState } from 'react';
import {
  createIterationDecision,
  rerunIterationDecision,
  adoptRevisedPlan,
  checkNeedsFreshDecision,
} from '../../../api/iterationDecisionApi';
import { createFeatureEngineering } from '../../../api/featureEngineeringApi';
import { createFeaturePreprocessing } from '../../../api/featurePreprocessingApi';
import { createModelSearchContext } from '../../../api/modelSearchContextApi';
import { createPipelineGeneration } from '../../../api/pipelineGenerationApi';
import { createPipelineExecution } from '../../../api/pipelineExecutionApi';
import { createMetricEvaluation } from '../../../api/metricEvaluationApi';
import {
  IterationDecisionResponse,
  DecisionReasoning,
  EvidenceItem,
  EvidenceBundle,
  IterationPlan,
  StageChange,
  RevisedWorkflowPlan,
  IterationRerunPlan,
  SystemChecks,
  StopRationale,
  AdoptRevisedPlanResult,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  DECISION_COLORS,
  DECISION_LABELS,
  CONFIDENCE_COLORS,
  CONFIDENCE_LABELS,
  COMPLETION_COLORS,
  GAP_MAGNITUDE_COLORS,
  IMPROVEMENT_COLORS,
  STAGE_LABELS,
  STAGE_COLORS,
  ACTION_LABELS,
  ACTION_COLORS,
  DIMENSION_LABELS,
  DIMENSION_COLORS,
  STOP_CATEGORY_LABELS,
} from '../constants';

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
  const [showAdoptConfirm, setShowAdoptConfirm] = useState(false);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let forceRerun = false;
      try {
        const freshCheck = await checkNeedsFreshDecision(taskId);
        if (freshCheck.success && freshCheck.data.needs_fresh) {
          forceRerun = true;
        }
      } catch {
        // proceed with normal run
      }
      const response = await createIterationDecision(taskId, { force_rerun: forceRerun });
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run iteration decision.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunIterationDecision(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run iteration decision.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdoptAndRerun = async () => {
    if (!result?.iteration_decision_id) return;
    setAdopting(true);
    setRerunError(null);
    setRerunProgress([]);
    setAdoptResult(null);
    setShowAdoptConfirm(false);

    try {
      setRerunProgress(['Adopting revised plan...']);
      const adoptResp = await adoptRevisedPlan(result.iteration_decision_id);
      if (!adoptResp.success || !adoptResp.data.adopted) {
        setRerunError(adoptResp.message || 'Failed to adopt revised plan.');
        setAdopting(false);
        return;
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
        if (!apiFn) {
          setRerunProgress(prev => [...prev, `${stage}: skipped (no handler)`]);
          continue;
        }
        setRerunProgress(prev => [...prev, `Running ${stage} (${i + 1}/${stages.length})...`]);
        try {
          const resp = await apiFn(taskId);
          if (resp.success) {
            setRerunProgress(prev => [...prev, `${stage}: completed successfully`]);
          } else {
            setRerunProgress(prev => [...prev, `${stage}: ${resp.message || 'completed with issues'}`]);
          }
        } catch (err: any) {
          const detail = err.response?.data?.detail;
          const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
          setRerunProgress(prev => [...prev, `${stage}: FAILED - ${msg || err.message}`]);
          setRerunError(`Rerun stopped at ${stage}: ${msg || err.message}`);
          hasError = true;
          break;
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
    } finally {
      setAdopting(false);
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  // --- Render helpers ---

  const renderDecision = () => {
    if (!result) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Iteration Decision</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Decision: </strong>
            <Badge
              label={DECISION_LABELS[result.decision || ''] || result.decision || 'N/A'}
              color={DECISION_COLORS[result.decision || ''] || '#9e9e9e'}
            />
          </div>
          <div style={s.field}>
            <strong>Confidence: </strong>
            <Badge
              label={CONFIDENCE_LABELS[result.decision_confidence || ''] || result.decision_confidence || 'N/A'}
              color={CONFIDENCE_COLORS[result.decision_confidence || ''] || '#9e9e9e'}
            />
          </div>
          <div style={s.field}>
            <strong>Status: </strong>
            <Badge
              label={STATUS_LABELS[result.status] || result.status}
              color={STATUS_COLORS[result.status] || '#9e9e9e'}
            />
          </div>
          <div style={s.field}>
            <strong>Iteration: </strong>
            <span>#{result.iteration_index}</span>
          </div>
          <div style={s.field}>
            <strong>Ready for Iteration: </strong>
            <span style={{ color: result.ready_for_iteration ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {result.ready_for_iteration ? 'Yes' : 'No'}
            </span>
          </div>
        </div>
      </div>
    );
  };

  const renderReasoning = (reasoning: DecisionReasoning | null | undefined) => {
    if (!reasoning) return <p>No decision reasoning available.</p>;
    return (
      <div>
        {/* Task Completion */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Task Completion Assessment</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Completion: </strong>
              <Badge
                label={reasoning.task_completion.completion_level}
                color={COMPLETION_COLORS[reasoning.task_completion.completion_level] || '#9e9e9e'}
              />
            </div>
            <div style={s.field}>
              <strong>Target Metric: </strong>
              <span>{reasoning.task_completion.target_metric || 'N/A'}</span>
            </div>
            {reasoning.task_completion.target_value != null && (
              <div style={s.field}>
                <strong>Target Value: </strong>
                <span>{reasoning.task_completion.target_value}</span>
              </div>
            )}
            {reasoning.task_completion.actual_value != null && (
              <div style={s.field}>
                <strong>Actual Value: </strong>
                <span>{reasoning.task_completion.actual_value}</span>
              </div>
            )}
            <div style={s.field}>
              <strong>Physics Constraints: </strong>
              <span style={{ color: reasoning.task_completion.physics_constraints_satisfied ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {reasoning.task_completion.physics_constraints_satisfied ? 'Satisfied' : 'Violated'}
              </span>
            </div>
          </div>
          {reasoning.task_completion.gap_description && (
            <p style={s.summaryText}>{reasoning.task_completion.gap_description}</p>
          )}
          {reasoning.task_completion.physics_violations?.length > 0 && (
            <div style={s.warningBox}>
              <strong>Physics Violations:</strong>
              <ul style={s.list}>
                {reasoning.task_completion.physics_violations.map((v, i) => <li key={i}>{v}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Performance */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Performance Assessment</h4>
          <p style={s.summaryText}>{reasoning.performance_assessment || 'N/A'}</p>
        </div>

        {/* Gap Analysis */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Gap Analysis</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Primary Gap: </strong>
              <span>{reasoning.gap_analysis.primary_gap || 'N/A'}</span>
            </div>
            <div style={s.field}>
              <strong>Magnitude: </strong>
              <Badge
                label={reasoning.gap_analysis.gap_magnitude}
                color={GAP_MAGNITUDE_COLORS[reasoning.gap_analysis.gap_magnitude] || '#9e9e9e'}
              />
            </div>
          </div>
          {reasoning.gap_analysis.contributing_factors?.length > 0 && (
            <div style={s.field}>
              <strong>Contributing Factors:</strong>
              <ul style={s.list}>
                {reasoning.gap_analysis.contributing_factors.map((f, i) => <li key={i}>{f}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Root Cause */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Root Cause Analysis</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Primary Cause: </strong>
              <span>{reasoning.root_cause.primary_root_cause || 'N/A'}</span>
            </div>
            <div style={s.field}>
              <strong>Dimension: </strong>
              <Badge
                label={DIMENSION_LABELS[reasoning.root_cause.dimension] || reasoning.root_cause.dimension}
                color={DIMENSION_COLORS[reasoning.root_cause.dimension] || '#9e9e9e'}
              />
            </div>
            <div style={s.field}>
              <strong>Stage at Fault: </strong>
              {reasoning.root_cause.upstream_stage_at_fault ? (
                <Badge
                  label={STAGE_LABELS[reasoning.root_cause.upstream_stage_at_fault] || reasoning.root_cause.upstream_stage_at_fault}
                  color={STAGE_COLORS[reasoning.root_cause.upstream_stage_at_fault] || '#9e9e9e'}
                />
              ) : <span>N/A</span>}
            </div>
          </div>
          {reasoning.root_cause.causal_chain && (
            <p style={s.summaryText}><strong>Causal Chain:</strong> {reasoning.root_cause.causal_chain}</p>
          )}
        </div>

        {/* Improvement Potential */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Improvement Potential</h4>
          <div style={s.grid}>
            <div style={s.field}>
              <strong>Estimate: </strong>
              <Badge
                label={reasoning.improvement_potential.estimate}
                color={IMPROVEMENT_COLORS[reasoning.improvement_potential.estimate] || '#9e9e9e'}
              />
            </div>
            <div style={s.field}>
              <strong>Effort: </strong>
              <span>{reasoning.improvement_potential.estimated_effort || 'N/A'}</span>
            </div>
          </div>
          {reasoning.improvement_potential.key_levers?.length > 0 && (
            <div style={s.field}>
              <strong>Key Levers:</strong>
              <ul style={s.list}>
                {reasoning.improvement_potential.key_levers.map((l, i) => <li key={i}>{l}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Final Summary */}
        <div style={s.card}>
          <h4 style={s.cardTitle}>Final Reasoning Summary</h4>
          <p style={s.summaryText}>{reasoning.final_reasoning_summary || 'N/A'}</p>
        </div>
      </div>
    );
  };

  const renderEvidence = (bundle: EvidenceBundle | null | undefined) => {
    if (!bundle) return <p>No evidence available.</p>;
    const sections = [
      { key: 'ml_performance', label: 'ML Performance Evidence', items: bundle.ml_performance },
      { key: 'materials', label: 'Materials Science Evidence', items: bundle.materials },
      { key: 'workflow_quality', label: 'Workflow Quality Evidence', items: bundle.workflow_quality },
      { key: 'history_trends', label: 'History Trend Evidence', items: bundle.history_trends },
    ];
    return (
      <div>
        {sections.map(section => (
          <div key={section.key} style={s.card}>
            <h4 style={s.cardTitle}>{section.label} ({section.items?.length || 0})</h4>
            {section.items && section.items.length > 0 ? (
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Type</th>
                    <th style={s.th}>Source Module</th>
                    <th style={s.th}>Source Field</th>
                    <th style={s.th}>Value</th>
                    <th style={s.th}>Interpretation</th>
                  </tr>
                </thead>
                <tbody>
                  {section.items.map((e, i) => (
                    <tr key={i}>
                      <td style={s.td}><Badge label={e.evidence_type} /></td>
                      <td style={s.td}>{e.source_module}</td>
                      <td style={s.td}>{e.source_field}</td>
                      <td style={s.td}>{typeof e.value === 'object' ? JSON.stringify(e.value) : String(e.value ?? '-')}</td>
                      <td style={s.td}>{e.interpretation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : <p style={{ color: '#999', fontSize: '13px' }}>No evidence items.</p>}
          </div>
        ))}
      </div>
    );
  };

  const renderIterationPlan = (plan: IterationPlan | null | undefined) => {
    if (!plan) return <p>No iteration plan available.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Iteration Plan</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Rerun From: </strong>
            <Badge
              label={STAGE_LABELS[plan.rerun_from_stage] || plan.rerun_from_stage}
              color={STAGE_COLORS[plan.rerun_from_stage] || '#9e9e9e'}
            />
          </div>
          <div style={s.field}>
            <strong>Remaining Iterations: </strong>
            <span>{plan.estimated_remaining_iterations}</span>
          </div>
        </div>
        {plan.expected_improvement && (
          <div style={s.field}>
            <strong>Expected Improvement: </strong>
            <span>{plan.expected_improvement}</span>
          </div>
        )}
        {plan.stop_condition && (
          <div style={s.field}>
            <strong>Stop Condition: </strong>
            <span>{plan.stop_condition}</span>
          </div>
        )}
        {plan.preserved_stages?.length > 0 && (
          <div style={s.subCard}>
            <strong>Preserved Stages: </strong>
            {plan.preserved_stages.map(st => (
              <Badge key={st} label={STAGE_LABELS[st] || st} color="#4caf50" />
            ))}
          </div>
        )}
        {plan.stage_changes?.length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <strong>Stage Changes ({plan.stage_changes.length}):</strong>
            <table style={{ ...s.table, marginTop: '8px' }}>
              <colgroup>
                <col style={{ width: '140px' }} />
                <col style={{ width: '80px' }} />
                <col style={{ width: '200px' }} />
                <col style={{ width: '200px' }} />
              </colgroup>
              <thead>
                <tr>
                  <th style={s.th}>Stage</th>
                  <th style={s.th}>Action</th>
                  <th style={s.th}>Description</th>
                  <th style={s.th}>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {plan.stage_changes.map((sc, i) => (
                  <tr key={i}>
                    <td style={s.td}>
                      <Badge
                        label={STAGE_LABELS[sc.stage] || sc.stage}
                        color={STAGE_COLORS[sc.stage] || '#9e9e9e'}
                      />
                    </td>
                    <td style={s.td}>
                      <Badge
                        label={ACTION_LABELS[sc.action] || sc.action}
                        color={ACTION_COLORS[sc.action] || '#9e9e9e'}
                      />
                    </td>
                    <td style={s.td}>{sc.description}</td>
                    <td style={s.td}>{sc.rationale}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  };

  const renderRevisedPlan = (rwp: RevisedWorkflowPlan | null | undefined) => {
    if (!rwp) return <p>No revised workflow plan.</p>;
    const strategies = [
      { key: 'task_summary', label: 'Task Summary' },
      { key: 'data_strategy', label: 'Data Strategy' },
      { key: 'feature_strategy', label: 'Feature Strategy' },
      { key: 'model_strategy', label: 'Model Strategy' },
      { key: 'validation_strategy', label: 'Validation Strategy' },
      { key: 'evaluation_strategy', label: 'Evaluation Strategy' },
      { key: 'hpo_strategy', label: 'HPO Strategy' },
    ];
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Revised Workflow Plan</h4>
        <div style={s.grid}>
          <div style={s.field}><strong>Status: </strong><span>{rwp.status}</span></div>
          <div style={s.field}><strong>Planning Mode: </strong><span>{rwp.planning_mode}</span></div>
        </div>
        {rwp.llm_reasoning_summary && (
          <div style={s.subCard}>
            <strong>AI Reasoning:</strong>
            <p style={s.summaryText}>{rwp.llm_reasoning_summary}</p>
          </div>
        )}
        <div style={s.subCard}>
          <strong>Changed Sections: </strong>
          <span style={{ color: '#e65100' }}>{(rwp.changed_sections || []).join(', ') || 'None'}</span>
        </div>
        <div style={s.subCard}>
          <strong>Preserved Sections: </strong>
          <span style={{ color: '#2e7d32' }}>{(rwp.preserved_sections || []).join(', ') || 'None'}</span>
        </div>
        {rwp.planning_warnings?.length > 0 && (
          <div style={s.warningBox}>
            <strong>Planning Warnings:</strong>
            <ul style={s.list}>
              {rwp.planning_warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}
        <div style={s.grid}>
          {strategies.map(({ key, label }) => (
            <div key={key} style={s.field}>
              <strong>{label}: </strong>
              <span>{(rwp as any)[key] ? 'Present' : 'Not set'}</span>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderRerunPlan = (irp: IterationRerunPlan | null | undefined) => {
    if (!irp) return <p>No iteration rerun plan.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Iteration Rerun Plan</h4>
        <div style={s.grid}>
          <div style={s.field}><strong>Next Iteration: </strong><span>#{irp.next_iteration_index}</span></div>
          <div style={s.field}>
            <strong>Entry Point: </strong>
            {irp.rerun_from_stage ? (
              <Badge
                label={STAGE_LABELS[irp.rerun_from_stage] || irp.rerun_from_stage}
                color={STAGE_COLORS[irp.rerun_from_stage] || '#9e9e9e'}
              />
            ) : <span>N/A</span>}
          </div>
          <div style={s.field}>
            <strong>Stop If No Gain: </strong>
            <span style={{ color: irp.stop_after_next_iteration_if_no_gain ? '#c62828' : '#2e7d32', fontWeight: 600 }}>
              {irp.stop_after_next_iteration_if_no_gain ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Min Improvement Threshold: </strong>
            <span>{irp.minimum_improvement_threshold ?? 'N/A'}</span>
          </div>
        </div>
        <div style={s.subCard}>
          <strong>Rerun Stages:</strong>
          <div style={s.field}>
            {(irp.rerun_stages || []).map(s => (
              <Badge key={s} label={STAGE_LABELS[s] || s} color={STAGE_COLORS[s] || '#9e9e9e'} />
            ))}
          </div>
        </div>
        <div style={s.subCard}>
          <strong>Reuse Artifacts:</strong> {(irp.reuse_artifacts || []).join(', ') || 'None'}
        </div>
        <div style={s.subCard}>
          <strong>Invalidate Artifacts:</strong> {(irp.invalidate_artifacts || []).join(', ') || 'None'}
        </div>
        {irp.expected_improvement_targets?.length > 0 && (
          <div style={s.subCard}>
            <strong>Expected Improvements:</strong>
            <ul style={s.list}>
              {irp.expected_improvement_targets.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          </div>
        )}
        {irp.reasoning && (
          <div style={s.subCard}>
            <strong>Reasoning:</strong>
            <p style={s.summaryText}>{irp.reasoning}</p>
          </div>
        )}
      </div>
    );
  };

  const renderStopRationale = (sr: StopRationale | null | undefined) => {
    if (!sr) return <p>No stop rationale.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Stop Rationale</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Category: </strong>
            <span>{STOP_CATEGORY_LABELS[sr.category] || sr.category}</span>
          </div>
        </div>
        <div style={s.field}>
          <strong>Primary Reason: </strong>
          <p style={s.summaryText}>{sr.primary_reason}</p>
        </div>
        {sr.supporting_reasons?.length > 0 && (
          <div style={s.subCard}>
            <strong>Supporting Reasons:</strong>
            <ul style={s.list}>
              {sr.supporting_reasons.map((r, i) => <li key={i}>{r}</li>)}
            </ul>
          </div>
        )}
        {sr.best_result_summary && (
          <div style={s.subCard}>
            <strong>Best Result:</strong>
            <p style={s.summaryText}>{sr.best_result_summary}</p>
          </div>
        )}
      </div>
    );
  };

  const renderSystemChecks = (checks: SystemChecks | null | undefined) => {
    if (!checks) return null;
    const checkGroups = [
      {
        label: 'ML Checks',
        items: [
          { key: 'weak_baseline_improvement', label: 'Weak Baseline Improvement' },
          { key: 'high_fold_variance', label: 'High Fold Variance' },
          { key: 'all_models_weak', label: 'All Models Weak' },
          { key: 'hpo_budget_limited', label: 'HPO Budget Limited' },
          { key: 'candidate_underperforms_baseline', label: 'Underperforms Baseline' },
          { key: 'unstable_best_model', label: 'Unstable Best Model' },
        ],
      },
      {
        label: 'Data Checks',
        items: [
          { key: 'small_sample_warning', label: 'Small Sample' },
          { key: 'feature_count_low', label: 'Feature Count Low' },
          { key: 'many_features_dropped', label: 'Many Features Dropped' },
        ],
      },
      {
        label: 'Materials Checks',
        items: [
          { key: 'physics_constraint_violated', label: 'Physics Constraint Violated' },
          { key: 'feature_materials_relevance_low', label: 'Feature Relevance Low' },
          { key: 'chemical_space_coverage_low', label: 'Chemical Coverage Low' },
        ],
      },
      {
        label: 'Guard Checks',
        items: [
          { key: 'max_iterations_reached', label: 'Max Iterations Reached' },
          { key: 'no_improvement_trend', label: 'No Improvement Trend' },
          { key: 'repeated_root_cause', label: 'Repeated Root Cause' },
        ],
      },
    ];
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>System Checks</h4>
        {checkGroups.map(group => (
          <div key={group.label} style={s.subCard}>
            <strong>{group.label}</strong>
            <div style={s.grid}>
              {group.items.map(({ key, label }) => (
                <div key={key} style={s.field}>
                  <span>{label}: </span>
                  <span style={{
                    color: (checks as any)[key] ? '#c62828' : '#4caf50',
                    fontWeight: 600,
                  }}>
                    {(checks as any)[key] ? 'TRIGGERED' : 'OK'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ))}
        {checks.warnings?.length > 0 && (
          <div style={s.warningBox}>
            <strong>Warnings:</strong>
            <ul style={s.list}>
              {checks.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderTab = (tabId: string, label: string) => (
    <button
      key={tabId}
      onClick={() => setActiveTab(tabId)}
      style={{
        ...s.tabButton,
        backgroundColor: activeTab === tabId ? '#1976d2' : '#e0e0e0',
        color: activeTab === tabId ? '#fff' : '#333',
      }}
    >
      {label}
    </button>
  );

  const tabs = [
    { id: 'decision', label: 'Decision' },
    { id: 'reasoning', label: 'Reasoning' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'iteration_plan', label: 'Iteration Plan' },
    { id: 'revised_plan', label: 'Revised Plan' },
    { id: 'rerun_plan', label: 'Rerun Plan' },
    { id: 'stop', label: 'Stop Rationale' },
    { id: 'system', label: 'System Checks' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Iteration Decision</h3>
      <p style={s.description}>
        Unified AI-based decision maker. Reviews materials task completion, model training results,
        and all upstream context holistically to make a single decision: ITERATE (with detailed
        reasoning and optimization plan) or STOP (with rationale and final pipeline selection input).
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Deciding...' : 'Run Iteration Decision'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Decision'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Iteration Decision Result</h4>

          {/* Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>Decision ID:</strong> {result.iteration_decision_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}>
              <strong>Decision: </strong>
              <Badge
                label={DECISION_LABELS[result.decision || ''] || result.decision || 'N/A'}
                color={DECISION_COLORS[result.decision || ''] || '#9e9e9e'}
              />
            </div>
            <div style={s.field}><strong>Iteration:</strong> #{result.iteration_index}</div>
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningBox}>
              <strong>Warnings:</strong>
              <ul style={s.list}>
                {result.warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          {result.error_message && (
            <div style={s.errorBox}>
              <strong>Error:</strong> {result.error_message}
            </div>
          )}

          {/* Adopt & Rerun section for ITERATE path */}
          {result.decision === 'iterate' && result.ready_for_iteration && (
            <div style={s.adoptSection}>
              <h4 style={s.cardTitle}>Iterate: Adopt Revised Plan & Rerun Pipeline</h4>
              <p style={s.description}>
                The system recommends iteration. Adopting the revised plan creates a new WorkflowPlan
                and re-executes the pipeline stages listed below.
              </p>

              {result.iteration_rerun_plan && (
                <div style={s.subCard}>
                  <div style={s.grid}>
                    <div style={s.field}>
                      <strong>Entry Point: </strong>
                      <Badge
                        label={STAGE_LABELS[result.iteration_rerun_plan.rerun_from_stage || ''] || result.iteration_rerun_plan.rerun_from_stage || 'N/A'}
                        color={STAGE_COLORS[result.iteration_rerun_plan.rerun_from_stage || ''] || '#9e9e9e'}
                      />
                    </div>
                    <div style={s.field}>
                      <strong>Stop if no gain: </strong>
                      <span style={{ color: result.iteration_rerun_plan.stop_after_next_iteration_if_no_gain ? '#c62828' : '#2e7d32', fontWeight: 600 }}>
                        {result.iteration_rerun_plan.stop_after_next_iteration_if_no_gain ? 'Yes' : 'No'}
                      </span>
                    </div>
                  </div>
                  <div style={s.field}>
                    <strong>Rerun Stages: </strong>
                    {(result.iteration_rerun_plan.rerun_stages || []).map(s => (
                      <Badge key={s} label={STAGE_LABELS[s] || s} color={STAGE_COLORS[s] || '#9e9e9e'} />
                    ))}
                  </div>
                </div>
              )}

              {!showAdoptConfirm ? (
                <button onClick={() => setShowAdoptConfirm(true)} disabled={adopting} style={s.adoptButton}>
                  {adopting ? 'Adopting...' : 'Adopt & Rerun'}
                </button>
              ) : (
                <div style={s.confirmBox}>
                  <p style={{ margin: '0 0 12px 0', fontWeight: 600, color: '#c62828' }}>
                    This will create a new WorkflowPlan and re-execute pipeline stages. Continue?
                  </p>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={handleAdoptAndRerun} disabled={adopting} style={s.adoptConfirmButton}>
                      {adopting ? 'Running...' : 'Yes, Adopt & Rerun'}
                    </button>
                    <button onClick={() => setShowAdoptConfirm(false)} disabled={adopting} style={s.cancelButton}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}

              {adoptResult && (
                <div style={{ ...s.subCard, marginTop: '12px', borderLeft: '4px solid #2e7d32' }}>
                  <strong>Plan Adopted: </strong>
                  <code>{adoptResult.adopted_workflow_plan_id}</code>
                </div>
              )}

              {rerunProgress.length > 0 && (
                <div style={{ ...s.subCard, marginTop: '12px' }}>
                  <strong>Rerun Progress:</strong>
                  <ul style={{ ...s.list, marginTop: '8px' }}>
                    {rerunProgress.map((msg, i) => (
                      <li key={i} style={{
                        color: msg.includes('FAILED') ? '#c62828' : msg.includes('completed') ? '#2e7d32' : '#333',
                        fontSize: '13px', marginBottom: '2px',
                      }}>
                        {msg}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {rerunError && (
                <div style={s.errorBox}>
                  <strong>Rerun Error:</strong> {rerunError}
                </div>
              )}

              {!adopting && rerunProgress.some(m => m.includes('All stages completed')) && !rerunError && (
                <div style={s.guidanceBox}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '15px' }}>Next Steps</h4>
                  <p style={{ margin: '4px 0', fontSize: '14px', lineHeight: 1.8 }}>
                    Pipeline re-execution complete. Run <strong>Iteration Decision</strong> again to
                    evaluate the new results and decide whether to iterate further or stop.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Tab navigation */}
          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          {/* Tab content */}
          <div style={s.tabContent}>
            {activeTab === 'decision' && renderDecision()}
            {activeTab === 'reasoning' && renderReasoning(result.reasoning)}
            {activeTab === 'evidence' && renderEvidence(result.evidence_bundle)}
            {activeTab === 'iteration_plan' && renderIterationPlan(result.iteration_plan)}
            {activeTab === 'revised_plan' && renderRevisedPlan(result.revised_workflow_plan)}
            {activeTab === 'rerun_plan' && renderRerunPlan(result.iteration_rerun_plan)}
            {activeTab === 'stop' && renderStopRationale(result.stop_rationale)}
            {activeTab === 'system' && renderSystemChecks(result.system_checks)}
            {activeTab === 'json' && (
              <div style={s.card}>
                <h4 style={s.cardTitle}>Full JSON</h4>
                <pre style={s.json}>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '24px',
    padding: '16px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
  },
  title: { margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600 },
  description: { margin: '0 0 16px 0', color: '#666', fontSize: '13px', lineHeight: 1.5 },
  buttonRow: { display: 'flex', gap: '8px', marginBottom: '16px' },
  runButton: {
    padding: '10px 20px', backgroundColor: '#7b1fa2', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px', backgroundColor: '#f57c00', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  errorBox: {
    padding: '12px', backgroundColor: '#ffebee', border: '1px solid #f44336',
    borderRadius: '4px', color: '#c62828', marginBottom: '16px',
  },
  resultBox: {
    padding: '16px', backgroundColor: '#fff', border: '1px solid #e0e0e0',
    borderRadius: '8px',
  },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  fieldRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  badge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '12px',
    color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px',
  },
  warningBox: {
    padding: '12px', backgroundColor: '#fff3e0', border: '1px solid #ff9800',
    borderRadius: '4px', color: '#e65100', marginBottom: '16px',
  },
  list: { margin: '4px 0', paddingLeft: '20px' },
  tabBar: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' },
  tabButton: {
    padding: '6px 14px', border: 'none', borderRadius: '16px',
    fontSize: '13px', fontWeight: 600, cursor: 'pointer',
  },
  tabContent: { minHeight: '200px', maxHeight: '60vh', overflowY: 'auto' as const },
  card: {
    padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px',
    marginBottom: '12px', border: '1px solid #e0e0e0',
    overflowX: 'auto' as const,
  },
  subCard: {
    padding: '10px', backgroundColor: '#fff', borderRadius: '4px',
    marginBottom: '8px', border: '1px solid #eee',
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  summaryText: { marginTop: '8px', color: '#333', fontSize: '14px', lineHeight: 1.5 },
  table: {
    width: '100%', borderCollapse: 'collapse' as const, fontSize: '13px',
    tableLayout: 'fixed' as const, minWidth: '700px',
  },
  th: {
    textAlign: 'left' as const, padding: '6px 8px', borderBottom: '2px solid #e0e0e0',
    fontWeight: 600, backgroundColor: '#fafafa', whiteSpace: 'nowrap' as const,
  },
  td: {
    padding: '6px 8px', borderBottom: '1px solid #eee',
    verticalAlign: 'top' as const, wordBreak: 'break-word' as const,
  },
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', fontSize: '11px',
    overflow: 'auto', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
  },
  adoptSection: {
    padding: '16px', backgroundColor: '#fff8e1', border: '2px solid #ff8f00',
    borderRadius: '8px', marginBottom: '16px',
  },
  adoptButton: {
    padding: '12px 24px', backgroundColor: '#e65100', color: '#fff',
    border: 'none', borderRadius: '6px', fontSize: '15px', fontWeight: 700,
    cursor: 'pointer', marginTop: '12px',
  },
  adoptConfirmButton: {
    padding: '10px 20px', backgroundColor: '#c62828', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  cancelButton: {
    padding: '10px 20px', backgroundColor: '#9e9e9e', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  confirmBox: {
    padding: '12px', backgroundColor: '#ffebee', borderRadius: '6px',
    marginTop: '12px', border: '1px solid #ef9a9a',
  },
  guidanceBox: {
    padding: '16px', backgroundColor: '#e8f5e9', border: '2px solid #4caf50',
    borderRadius: '8px', marginTop: '12px',
  },
};

export default IterationDecisionPanel;
