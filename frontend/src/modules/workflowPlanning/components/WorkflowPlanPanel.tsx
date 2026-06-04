import React, { useState } from 'react';
import { createWorkflowPlan, rerunWorkflowPlan } from '../../../api/workflowPlanningApi';
import { WorkflowPlanResponse, FeatureStrategy, DecisionRationale, SelectedFeatureAction, RejectedFeatureAction, SelectedModelAction, RejectedModelAction, ModelDecisionRationale } from '../types';

interface WorkflowPlanPanelProps {
  taskId: string;
  initialResult?: WorkflowPlanResponse;
}

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return '#4caf50';
      case 'planned_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const Badge: React.FC<{ label: string; color?: string; style?: React.CSSProperties }> = ({ label, color = '#1976d2', style }) => (
    <span style={{ ...s.badge, backgroundColor: color, ...style }}>{label}</span>
  );

  const renderRationale = (r: DecisionRationale | null | undefined) => {
    if (!r) return <span style={{ color: '#999', fontSize: '11px' }}>No rationale</span>;
    return (
      <div style={{ fontSize: '11px', color: '#777', display: 'flex', flexDirection: 'column', gap: '1px' }}>
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
    if (!r) return <span style={{ color: '#999', fontSize: '11px' }}>No rationale</span>;
    return (
      <div style={{ fontSize: '11px', color: '#777', display: 'flex', flexDirection: 'column', gap: '1px' }}>
        {r.reason && <div><strong>Reason:</strong> {r.reason}</div>}
        {r.expected_performance && <div><strong>Expected Perf:</strong> {r.expected_performance}</div>}
        {r.risk && <div><strong>Risk:</strong> {r.risk}</div>}
        {r.fallback && <div><strong>Fallback:</strong> {r.fallback}</div>}
      </div>
    );
  };

  const renderSummary = () => (
    <div>
      {result?.task_summary && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Task Summary</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Type:</strong> {result.task_summary.task_type}</div>
            <div style={s.field}><strong>Input Modality:</strong> {result.task_summary.input_modality}</div>
            <div style={s.field}><strong>Prediction Target:</strong> {result.task_summary.prediction_target}</div>
            <div style={s.field}><strong>Material Domain:</strong> {result.task_summary.material_domain}</div>
            <div style={s.field}><strong>Primary Goal:</strong> {result.task_summary.primary_goal}</div>
          </div>
        </div>
      )}
      {result?.data_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Data Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Target Column:</strong> {result.data_strategy.target_column}</div>
            <div style={s.field}><strong>Input Columns:</strong> {result.data_strategy.input_columns?.join(', ')}</div>
            <div style={s.field}><strong>Duplicate Handling:</strong> {result.data_strategy.duplicate_handling}</div>
            <div style={s.field}><strong>Missing Value Strategy:</strong> {result.data_strategy.missing_value_strategy}</div>
          </div>
          {result.data_strategy.target_handling && (
            <div style={s.field}>
              <strong>Target Handling:</strong>{' '}
              {result.data_strategy.target_handling.requires_transformation_check
                ? `Transform (${result.data_strategy.target_handling.recommended_transformation})`
                : 'No transformation needed'}
            </div>
          )}
        </div>
      )}
      {result?.preprocessing_intent && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Preprocessing Intent</h4>
          {result.preprocessing_intent.high_level_goals?.length > 0 && (
            <div style={s.field}><strong>High-Level Goals:</strong>
              <ul style={s.list}>{result.preprocessing_intent.high_level_goals.map((g, i) => <li key={i}>{g}</li>)}</ul>
            </div>
          )}
          {result.preprocessing_intent.risks_to_check_after_feature_engineering?.length > 0 && (
            <div style={s.field}><strong>Risks to Check:</strong>
              <ul style={s.list}>{result.preprocessing_intent.risks_to_check_after_feature_engineering.map((r, i) => <li key={i}>{r}</li>)}</ul>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderFeatureStrategy = () => (
    <div>
      {result?.feature_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Feature Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Feature Type:</strong> {result.feature_strategy.feature_type}</div>
            <div style={s.field}><strong>Structure Features:</strong> {result.feature_strategy.requires_structure_features ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Feature Selection:</strong> {result.feature_strategy.feature_selection_required ? 'Yes' : 'No'}</div>
            <div style={s.field}><strong>Feature Scaling:</strong> {result.feature_strategy.feature_scaling_required ? 'Yes' : 'No'}</div>
          </div>

          {(result.feature_strategy.selected_feature_actions?.length ?? 0) > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#2e7d32' }}>Selected Feature Actions:</strong>
              <table style={{ ...s.innerTable, marginTop: '8px' }}>
                <thead>
                  <tr><th style={{...s.th, width: '10%'}}>Action</th><th style={{...s.th, width: '14%'}}>Capability</th><th style={{...s.th, width: '7%'}}>Priority</th><th style={{...s.th, width: '14%'}}>Output Group</th><th style={{...s.th, width: '55%'}}>Rationale</th></tr>
                </thead>
                <tbody>
                  {result.feature_strategy.selected_feature_actions?.map((a: SelectedFeatureAction, i: number) => (
                    <tr key={i}>
                      <td style={s.td}>{a.action_id}</td>
                      <td style={{...s.td, overflow: 'hidden'}}><Badge label={a.capability_id} color="#2e7d32" style={{ maxWidth: '100%', overflowWrap: 'break-word', whiteSpace: 'normal' }} /></td>
                      <td style={s.td}>{a.priority}</td>
                      <td style={s.td}>{a.output_feature_group}</td>
                      <td style={s.td}>{renderRationale(a.decision_rationale)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(result.feature_strategy.rejected_feature_actions?.length ?? 0) > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#c62828' }}>Rejected Feature Actions:</strong>
              {result.feature_strategy.rejected_feature_actions?.map((a: RejectedFeatureAction, i: number) => (
                <div key={i} style={{ fontSize: '12px', marginLeft: '8px' }}>{a.capability_id}: {a.reason}</div>
              ))}
            </div>
          )}

          {(result.feature_strategy.executable_featurizers?.length ?? 0) > 0 && (
            <div style={s.field}><strong>Executable Featurizers:</strong>{' '}
              {result.feature_strategy.executable_featurizers?.map((f, i) => <Badge key={i} label={f} color="#2e7d32" />)}</div>
          )}
        </div>
      )}
    </div>
  );

  const renderModelStrategy = () => (
    <div>
      {result?.model_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Model Strategy</h4>
          <div style={s.field}><strong>Preferred Bias:</strong> {result.model_strategy.preferred_model_bias}</div>

          {result.model_strategy.model_selection_rationale_summary && (
            <div style={s.subCard}><strong>Selection Rationale:</strong>
              <p style={s.summaryText}>{result.model_strategy.model_selection_rationale_summary}</p>
            </div>
          )}

          {(result.model_strategy.selected_model_actions?.length ?? 0) > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#2e7d32' }}>Selected Models:</strong>
              <table style={{ ...s.innerTable, marginTop: '8px' }}>
                <thead>
                  <tr><th style={{...s.th, width: '10%'}}>Action</th><th style={{...s.th, width: '14%'}}>Family</th><th style={{...s.th, width: '7%'}}>Priority</th><th style={{...s.th, width: '14%'}}>Expected Perf</th><th style={{...s.th, width: '55%'}}>Rationale</th></tr>
                </thead>
                <tbody>
                  {result.model_strategy.selected_model_actions?.map((a: SelectedModelAction, i: number) => (
                    <tr key={i}>
                      <td style={s.td}>{a.action_id}</td>
                      <td style={{...s.td, overflow: 'hidden'}}><Badge label={a.model_family} color="#1565c0" style={{ maxWidth: '100%', overflowWrap: 'break-word', whiteSpace: 'normal' }} /></td>
                      <td style={s.td}>{a.priority}</td>
                      <td style={s.td}>{a.decision_rationale?.expected_performance || '-'}</td>
                      <td style={s.td}>{renderModelRationale(a.decision_rationale)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {(result.model_strategy.rejected_model_actions?.length ?? 0) > 0 && (
            <div style={s.subCard}>
              <strong style={{ color: '#c62828' }}>Rejected Models:</strong>
              {result.model_strategy.rejected_model_actions?.map((a: RejectedModelAction, i: number) => (
                <div key={i} style={{ fontSize: '12px', marginLeft: '8px' }}><Badge label={a.model_family} color="#c62828" /> {a.reason}</div>
              ))}
            </div>
          )}

          {(!result.model_strategy.selected_model_actions || result.model_strategy.selected_model_actions.length === 0) && (
            <div style={s.grid}>
              <div style={s.field}><strong>Candidate Models:</strong>{' '}
                {result.model_strategy.candidate_model_families?.map((m, i) => <Badge key={i} label={m} color="#1565c0" />)}</div>
              <div style={s.field}><strong>Baseline Models:</strong>{' '}
                {result.model_strategy.baseline_models?.map((m, i) => <Badge key={i} label={m} color="#6a1b9a" />)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );

  const renderValidationAndMore = () => (
    <div>
      {result?.validation_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Validation Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Split:</strong> {result.validation_strategy.split_strategy}</div>
            <div style={s.field}><strong>n_splits:</strong> {result.validation_strategy.n_splits}</div>
            {result.validation_strategy.test_size != null && <div style={s.field}><strong>Test Size:</strong> {result.validation_strategy.test_size}</div>}
            <div style={s.field}><strong>Stratification:</strong> {result.validation_strategy.stratification_required ? 'Yes' : 'No'}</div>
          </div>
        </div>
      )}
      {result?.evaluation_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Evaluation Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Primary Metric:</strong> {result.evaluation_strategy.primary_metric}</div>
            <div style={s.field}><strong>Secondary:</strong> {result.evaluation_strategy.secondary_metrics?.join(', ')}</div>
            <div style={s.field}><strong>Direction:</strong> {result.evaluation_strategy.metric_direction}</div>
          </div>
        </div>
      )}
      {result?.hpo_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>HPO Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Enabled:</strong> {result.hpo_strategy.enabled ? 'Yes' : 'No'}</div>
            {result.hpo_strategy.enabled && (
              <>
                <div style={s.field}><strong>Search Method:</strong> {result.hpo_strategy.search_method}</div>
                <div style={s.field}><strong>Budget:</strong> {result.hpo_strategy.budget_level} ({result.hpo_strategy.max_trials} trials)</div>
              </>
            )}
          </div>
        </div>
      )}
      {result?.interpretability_strategy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Interpretability Strategy</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Enabled:</strong> {result.interpretability_strategy.enabled ? 'Yes' : 'No'}</div>
            {result.interpretability_strategy.enabled && (
              <>
                <div style={s.field}><strong>Priority:</strong> {result.interpretability_strategy.priority}</div>
                <div style={s.field}><strong>Methods:</strong>{' '}
                  {result.interpretability_strategy.methods?.map((m, i) => <Badge key={i} label={m} color="#00838f" />)}</div>
              </>
            )}
          </div>
        </div>
      )}

      {result?.pipeline_generation_input && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Pipeline Generation Input</h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {result.pipeline_generation_input.pipeline_steps?.map((step, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '20px', height: '20px', borderRadius: '50%', backgroundColor: '#1976d2', color: '#fff', fontSize: '11px', fontWeight: 600 }}>{i + 1}</span>
                <span>{step}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {result?.workflow_rationale && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Workflow Rationale</h4>
          {result.workflow_rationale.overall_reasoning_summary && (
            <p style={s.summaryText}>{result.workflow_rationale.overall_reasoning_summary}</p>
          )}
          {result.workflow_rationale.key_assumptions?.length > 0 && (
            <div style={s.field}><strong>Key Assumptions:</strong><ul style={s.list}>{result.workflow_rationale.key_assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul></div>
          )}
          {result.workflow_rationale.known_risks?.length > 0 && (
            <div style={s.field}><strong>Known Risks:</strong><ul style={s.list}>{result.workflow_rationale.known_risks.map((r, i) => <li key={i}>{r}</li>)}</ul></div>
          )}
        </div>
      )}

      {result?.execution_hints && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Execution Hints</h4>
          {result.execution_hints.module_order?.length > 0 && (
            <div style={s.field}><strong>Module Order:</strong>{' '}
              {result.execution_hints.module_order.map((m, i) => <Badge key={i} label={`${i + 1}. ${m}`} color="#00838f" />)}</div>
          )}
        </div>
      )}

      {result?.llm_reasoning_summary && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>AI Reasoning Summary</h4>
          <p style={s.summaryText}>{result.llm_reasoning_summary}</p>
        </div>
      )}
    </div>
  );

  const renderTab = (tabId: string, label: string) => (
    <button key={tabId} onClick={() => setActiveTab(tabId)} style={{
      ...s.tabButton,
      backgroundColor: activeTab === tabId ? '#1976d2' : '#e0e0e0',
      color: activeTab === tabId ? '#fff' : '#333',
    }}>{label}</button>
  );

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'features', label: 'Feature Strategy' },
    { id: 'model', label: 'Model Strategy' },
    { id: 'planning', label: 'Validation & More' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>AI-guided Workflow Planning</h3>
      <p style={s.description}>
        Generate a structured machine learning workflow plan based on task specification,
        task interpretation, and dataset profiling results.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRunPlanning} disabled={loading} style={s.runButton}>
          {loading ? 'Planning...' : 'Run Workflow Planning'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Planning...' : 'Re-run Planning'}
        </button>
      </div>

      {error && <div style={s.errorBox}><strong>Error:</strong> {error}</div>}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Workflow Plan Result</h4>

          <div style={s.fieldRow}>
            <div style={s.field}><strong>Plan ID:</strong> {result.workflow_plan_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={result.status} color={getStatusColor(result.status)} />
            </div>
            <div style={s.field}><strong>Confidence:</strong> {result.confidence_score}</div>
            {result.fe_registry_snapshot_version && (
              <div style={s.field}><strong>Registry:</strong> {result.fe_registry_snapshot_version}</div>
            )}
          </div>

          {(result.planning_warnings?.length ?? 0) > 0 && (
            <div style={s.warningBox}><strong>Planning Warnings:</strong>
              <ul style={s.list}>{result.planning_warnings?.map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}

          {(result.planning_assumptions?.length ?? 0) > 0 && (
            <div style={{ ...s.warningBox, backgroundColor: '#e3f2fd', border: '1px solid #90caf9', color: '#1565c0' }}>
              <strong>Planning Assumptions:</strong>
              <ul style={s.list}>{result.planning_assumptions?.map((a, i) => <li key={i}>{a}</li>)}</ul>
            </div>
          )}

          <div style={s.tabBar}>{tabs.map(t => renderTab(t.id, t.label))}</div>

          <div style={s.tabContent}>
            {activeTab === 'summary' && renderSummary()}
            {activeTab === 'features' && renderFeatureStrategy()}
            {activeTab === 'model' && renderModelStrategy()}
            {activeTab === 'planning' && renderValidationAndMore()}
            {activeTab === 'json' && (
              <div style={s.card}><h4 style={s.cardTitle}>Full JSON</h4><pre style={s.json}>{JSON.stringify(result, null, 2)}</pre></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: { marginTop: '24px', padding: '16px', border: '1px solid #e0e0e0', borderRadius: '8px', backgroundColor: '#fafafa' },
  title: { margin: '0 0 8px 0', fontSize: '18px', fontWeight: 600 },
  description: { margin: '0 0 16px 0', color: '#666', fontSize: '13px', lineHeight: 1.5 },
  buttonRow: { display: 'flex', gap: '8px', marginBottom: '16px' },
  runButton: { padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' },
  rerunButton: { padding: '10px 20px', backgroundColor: '#f57c00', color: '#fff', border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer' },
  errorBox: { padding: '12px', backgroundColor: '#ffebee', border: '1px solid #f44336', borderRadius: '4px', color: '#c62828', marginBottom: '16px' },
  resultBox: { padding: '16px', backgroundColor: '#fff', border: '1px solid #e0e0e0', borderRadius: '8px' },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  fieldRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  badge: { display: 'inline-block', padding: '2px 8px', borderRadius: '12px', color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px' },
  warningBox: { padding: '12px', backgroundColor: '#fff3e0', border: '1px solid #ff9800', borderRadius: '4px', color: '#e65100', marginBottom: '16px' },
  list: { margin: '4px 0', paddingLeft: '20px' },
  tabBar: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' },
  tabButton: { padding: '6px 14px', border: 'none', borderRadius: '16px', fontSize: '13px', fontWeight: 600, cursor: 'pointer' },
  tabContent: { minHeight: '200px', maxHeight: '60vh', overflowY: 'auto' as const },
  card: { padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px', marginBottom: '12px', border: '1px solid #e0e0e0', overflowX: 'auto' as const },
  subCard: { padding: '10px', backgroundColor: '#fff', borderRadius: '4px', marginBottom: '8px', border: '1px solid #eee', marginTop: '8px', overflowX: 'auto' as const },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  summaryText: { marginTop: '8px', color: '#333', fontSize: '14px', lineHeight: 1.5 },
  innerTable: { width: '100%', borderCollapse: 'collapse' as const, fontSize: '12px', tableLayout: 'fixed' as const },
  th: { textAlign: 'left' as const, padding: '6px 8px', borderBottom: '2px solid #e0e0e0', fontWeight: 600, backgroundColor: '#fafafa', whiteSpace: 'nowrap' as const, fontSize: '12px' },
  td: { padding: '6px 8px', borderBottom: '1px solid #eee', verticalAlign: 'top' as const, wordBreak: 'break-word' as const, fontSize: '12px' },
  json: { backgroundColor: '#263238', color: '#aed581', padding: '12px', borderRadius: '4px', overflow: 'auto', fontSize: '11px' },
};

export default WorkflowPlanPanel;
