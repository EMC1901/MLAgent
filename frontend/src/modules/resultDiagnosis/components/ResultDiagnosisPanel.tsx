import React, { useState } from 'react';
import {
  createResultDiagnosis,
  rerunResultDiagnosis,
  getIterationContextForDiagnosis,
  checkNeedsFreshDiagnosis,
} from '../../../api/resultDiagnosisApi';
import {
  ResultDiagnosisResponse,
  OverallAssessment,
  DiagnosticFinding,
  EvidenceItem,
  RootCauseHypothesis,
  RefinementRecommendation,
  SystemDiagnosticChecks,
  LLMDiagnosisResult,
  ClosedLoopRefinementInput,
  EvidenceSummary,
  IterationContext,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  DIAGNOSIS_TYPE_COLORS,
  SEVERITY_COLORS,
  CONFIDENCE_COLORS,
  EVIDENCE_STRENGTH_COLORS,
  PRIORITY_COLORS,
  PERFORMANCE_COLORS,
  IMPROVEMENT_LABELS,
  STABILITY_LABELS,
  TARGET_STAGE_LABELS,
  RECOMMENDATION_TYPE_LABELS,
  DIAGNOSIS_MODE_LABELS,
} from '../constants';

interface ResultDiagnosisPanelProps {
  taskId: string;
}

