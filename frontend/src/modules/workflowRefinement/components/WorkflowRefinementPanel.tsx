import React, { useState } from 'react';
import {
  createWorkflowRefinement,
  rerunWorkflowRefinement,
  adoptRevisedPlan,
} from '../../../api/workflowRefinementApi';
import { createFeatureEngineering } from '../../../api/featureEngineeringApi';
import { createFeaturePreprocessing } from '../../../api/featurePreprocessingApi';
import { createModelSearchContext } from '../../../api/modelSearchContextApi';
import { createModelSearchPlan } from '../../../api/modelSearchApi';
import { createPipelineGeneration } from '../../../api/pipelineGenerationApi';
import { createPipelineExecution } from '../../../api/pipelineExecutionApi';
import { createMetricEvaluation } from '../../../api/metricEvaluationApi';
import {
  WorkflowRefinementResponse,
  DecisionReasoning,
  EvidenceUsed,
  RevisedWorkflowPlanResponse,
  WorkflowPlanDelta,
  IterationRerunPlan,
  FinalPipelineSelectionInput,
  WorkflowRefinementValidationResult,
  AdoptRevisedPlanResult,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  DECISION_COLORS,
  DECISION_LABELS,
  CONFIDENCE_COLORS,
  RERUN_STAGE_COLORS,
  RERUN_STAGE_LABELS,
} from '../constants';

interface WorkflowRefinementPanelProps {
  taskId: string;
  initialResult?: WorkflowRefinementResponse;
}