const ResultDiagnosisPanel: React.FC<ResultDiagnosisPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResultDiagnosisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [iterationCtx, setIterationCtx] = useState<IterationContext | null>(null);

  const fetchIterationContext = async (rdId: string) => {
    try {
      const ctxResp = await getIterationContextForDiagnosis(rdId);
      if (ctxResp.success) {
        setIterationCtx(ctxResp.data);
      } else {
        setIterationCtx(null);
      }
    } catch {
      setIterationCtx(null);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setIterationCtx(null);
    try {
      // Check if existing diagnosis is stale — if so, force a fresh run
      let forceRerun = false;
      try {
        const freshCheck = await checkNeedsFreshDiagnosis(taskId);
        if (freshCheck.success && freshCheck.data.needs_fresh) {
          forceRerun = true;
        }
      } catch {
        // If check fails, proceed with normal run
      }

      const response = await createResultDiagnosis(taskId, { force_rerun: forceRerun });
      if (response.success) {
        setResult(response.data);
        if (response.data.result_diagnosis_id) {
          await fetchIterationContext(response.data.result_diagnosis_id);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run result diagnosis.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setIterationCtx(null);
    try {
      const response = await rerunResultDiagnosis(taskId);
      if (response.success) {
        setResult(response.data);
        if (response.data.result_diagnosis_id) {
          await fetchIterationContext(response.data.result_diagnosis_id);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run result diagnosis.');
    } finally {
      setLoading(false);
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={s.section}>
      <strong style={s.sectionTitle}>{title}</strong>
      <div style={s.sectionContent}>{children}</div>
    </div>
  );

  const renderOverallAssessment = (oa: OverallAssessment | null | undefined) => {
    if (!oa) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Overall Assessment</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Performance: </strong>
            <Badge label={oa.performance_level} color={PERFORMANCE_COLORS[oa.performance_level] || '#9e9e9e'} />
          </div>
          <div style={s.field}>
            <strong>Baseline Improvement: </strong>
            <span>{IMPROVEMENT_LABELS[oa.baseline_improvement_level] || oa.baseline_improvement_level}</span>
          </div>
          <div style={s.field}>
            <strong>Stability: </strong>
            <span>{STABILITY_LABELS[oa.stability_level] || oa.stability_level}</span>
          </div>
          <div style={s.field}>
            <strong>Main Issue: </strong>
            <Badge label={oa.main_issue_category || 'none'} color={DIAGNOSIS_TYPE_COLORS[oa.main_issue_category] || '#9e9e9e'} />
          </div>
          <div style={s.field}>
            <strong>Should Refine: </strong>
            <span style={{ color: oa.should_refine ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {oa.should_refine ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Confidence: </strong>
            <Badge label={oa.confidence_level} color={CONFIDENCE_COLORS[oa.confidence_level] || '#9e9e9e'} />
          </div>
        </div>
        <div style={s.summaryText}>{oa.summary}</div>
      </div>
    );
  };

  const renderDiagnosticFindings = (findings: DiagnosticFinding[]) => {
    if (!findings || findings.length === 0) return <p>No diagnostic findings.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Diagnostic Findings ({findings.length})</h4>
        <table style={s.table}>
          <colgroup>
            <col style={{ width: '130px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '90px' }} />
            <col style={{ width: '200px' }} />
            <col style={{ width: '120px' }} />
            <col style={{ width: '180px' }} />
            <col style={{ width: '100px' }} />
          </colgroup>
          <thead>
            <tr>
              <th style={s.th}>Type</th>
              <th style={s.th}>Severity</th>
              <th style={s.th}>Evidence</th>
              <th style={s.th}>Description</th>
              <th style={s.th}>Affected Models</th>
              <th style={s.th}>Recommended Actions</th>
              <th style={s.th}>Confidence</th>
            </tr>
          </thead>
          <tbody>
            {findings.map((f, i) => (
              <tr key={f.finding_id || i}>
                <td style={s.td}>
                  <Badge label={f.diagnosis_type} color={DIAGNOSIS_TYPE_COLORS[f.diagnosis_type] || '#9e9e9e'} />
                </td>
                <td style={s.td}>
                  <Badge label={f.severity} color={SEVERITY_COLORS[f.severity] || '#9e9e9e'} />
                </td>
                <td style={s.td}>
                  <Badge label={f.evidence_strength} color={EVIDENCE_STRENGTH_COLORS[f.evidence_strength] || '#9e9e9e'} />
                </td>
                <td style={s.td}>{f.description}</td>
                <td style={s.td}>{(f.affected_models || []).join(', ') || '-'}</td>
                <td style={s.td}>
                  <ul style={s.list}>
                    {(f.recommended_actions || []).slice(0, 3).map((a, j) => (
                      <li key={j}>{a}</li>
                    ))}
                  </ul>
                </td>
                <td style={s.td}>
                  <Badge label={f.confidence_level} color={CONFIDENCE_COLORS[f.confidence_level] || '#9e9e9e'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderEvidenceItems = (items: EvidenceItem[], title: string) => {
    if (!items || items.length === 0) return null;
    return (
      <div style={s.subCard}>
        <strong>{title}</strong>
        <table style={s.smallTable}>
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
            {items.map((e, i) => (
              <tr key={i}>
                <td style={s.td}>{e.evidence_type}</td>
                <td style={s.td}>{e.source_module}</td>
                <td style={s.td}>{e.source_field}</td>
                <td style={s.td}>{typeof e.value === 'object' ? JSON.stringify(e.value) : String(e.value ?? '-')}</td>
                <td style={s.td}>{e.interpretation}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderEvidenceSummary = (es: EvidenceSummary | null | undefined) => {
    if (!es) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Evidence Summary</h4>
        {renderEvidenceItems(es.metric_evidence, 'Metric Evidence')}
        {renderEvidenceItems(es.baseline_evidence, 'Baseline Evidence')}
        {renderEvidenceItems(es.fold_stability_evidence, 'Fold Stability Evidence')}
        {renderEvidenceItems(es.dataset_evidence, 'Dataset Evidence')}
        {renderEvidenceItems(es.feature_evidence, 'Feature Evidence')}
        {renderEvidenceItems(es.pipeline_evidence, 'Pipeline Evidence')}
      </div>
    );
  };

  const renderRootCauseHypotheses = (hypotheses: RootCauseHypothesis[]) => {
    if (!hypotheses || hypotheses.length === 0) return null;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Root Cause Hypotheses</h4>
        {hypotheses.map((h, i) => (
          <div key={h.hypothesis_id || i} style={s.subCard}>
            <div style={s.grid}>
              <div style={s.field}>
                <strong>Type: </strong><span>{h.root_cause_type}</span>
              </div>
              <div style={s.field}>
                <strong>Likelihood: </strong><Badge label={h.likelihood} color={CONFIDENCE_COLORS[h.likelihood] || '#9e9e9e'} />
              </div>
              <div style={s.field}>
                <strong>Actionability: </strong><Badge label={h.actionability} />
              </div>
            </div>
            <p style={s.summaryText}>{h.description}</p>
            <div><strong>Supporting Findings:</strong> {(h.supporting_findings || []).join(', ') || '-'}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderRefinementRecommendations = (recs: RefinementRecommendation[]) => {
    if (!recs || recs.length === 0) return <p>No refinement recommendations.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Refinement Recommendations ({recs.length})</h4>
        <table style={s.table}>
          <colgroup>
            <col style={{ width: '140px' }} />
            <col style={{ width: '140px' }} />
            <col style={{ width: '80px' }} />
            <col style={{ width: '200px' }} />
            <col style={{ width: '160px' }} />
            <col style={{ width: '140px' }} />
            <col style={{ width: '100px' }} />
          </colgroup>
          <thead>
            <tr>
              <th style={s.th}>Target Stage</th>
              <th style={s.th}>Type</th>
              <th style={s.th}>Priority</th>
              <th style={s.th}>Description</th>
              <th style={s.th}>Expected Benefit</th>
              <th style={s.th}>Risk</th>
              <th style={s.th}>Human Review</th>
            </tr>
          </thead>
          <tbody>
            {recs.map((r, i) => (
              <tr key={r.recommendation_id || i}>
                <td style={s.td}>
                  <span>{TARGET_STAGE_LABELS[r.target_stage] || r.target_stage}</span>
                </td>
                <td style={s.td}>
                  <span>{RECOMMENDATION_TYPE_LABELS[r.recommendation_type] || r.recommendation_type}</span>
                </td>
                <td style={s.td}>
                  <Badge label={r.priority} color={PRIORITY_COLORS[r.priority] || '#9e9e9e'} />
                </td>
                <td style={s.td}>{r.description}</td>
                <td style={s.td}>{r.expected_benefit}</td>
                <td style={s.td}>{r.risk}</td>
                <td style={s.td}>{r.requires_human_review ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderSystemChecks = (checks: SystemDiagnosticChecks | null | undefined) => {
    if (!checks) return null;
    const checkItems = [
      { key: 'weak_baseline_improvement', label: 'Weak Baseline Improvement' },
      { key: 'high_fold_variance', label: 'High Fold Variance' },
      { key: 'all_models_weak', label: 'All Models Weak' },
      { key: 'hpo_budget_limited', label: 'HPO Budget Limited' },
      { key: 'small_sample_warning', label: 'Small Sample Warning' },
      { key: 'feature_count_low', label: 'Feature Count Low' },
      { key: 'many_features_dropped', label: 'Many Features Dropped' },
      { key: 'candidate_underperforms_baseline', label: 'Candidate Underperforms Baseline' },
      { key: 'unstable_best_model', label: 'Unstable Best Model' },
    ];
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>System Diagnostic Checks</h4>
        <div style={s.grid}>
          {checkItems.map(({ key, label }) => (
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
        {checks.warnings && checks.warnings.length > 0 && (
          <div style={s.warningBox}>
            <strong>Warnings:</strong>
            <ul style={s.list}>
              {checks.warnings.map((w: string, i: number) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    );
  };

  const renderLLMDiagnosis = (llm: LLMDiagnosisResult | null | undefined) => {
    if (!llm) return <p>LLM diagnosis not available (fallback mode or LLM disabled).</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>LLM Diagnosis</h4>
        <div style={s.field}>
          <strong>Confidence: </strong>
          <Badge label={llm.confidence_level || 'unknown'} color={CONFIDENCE_COLORS[llm.confidence_level] || '#9e9e9e'} />
        </div>
        <div style={s.field}>
          <strong>Findings: </strong>{llm.diagnostic_findings?.length || 0}
        </div>
        <div style={s.field}>
          <strong>Hypotheses: </strong>{llm.root_cause_hypotheses?.length || 0}
        </div>
        <div style={s.field}>
          <strong>Recommendations: </strong>{llm.refinement_recommendations?.length || 0}
        </div>
      </div>
    );
  };

  const renderClosedLoopInput = (cli: ClosedLoopRefinementInput | null | undefined) => {
    if (!cli) return <p>No closed-loop refinement input available.</p>;
    return (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Closed-loop Refinement Input</h4>
        <div style={s.grid}>
          <div style={s.field}>
            <strong>Should Refine: </strong>
            <span style={{ color: cli.should_refine ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {cli.should_refine ? 'Yes' : 'No'}
            </span>
          </div>
          <div style={s.field}>
            <strong>Ready: </strong>
            <span style={{ color: cli.ready_for_closed_loop_refinement ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
              {cli.ready_for_closed_loop_refinement ? 'Yes' : 'No'}
            </span>
          </div>
        </div>
        <div style={s.field}>
          <strong>Refinement Focus: </strong>
          {(cli.refinement_focus || []).map((f: string) => (
            <Badge key={f} label={TARGET_STAGE_LABELS[f] || f} color="#1976d2" />
          ))}
        </div>
        {cli.constraints_to_preserve && cli.constraints_to_preserve.length > 0 && (
          <div style={s.field}>
            <strong>Constraints to Preserve: </strong>
            {(cli.constraints_to_preserve || []).join(', ')}
          </div>
        )}
        {cli.avoid_actions && cli.avoid_actions.length > 0 && (
          <div style={s.field}>
            <strong>Actions to Avoid: </strong>
            <ul style={s.list}>
              {(cli.avoid_actions || []).map((a: string, i: number) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}
        {cli.suggested_next_iteration_profile && (
          <div style={s.subCard}>
            <strong>Suggested Next Iteration:</strong>
            <div>Budget: {cli.suggested_next_iteration_profile.model_search_budget}</div>
            <div>HPO: {cli.suggested_next_iteration_profile.hpo_trials}</div>
            <div>Features: {cli.suggested_next_iteration_profile.feature_strategy}</div>
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
    { id: 'overview', label: 'Overview' },
    { id: 'findings', label: 'Findings' },
    { id: 'evidence', label: 'Evidence' },
    { id: 'hypotheses', label: 'Hypotheses' },
    { id: 'recommendations', label: 'Recommendations' },
    { id: 'system', label: 'System Checks' },
    { id: 'llm', label: 'LLM Diagnosis' },
    { id: 'closed_loop', label: 'Closed-loop Input' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>LLM-based Result Diagnosis</h3>
      <p style={s.description}>
        Analyzes model evaluation results using LLM and rule-based diagnostics to identify
        potential issues (overfitting, underfitting, feature insufficiency, HPO limitations, etc.)
        and generates structured refinement recommendations for closed-loop optimization.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Diagnosing...' : 'Run Diagnosis'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Diagnosis'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Result Diagnosis</h4>

          {/* Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}><strong>Diagnosis ID:</strong> {result.result_diagnosis_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}>
              <strong>Mode: </strong>
              <span>{DIAGNOSIS_MODE_LABELS[result.diagnosis_mode] || result.diagnosis_mode}</span>
            </div>
            {iterationCtx && iterationCtx.is_part_of_iteration && (
              <div style={s.field}>
                <strong>Iteration: </strong>
                <span style={{
                  display: 'inline-block', padding: '2px 10px', borderRadius: '12px',
                  color: '#fff', fontSize: '13px', fontWeight: 700,
                  backgroundColor: '#7b1fa2',
                }}>
                  #{iterationCtx.iteration_index}
                </span>
                <span style={{ color: '#666', fontSize: '12px', marginLeft: '4px' }}>
                  (analysis {iterationCtx.diagnosis_position} of {iterationCtx.total_diagnoses})
                </span>
              </div>
            )}
            {iterationCtx && !iterationCtx.is_part_of_iteration && iterationCtx.total_diagnoses > 1 && (
              <div style={s.field}>
                <strong>Iteration: </strong>
                <span style={{
                  display: 'inline-block', padding: '2px 10px', borderRadius: '12px',
                  color: '#fff', fontSize: '13px', fontWeight: 700,
                  backgroundColor: '#f57c00',
                }}>
                  Analysis #{iterationCtx.diagnosis_position}
                </span>
                <span style={{ color: '#666', fontSize: '12px', marginLeft: '4px' }}>
                  of {iterationCtx.total_diagnoses} — run Workflow Refinement next to evaluate
                </span>
              </div>
            )}
            {iterationCtx && !iterationCtx.is_part_of_iteration && iterationCtx.total_diagnoses <= 1 && (
              <div style={s.field}>
                <strong>Iteration: </strong>
                <span style={{ color: '#999', fontSize: '13px' }}>Initial analysis (not yet refined)</span>
              </div>
            )}
            <div style={s.field}>
              <strong>Ready for Closed-loop: </strong>
              <span style={{ color: result.ready_for_closed_loop_refinement ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                {result.ready_for_closed_loop_refinement ? 'Yes' : 'No'}
              </span>
            </div>
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningBox}>
              <strong>Warnings:</strong>
              <ul style={s.list}>
                {result.warnings.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {result.error_message && (
            <div style={s.errorBox}>
              <strong>Error:</strong> {result.error_message}
            </div>
          )}

          {/* Tab navigation */}
          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          {/* Tab content */}
          <div style={s.tabContent}>
            {activeTab === 'overview' && renderOverallAssessment(result.overall_assessment)}
            {activeTab === 'findings' && renderDiagnosticFindings(result.diagnostic_findings)}
            {activeTab === 'evidence' && renderEvidenceSummary(result.evidence_summary)}
            {activeTab === 'hypotheses' && renderRootCauseHypotheses(result.root_cause_hypotheses)}
            {activeTab === 'recommendations' && renderRefinementRecommendations(result.refinement_recommendations)}
            {activeTab === 'system' && renderSystemChecks(result.system_diagnostic_checks)}
            {activeTab === 'llm' && renderLLMDiagnosis(result.llm_diagnosis)}
            {activeTab === 'closed_loop' && renderClosedLoopInput(result.closed_loop_refinement_input)}
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
    padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff',
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
  section: { marginBottom: '12px' },
  sectionTitle: { display: 'block', marginBottom: '6px', fontSize: '14px' },
  sectionContent: {},
  table: {
    width: '100%', borderCollapse: 'collapse' as const, fontSize: '13px',
    tableLayout: 'fixed' as const, minWidth: '900px',
  },
  smallTable: {
    width: '100%', borderCollapse: 'collapse' as const, fontSize: '12px',
    marginTop: '6px', tableLayout: 'fixed' as const, minWidth: '700px',
  },
  th: {
    textAlign: 'left' as const, padding: '6px 8px', borderBottom: '2px solid #e0e0e0',
    fontWeight: 600, backgroundColor: '#fafafa', whiteSpace: 'nowrap' as const,
  },
  td: {
    padding: '6px 8px', borderBottom: '1px solid #eee',
    verticalAlign: 'top' as const, wordBreak: 'break-word' as const,
    overflowWrap: 'break-word' as const,
  },
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
    maxHeight: '500px',
  },
};

export default ResultDiagnosisPanel;