const WorkflowRefinementPanel: React.FC<WorkflowRefinementPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowRefinementResponse | null>(initialResult ?? null);
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
      const response = await createWorkflowRefinement(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run workflow refinement.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunWorkflowRefinement(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run workflow refinement.');
    } finally {
      setLoading(false);
    }
  };

  const handleAdoptAndRerun = async () => {
    if (!result?.workflow_refinement_id) return;
    setAdopting(true);
    setRerunError(null);
    setRerunProgress([]);
    setAdoptResult(null);
    setShowAdoptConfirm(false);

    try {
      // Step 1: Adopt the revised plan
      setRerunProgress(['Adopting revised plan...']);
      const adoptResp = await adoptRevisedPlan(result.workflow_refinement_id);
      if (!adoptResp.success || !adoptResp.data.adopted) {
        setRerunError(adoptResp.message || 'Failed to adopt revised plan.');
        setAdopting(false);
        return;
      }
      setAdoptResult(adoptResp.data);
      setRerunProgress(prev => [...prev, 'Plan adopted as ' + adoptResp.data.adopted_workflow_plan_id]);

      // Step 2: Run pipeline stages in sequence
      const stages = adoptResp.data.rerun_stages || [];
      const STAGE_API: Record<string, (taskId: string) => Promise<any>> = {
        workflow_planning: async () => null, // already adopted
        feature_engineering: createFeatureEngineering,
        feature_preprocessing: createFeaturePreprocessing,
        model_search_context: createModelSearchContext,
        model_search: createModelSearchPlan,
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
        setRerunProgress(prev => [...prev, 'All stages completed. Ready for next refinement.']);
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

  const renderDecision = () => {
    if (!result) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Refinement Decision</h4>
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
              label={result.decision_confidence_level || 'N/A'}
              color={CONFIDENCE_COLORS[result.decision_confidence_level || ''] || '#9e9e9e'}
            />
          </div>
          <div style={s.field}>
            <strong>Recommended Rerun From: </strong>
            {result.recommended_rerun_from_stage ? (
              <Badge
                label={RERUN_STAGE_LABELS[result.recommended_rerun_from_stage] || result.recommended_rerun_from_stage}
                color={RERUN_STAGE_COLORS[result.recommended_rerun_from_stage] || '#9e9e9e'}
              />
            ) : (
              <span>N/A</span>
            )}
          </div>
          <div style={s.field}>
            <strong>Ready for Iteration: </strong>
            <span style={{ color: result.ready_for_iteration ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {result.ready_for_iteration ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Ready for Final Selection: </strong>
            <span style={{ color: result.ready_for_final_pipeline_selection ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {result.ready_for_final_pipeline_selection ? 'Yes' : 'No'}
            </span>
          </div>
          {result.llm_workflow_refinement?.workflow_refinement_decision?.primary_reason && (
            <div style={{ ...s.field, gridColumn: '1 / -1' }}>
              <strong>Primary Reason: </strong>
              <span>{result.llm_workflow_refinement.workflow_refinement_decision.primary_reason}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderDecisionReasoning = (reasoning: DecisionReasoning | null | undefined) => {
    if (!reasoning) return <p>No decision reasoning available.</p>;
    const items = [
      { key: 'performance_assessment', label: 'Performance Assessment' },
      { key: 'baseline_assessment', label: 'Baseline Assessment' },
      { key: 'stability_assessment', label: 'Stability Assessment' },
      { key: 'diagnosis_assessment', label: 'Diagnosis Assessment' },
      { key: 'cost_assessment', label: 'Cost Assessment' },
      { key: 'risk_assessment', label: 'Risk Assessment' },
      { key: 'final_reasoning_summary', label: 'Final Reasoning Summary' },
    ];
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Decision Reasoning</h4>
        {items.map(({ key, label }) => (
          <div key={key} style={s.subCard}>
            <strong>{label}</strong>
            <p style={s.summaryText}>{(reasoning as any)[key] || 'N/A'}</p>
          </div>
        ))}
      </div>
    );
  };

  const renderEvidence = (evidence: EvidenceUsed[]) => {
    if (!evidence || evidence.length === 0) return <p>No evidence recorded.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Evidence Used ({evidence.length})</h4>
        <table style={s.table}>
          <colgroup>
            <col style={{ width: '140px' }} />
            <col style={{ width: '120px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '120px' }} />
            <col style={{ width: '200px' }} />
            <col style={{ width: '140px' }} />
          </colgroup>
          <thead>
            <tr>
              <th style={s.th}>Source Module</th>
              <th style={s.th}>Evidence Type</th>
              <th style={s.th}>Source Field</th>
              <th style={s.th}>Value</th>
              <th style={s.th}>Interpretation</th>
              <th style={s.th}>Supports</th>
            </tr>
          </thead>
          <tbody>
            {evidence.map((e, i) => (
              <tr key={e.evidence_id || i}>
                <td style={s.td}>{e.source_module}</td>
                <td style={s.td}>
                  <Badge label={e.evidence_type} />
                </td>
                <td style={s.td}>{e.source_field}</td>
                <td style={s.td}>{typeof e.value === 'object' ? JSON.stringify(e.value) : String(e.value ?? '-')}</td>
                <td style={s.td}>{e.interpretation}</td>
                <td style={s.td}>
                  <Badge
                    label={e.supports_decision === 'proceed_next_stage' ? 'Proceed' : 'Iterate'}
                    color={DECISION_COLORS[e.supports_decision] || '#9e9e9e'}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderRevisedWorkflowPlan = (rwp: RevisedWorkflowPlanResponse | null | undefined) => {
    if (!rwp) return <p>No revised workflow plan (decision was proceed_next_stage or plan not generated).</p>;
    const strategies = [
      { key: 'task_summary', label: 'Task Summary' },
      { key: 'data_strategy', label: 'Data Strategy' },
      { key: 'feature_strategy', label: 'Feature Strategy' },
      { key: 'model_strategy', label: 'Model Strategy' },
      { key: 'validation_strategy', label: 'Validation Strategy' },
      { key: 'evaluation_strategy', label: 'Evaluation Strategy' },
      { key: 'hpo_strategy', label: 'HPO Strategy' },
      { key: 'interpretability_strategy', label: 'Interpretability Strategy' },
      { key: 'pipeline_generation_input', label: 'Pipeline Generation Input' },
    ];
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Revised WorkflowPlanResponse</h4>
        <div style={s.grid}>
          <div style={s.field}><strong>Status: </strong><span>{rwp.status}</span></div>
          <div style={s.field}><strong>Planning Mode: </strong><span>{rwp.planning_mode}</span></div>
          <div style={s.field}><strong>Confidence Score: </strong><span>{rwp.confidence_score}</span></div>
        </div>
        {rwp.llm_reasoning_summary && (
          <div style={s.subCard}>
            <strong>LLM Reasoning:</strong>
            <p style={s.summaryText}>{rwp.llm_reasoning_summary}</p>
          </div>
        )}
        {rwp.refinement_metadata && (
          <div style={s.subCard}>
            <strong>Refinement Metadata:</strong>
            <div>Changed: {(rwp.refinement_metadata.changed_sections || []).join(', ') || 'None'}</div>
            <div>Preserved: {(rwp.refinement_metadata.preserved_sections || []).join(', ') || 'None'}</div>
          </div>
        )}
        {rwp.planning_warnings && rwp.planning_warnings.length > 0 && (
          <div style={s.warningBox}>
            <strong>Planning Warnings:</strong>
            <ul style={s.list}>
              {rwp.planning_warnings.map((w: string, i: number) => <li key={i}>{w}</li>)}
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

  const renderWorkflowPlanDelta = (delta: WorkflowPlanDelta | null | undefined) => {
    if (!delta) return <p>No workflow plan delta available.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Workflow Plan Delta</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Changed Sections: </strong>
            <span style={{ color: '#e65100' }}>{(delta.changed_sections || []).join(', ') || 'None'}</span>
          </div>
          <div style={s.field}>
            <strong>Preserved Sections: </strong>
            <span style={{ color: '#2e7d32' }}>{(delta.preserved_sections || []).join(', ') || 'None'}</span>
          </div>
        </div>
        {delta.feature_strategy_delta && (
          <div style={s.subCard}>
            <strong>Feature Strategy Delta:</strong>
            <pre style={s.json}>{JSON.stringify(delta.feature_strategy_delta, null, 2)}</pre>
          </div>
        )}
        {delta.model_strategy_delta && (
          <div style={s.subCard}>
            <strong>Model Strategy Delta:</strong>
            <pre style={s.json}>{JSON.stringify(delta.model_strategy_delta, null, 2)}</pre>
          </div>
        )}
        {delta.hpo_strategy_delta && (
          <div style={s.subCard}>
            <strong>HPO Strategy Delta:</strong>
            <pre style={s.json}>{JSON.stringify(delta.hpo_strategy_delta, null, 2)}</pre>
          </div>
        )}
        {delta.rejected_or_unsafe_changes && delta.rejected_or_unsafe_changes.length > 0 && (
          <div style={s.errorBox}>
            <strong>Rejected/Unsafe Changes:</strong>
            <ul style={s.list}>
              {delta.rejected_or_unsafe_changes.map((c: string, i: number) => <li key={i}>{c}</li>)}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderIterationRerunPlan = (irp: IterationRerunPlan | null | undefined) => {
    if (!irp) return <p>No iteration rerun plan (decision was proceed_next_stage).</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Iteration Rerun Plan</h4>
        <div style={s.grid}>
          <div style={s.field}><strong>Next Iteration: </strong><span>#{irp.next_iteration_index}</span></div>
          <div style={s.field}>
            <strong>Entry Point: </strong>
            {irp.recommended_rerun_from_stage ? (
              <Badge
                label={RERUN_STAGE_LABELS[irp.recommended_rerun_from_stage] || irp.recommended_rerun_from_stage}
                color={RERUN_STAGE_COLORS[irp.recommended_rerun_from_stage] || '#9e9e9e'}
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
            {(irp.rerun_stages || []).map((s: string) => (
              <Badge key={s} label={RERUN_STAGE_LABELS[s] || s} color={RERUN_STAGE_COLORS[s] || '#9e9e9e'} />
            ))}
          </div>
        </div>
        <div style={s.subCard}>
          <strong>Reuse Artifacts:</strong> {(irp.reuse_artifacts || []).join(', ') || 'None'}
        </div>
        <div style={s.subCard}>
          <strong>Invalidate Artifacts:</strong> {(irp.invalidate_artifacts || []).join(', ') || 'None'}
        </div>
        {irp.expected_improvement_targets && irp.expected_improvement_targets.length > 0 && (
          <div style={s.subCard}>
            <strong>Expected Improvements:</strong>
            <ul style={s.list}>
              {irp.expected_improvement_targets.map((t: string, i: number) => <li key={i}>{t}</li>)}
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

  const renderFinalPipelineSelectionInput = (fpsi: FinalPipelineSelectionInput | null | undefined) => {
    if (!fpsi) return <p>No final pipeline selection input (decision was iterate_refinement).</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Final Pipeline Selection Input</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Ready for Selection: </strong>
            <span style={{ color: fpsi.ready_for_final_pipeline_selection ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {fpsi.ready_for_final_pipeline_selection ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}><strong>Best Model: </strong><span>{fpsi.current_best_model_id || 'N/A'}</span></div>
          <div style={s.field}><strong>Best Trial: </strong><span>{fpsi.current_best_trial_id || 'N/A'}</span></div>
          <div style={s.field}><strong>Best Pipeline: </strong><span>{fpsi.current_best_pipeline_spec_id || 'N/A'}</span></div>
        </div>
        {fpsi.candidate_metric_evaluation_ids && fpsi.candidate_metric_evaluation_ids.length > 0 && (
          <div style={s.subCard}>
            <strong>Candidate Evaluations: </strong>
            {fpsi.candidate_metric_evaluation_ids.join(', ')}
          </div>
        )}
      </div>
    );
  };

  const renderValidation = (vr: WorkflowRefinementValidationResult | null | undefined) => {
    if (!vr) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Validation Result</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Valid: </strong>
            <span style={{ color: vr.is_valid ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {vr.is_valid ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Safety Scan: </strong>
            <span style={{ color: vr.safety_scan_passed ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {vr.safety_scan_passed ? 'Passed' : 'Failed'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Decision Valid: </strong>
            <span>{vr.decision_valid ? 'Yes' : 'No'}</span>
          </div>
          {vr.revised_plan_valid !== null && vr.revised_plan_valid !== undefined && (
            <div style={s.field}>
              <strong>Revised Plan Valid: </strong>
              <span style={{ color: vr.revised_plan_valid ? '#2e7d32' : '#c62828' }}>
                {vr.revised_plan_valid ? 'Yes' : 'No'}
              </span>
            </div>
          )}
        </div>
        {vr.issues && vr.issues.length > 0 && (
          <div style={s.errorBox}>
            <strong>Issues:</strong>
            <ul style={s.list}>
              {vr.issues.map((iss: string, i: number) => <li key={i}>{iss}</li>)}
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
    { id: 'revised_plan', label: 'Revised Plan' },
    { id: 'delta', label: 'Plan Delta' },
    { id: 'rerun_plan', label: 'Rerun Plan' },
    { id: 'final_selection', label: 'Final Selection' },
    { id: 'validation', label: 'Validation' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>LLM-driven Workflow Refinement</h3>
      <p style={s.description}>
        LLM-based closed-loop decision maker. Reads result diagnosis, metrics, and experiment history
        to decide whether to proceed to Final Pipeline Selection or generate a revised WorkflowPlanResponse
        for another iteration. Outputs detailed reasoning, evidence, and rerun plans.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Deciding...' : 'Run Workflow Refinement'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Refinement'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Workflow Refinement Result</h4>

          {/* Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>Refinement ID:</strong> {result.workflow_refinement_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}><strong>Iteration:</strong> #{result.iteration_index}</div>
            <div style={s.field}>
              <strong>Decision: </strong>
              <Badge
                label={DECISION_LABELS[result.decision || ''] || result.decision || 'N/A'}
                color={DECISION_COLORS[result.decision || ''] || '#9e9e9e'}
              />
            </div>
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

          {/* Adopt & Rerun section — shown when decision is iterate_refinement */}
          {result.decision === 'iterate_refinement' && result.ready_for_iteration && (
            <div style={s.adoptSection}>
              <h4 style={s.cardTitle}>Iterate: Adopt Revised Plan & Rerun Pipeline</h4>
              <p style={s.description}>
                The LLM recommends iteration. Adopting the revised plan creates a new WorkflowPlan
                and re-executes the pipeline stages listed below. Existing results are preserved.
              </p>

              {result.iteration_rerun_plan && (
                <div style={s.subCard}>
                  <div style={s.grid}>
                    <div style={s.field}>
                      <strong>Entry Point: </strong>
                      <Badge
                        label={RERUN_STAGE_LABELS[result.iteration_rerun_plan.recommended_rerun_from_stage || ''] || result.iteration_rerun_plan.recommended_rerun_from_stage || 'N/A'}
                        color={RERUN_STAGE_COLORS[result.iteration_rerun_plan.recommended_rerun_from_stage || ''] || '#9e9e9e'}
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
                    {(result.iteration_rerun_plan.rerun_stages || []).map((s: string) => (
                      <Badge key={s} label={RERUN_STAGE_LABELS[s] || s} color={RERUN_STAGE_COLORS[s] || '#9e9e9e'} />
                    ))}
                  </div>
                  {result.iteration_rerun_plan.reasoning && (
                    <div style={{ marginTop: '8px' }}>
                      <strong>Reasoning: </strong>
                      <span>{result.iteration_rerun_plan.reasoning}</span>
                    </div>
                  )}
                </div>
              )}

              {!showAdoptConfirm ? (
                <button
                  onClick={() => setShowAdoptConfirm(true)}
                  disabled={adopting}
                  style={s.adoptButton}
                >
                  {adopting ? 'Adopting...' : 'Adopt & Rerun'}
                </button>
              ) : (
                <div style={s.confirmBox}>
                  <p style={{ margin: '0 0 12px 0', fontWeight: 600, color: '#c62828' }}>
                    This will create a new WorkflowPlan and re-execute the pipeline stages above. Continue?
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
                    {rerunProgress.map((msg: string, i: number) => (
                      <li key={i} style={{
                        color: msg.includes('FAILED') ? '#c62828' : msg.includes('completed') ? '#2e7d32' : '#333',
                        fontSize: '13px',
                        marginBottom: '2px',
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
                  <p style={{ margin: '8px 0 0 0', fontSize: '13px' }}>
                    Some stages may have completed before the error. Check individual module results.
                  </p>
                </div>
              )}

              {!adopting && rerunProgress.some(m => m.includes('All stages completed')) && !rerunError && (
                <div style={s.guidanceBox}>
                  <h4 style={{ margin: '0 0 8px 0', fontSize: '15px' }}>Next Steps</h4>
                  <ol style={{ margin: '0', paddingLeft: '20px', fontSize: '14px', lineHeight: 1.8 }}>
                    <li>
                      <strong>Re-run Result Diagnosis</strong> — scroll up to <em>LLM-based Result Diagnosis</em> and
                      click <strong style={{ color: '#f57c00' }}>Re-run Diagnosis</strong> (the orange button).
                      This ensures a fresh analysis against the newly created metric results.
                    </li>
                    <li>
                      <strong>Run Workflow Refinement again</strong> — click <strong>Run Workflow Refinement</strong> above.
                      The LLM will compare results across iterations and decide whether to proceed to Final Selection
                      or iterate further.
                    </li>
                  </ol>
                  <p style={{ margin: '10px 0 0 0', fontSize: '13px', color: '#666' }}>
                    The closed-loop cycle: <strong>Re-run Diagnosis → Workflow Refinement → Adopt &amp; Rerun → repeat</strong> until
                    the LLM returns <em>Proceed to Final Selection</em>.
                  </p>
                  <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#c62828' }}>
                    Important: Use <strong>Re-run Diagnosis</strong> (not Run Diagnosis) after each Adopt &amp; Rerun.
                    The Run button may return cached results from a previous iteration.
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
            {activeTab === 'reasoning' && renderDecisionReasoning(result.decision_reasoning)}
            {activeTab === 'evidence' && renderEvidence(result.evidence_used)}
            {activeTab === 'revised_plan' && renderRevisedWorkflowPlan(result.revised_workflow_plan)}
            {activeTab === 'delta' && renderWorkflowPlanDelta(result.workflow_plan_delta)}
            {activeTab === 'rerun_plan' && renderIterationRerunPlan(result.iteration_rerun_plan)}
            {activeTab === 'final_selection' && renderFinalPipelineSelectionInput(result.final_pipeline_selection_input)}
            {activeTab === 'validation' && renderValidation(result.workflow_refinement_validation_result)}
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
  tabContent: { minHeight: '200px' },
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
    tableLayout: 'fixed' as const, minWidth: '900px',
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
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
    maxHeight: '500px',
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

export default WorkflowRefinementPanel;
