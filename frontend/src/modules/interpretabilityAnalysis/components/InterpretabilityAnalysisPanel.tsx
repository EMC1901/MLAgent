import React, { useState } from 'react';
import {
  createInterpretabilityAnalysis,
  rerunInterpretabilityAnalysis,
} from '../../../api/interpretabilityAnalysisApi';
import {
  InterpretabilityAnalysisResponse,
  GlobalFeatureImportanceItem,
  ShapSummary,
  LocalExplanationItem,
  HighErrorSampleAnalysis,
  MaterialInsightSummary,
  LLMInterpretabilitySummary,
  MaterialPattern,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  PROFILE_LABELS,
  CONFIDENCE_COLORS,
  EVIDENCE_COLORS,
  METHOD_LABELS,
} from '../constants';

interface InterpretabilityAnalysisPanelProps {
  taskId: string;
  initialResult?: InterpretabilityAnalysisResponse;
}

const InterpretabilityAnalysisPanel: React.FC<InterpretabilityAnalysisPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InterpretabilityAnalysisResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createInterpretabilityAnalysis(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run interpretability analysis.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunInterpretabilityAnalysis(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run interpretability analysis.');
    } finally {
      setLoading(false);
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const tabs = [
    { id: 'summary', label: 'Summary' },
    { id: 'featureImportance', label: 'Feature Importance' },
    { id: 'shap', label: 'SHAP Summary' },
    { id: 'localExplanations', label: 'Local Explanations' },
    { id: 'highError', label: 'High Error Samples' },
    { id: 'materialInsight', label: 'Material Insights' },
    { id: 'riskNotes', label: 'Risk Notes' },
    { id: 'finalOutputInput', label: 'Final Output Input' },
    { id: 'json', label: 'Full JSON' },
  ];

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

  return (
    <div style={s.container}>
      <h3 style={s.title}>Interpretability Analysis</h3>
      <p style={s.description}>
        AI-powered interpretability analysis. Provides global and local explanations for model
        predictions, feature importance, SHAP summaries, material science insights, and risk
        assessments to support informed decision-making.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Analyzing...' : 'Run Interpretability Analysis'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Analysis'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Interpretability Analysis Result</h4>

          {/* Summary bar */}
          <div style={s.fieldRow}>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={s.field}>
              <strong>Analysis ID: </strong>
              <code>{result.interpretability_analysis_id}</code>
            </div>
            {result.analysis_profile && (
              <div style={s.field}>
                <strong>Profile: </strong>
                <span>{PROFILE_LABELS[result.analysis_profile] || result.analysis_profile}</span>
              </div>
            )}
            {result.ready_for_final_output && (
              <div style={s.field}>
                <strong>Ready: </strong>
                <span style={{ color: '#2e7d32', fontWeight: 600 }}>Ready for Final Output</span>
              </div>
            )}
          </div>

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={s.warningBox}>
              <strong>Warnings:</strong>
              <ul style={s.list}>
                {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
              </ul>
            </div>
          )}

          {/* Tab navigation */}
          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          {/* Tab content */}
          <div style={s.tabContent}>
            {activeTab === 'summary' && <SummaryTab result={result} />}
            {activeTab === 'featureImportance' && <FeatureImportanceTab items={result.global_feature_importance} />}
            {activeTab === 'shap' && <ShapTab shap={result.shap_summary} />}
            {activeTab === 'localExplanations' && <LocalExplanationsTab items={result.local_explanations} />}
            {activeTab === 'highError' && <HighErrorTab items={result.high_error_sample_analysis} />}
            {activeTab === 'materialInsight' && <MaterialInsightTab insight={result.material_insight_summary} llmSummary={result.llm_interpretability_summary} />}
            {activeTab === 'riskNotes' && <RiskNotesTab risks={result.interpretability_risk_notes} warnings={result.warnings} />}
            {activeTab === 'finalOutputInput' && <FinalOutputInputTab input={result.final_output_input} />}
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


/* ---- Shared Badge ---- */

const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
  <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
);


/* ---- Summary Tab ---- */

const SummaryTab: React.FC<{ result: InterpretabilityAnalysisResponse }> = ({ result }) => (
  <div style={s.card}>
    <h4 style={s.cardTitle}>Analysis Summary</h4>
    <div style={s.grid}>
      <SummaryField label="Analysis ID" value={result.interpretability_analysis_id} />
      <SummaryField label="Final Model" value={result.final_model_id} />
      <SummaryField label="Model Family" value={result.final_model_family} />
      <SummaryField label="Final Trial" value={result.final_trial_id} />
      <SummaryField label="Profile" value={PROFILE_LABELS[result.analysis_profile] || result.analysis_profile} />
      <SummaryField label="Ready for Final Output" value={result.ready_for_final_output ? 'Yes' : 'No'} />
    </div>
    {result.interpretability_methods_used && result.interpretability_methods_used.length > 0 && (
      <div style={s.subCard}>
        <strong>Methods Used: </strong>
        {result.interpretability_methods_used.map((m, i) => (
          <span key={i} style={{ ...s.methodTag, marginLeft: i > 0 ? '4px' : '0' }}>{METHOD_LABELS[m] || m}</span>
        ))}
      </div>
    )}
  </div>
);

const SummaryField: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => (
  <div style={s.summaryField}>
    <span style={s.summaryLabel}>{label}</span>
    <span style={s.summaryValue}>{value || '-'}</span>
  </div>
);


/* ---- Feature Importance Tab ---- */

const FeatureImportanceTab: React.FC<{ items: GlobalFeatureImportanceItem[] }> = ({ items }) => (
  <div>
    {!items || items.length === 0 ? (
      <p>No feature importance data available.</p>
    ) : (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Global Feature Importance</h4>
        <div style={{ overflowX: 'auto' }}>
          <table style={s.table}>
            <thead>
              <tr>
                <th style={s.th}>Rank</th>
                <th style={s.th}>Feature</th>
                <th style={s.th}>Importance</th>
                <th style={s.th}>Method</th>
                <th style={s.th}>Feature Group</th>
                <th style={s.th}>Hint</th>
              </tr>
            </thead>
            <tbody>
              {items.map((fi, i) => (
                <tr key={i}>
                  <td style={s.td}>{fi.importance_rank}</td>
                  <td style={s.td}>{fi.feature_name}</td>
                  <td style={s.td}>{fi.importance_value.toFixed(6)}</td>
                  <td style={s.td}>
                    <span style={{ ...s.methodTag, fontSize: '11px' }}>
                      {METHOD_LABELS[fi.importance_method] || fi.importance_method}
                    </span>
                  </td>
                  <td style={s.td}>{fi.feature_group}</td>
                  <td style={{ ...s.td, fontSize: '12px', color: '#666' }}>{fi.interpretation_hint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )}
  </div>
);


/* ---- SHAP Tab ---- */

const ShapTab: React.FC<{ shap?: ShapSummary }> = ({ shap }) => (
  <div>
    {!shap ? (
      <p>No SHAP summary available.</p>
    ) : !shap.shap_available ? (
      <div style={s.card}>
        <h4 style={s.cardTitle}>SHAP Summary</h4>
        <p style={{ color: '#888', fontStyle: 'italic' }}>SHAP was not available for this model.</p>
        {shap.warnings && shap.warnings.length > 0 && (
          <div style={s.warningBox}>
            {shap.warnings.map((w, i) => <p key={i} style={{ margin: '4px 0' }}>{w}</p>)}
          </div>
        )}
      </div>
    ) : (
      <div style={s.card}>
        <h4 style={s.cardTitle}>SHAP Summary</h4>
        <div style={s.grid}>
          <SummaryField label="Explainer Type" value={shap.explainer_type} />
          <SummaryField label="Samples Explained" value={String(shap.n_samples_explained)} />
        </div>
        {shap.top_shap_features && shap.top_shap_features.length > 0 && (
          <div style={s.subCard}>
            <strong>Top SHAP Features</strong>
            <table style={{ ...s.table, tableLayout: 'auto', minWidth: 'auto', marginTop: '8px' }}>
              <thead>
                <tr>
                  <th style={s.th}>Rank</th>
                  <th style={s.th}>Feature</th>
                  <th style={s.th}>Mean |SHAP|</th>
                  <th style={s.th}>Summary</th>
                </tr>
              </thead>
              <tbody>
                {shap.top_shap_features.map((f, i) => (
                  <tr key={i}>
                    <td style={s.td}>{f.rank}</td>
                    <td style={s.td}>{f.feature_name}</td>
                    <td style={s.td}>{f.mean_abs_shap.toFixed(6)}</td>
                    <td style={{ ...s.td, wordBreak: 'break-word' }}>{f.direction_summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {shap.warnings && shap.warnings.length > 0 && (
          <div style={{ ...s.warningBox, marginTop: '12px' }}>
            <strong>SHAP Warnings:</strong>
            {shap.warnings.map((w, i) => <p key={i} style={{ margin: '2px 0', fontSize: '12px' }}>{w}</p>)}
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Local Explanations Tab ---- */

const LocalExplanationsTab: React.FC<{ items: LocalExplanationItem[] }> = ({ items }) => (
  <div>
    <div style={{
      padding: '10px 14px',
      backgroundColor: '#e3f2fd',
      border: '1px solid #90caf9',
      borderRadius: '6px',
      fontSize: '13px',
      color: '#1565c0',
      marginBottom: '16px',
      lineHeight: 1.5,
    }}>
      Per-sample prediction explanations using SHAP values. Shows up to 10 representative samples
      with their top positive and negative feature contributions. Green chips indicate features that
      pushed the prediction higher; red chips indicate features that pushed it lower.
    </div>
    {!items || items.length === 0 ? (
      <p>No local explanations available.</p>
    ) : (
      <div>
        {items.map((item, i) => (
          <div key={i} style={s.card}>
            <div style={s.cardTitle}>
              <span>Sample {item.sample_id}</span>
              {item.y_true != null && <span> &mdash; True: {item.y_true}</span>}
              {item.y_pred != null && <span> &mdash; Pred: {item.y_pred.toFixed(4)}</span>}
              {item.prediction_error != null && (
                <span style={{ color: item.prediction_error > 0.5 ? '#f44336' : '#4caf50' }}>
                  {' '}&mdash; Error: {item.prediction_error.toFixed(4)}
                </span>
              )}
            </div>
            {item.top_positive_features && item.top_positive_features.length > 0 && (
              <div style={s.featureChips}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top positive: </span>
                {item.top_positive_features.map((f, j) => (
                  <span key={j} style={{ ...s.chip, backgroundColor: '#e8f5e9', color: '#2e7d32' }}>
                    {f.feature} (+{f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            {item.top_negative_features && item.top_negative_features.length > 0 && (
              <div style={s.featureChips}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top negative: </span>
                {item.top_negative_features.map((f, j) => (
                  <span key={j} style={{ ...s.chip, backgroundColor: '#ffebee', color: '#c62828' }}>
                    {f.feature} ({f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            <p style={s.summaryText}>{item.local_explanation_summary}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);


/* ---- High Error Tab ---- */

const HighErrorTab: React.FC<{ items: HighErrorSampleAnalysis[] }> = ({ items }) => (
  <div>
    {!items || items.length === 0 ? (
      <p>No high-error sample analysis available.</p>
    ) : (
      <div>
        {items.map((item, i) => (
          <div key={i} style={s.card}>
            <h4 style={s.cardTitle}>
              Rank #{item.error_rank}: Sample {item.sample_id}
              <span style={{ color: '#f44336', marginLeft: '8px', fontSize: '13px', fontWeight: 400 }}>
                Abs Error: {item.absolute_error.toFixed(4)}
                {item.relative_error != null && ` (${(item.relative_error * 100).toFixed(1)}%)`}
              </span>
            </h4>
            <div style={s.subCard}>
              <strong>Possible Error Factors:</strong>
              <ul style={s.list}>
                {item.possible_error_factors.map((f, j) => (
                  <li key={j}>{f}</li>
                ))}
              </ul>
            </div>
            <p style={s.summaryText}>{item.feature_pattern_summary}</p>
            <p style={{ fontSize: '13px', color: '#1976d2', fontStyle: 'italic', margin: '4px 0' }}>
              {item.review_suggestion}
            </p>
          </div>
        ))}
      </div>
    )}
  </div>
);


/* ---- Material Insight Tab ---- */

const MaterialInsightTab: React.FC<{
  insight?: MaterialInsightSummary;
  llmSummary?: LLMInterpretabilitySummary;
}> = ({ insight, llmSummary }) => {
  const patterns = insight?.top_material_patterns || llmSummary?.top_material_patterns || [];
  const groups = insight?.feature_groups_interpretation || llmSummary?.feature_groups_interpretation || [];
  const hypotheses = insight?.domain_hypotheses || llmSummary?.domain_hypotheses || [];
  const limitations = insight?.limitations || llmSummary?.limitations || [];
  const confidence = insight?.confidence_level || llmSummary?.confidence_level || '';

  return (
    <div>
      <div style={s.disclaimerBox}>
        <strong>Important:</strong> These insights are model-based interpretations, not causal conclusions.
      </div>

      {confidence && (
        <div style={s.card}>
          <div style={s.field}>
            <strong>Interpretation Confidence: </strong>
            <Badge label={confidence} color={CONFIDENCE_COLORS[confidence] || '#9e9e9e'} />
          </div>
        </div>
      )}

      {patterns.length === 0 && hypotheses.length === 0 ? (
        <p>No material insights available (AI summary may have failed or was not requested).</p>
      ) : (
        <div>
          {patterns.length > 0 && (
            <div style={s.card}>
              <h4 style={s.cardTitle}>Top Material Patterns ({patterns.length})</h4>
              {patterns.map((p: MaterialPattern, i: number) => (
                <div key={i} style={s.subCard}>
                  <p style={{ fontWeight: 600, margin: '0 0 4px 0' }}>{p.pattern}</p>
                  <p style={{ fontSize: '13px', color: '#555', margin: '4px 0' }}>{p.possible_material_meaning}</p>
                  <div style={s.featureChips}>
                    <span style={{ fontSize: '12px', color: '#888' }}>Supporting features: </span>
                    {p.supporting_features.map((f, j) => (
                      <span key={j} style={s.chip}>{f}</span>
                    ))}
                  </div>
                  <div style={{ marginTop: '8px', fontSize: '12px' }}>
                    <span>
                      Evidence:{' '}
                      <span style={{
                        color: EVIDENCE_COLORS[p.evidence_strength] || '#999',
                        fontWeight: 600,
                      }}>
                        {p.evidence_strength}
                      </span>
                    </span>
                  </div>
                  <p style={{ fontSize: '11px', color: '#f57c00', fontStyle: 'italic', margin: '4px 0 0 0' }}>
                    {p.caution}
                  </p>
                </div>
              ))}
            </div>
          )}

          {hypotheses.length > 0 && (
            <div style={s.card}>
              <h4 style={s.cardTitle}>Domain Hypotheses</h4>
              <ul style={s.list}>
                {hypotheses.map((h, i) => (
                  <li key={i} style={{ marginBottom: '6px', fontSize: '14px', lineHeight: 1.5 }}>{h}</li>
                ))}
              </ul>
            </div>
          )}

          {groups.length > 0 && (
            <div style={s.card}>
              <h4 style={s.cardTitle}>Feature Groups Interpretation</h4>
              {groups.map((g: { feature_group: string; summary: string }, i: number) => (
                <div key={i} style={s.subCard}>
                  <strong>{g.feature_group}:</strong>
                  <span style={{ marginLeft: '8px', fontSize: '14px' }}>{g.summary}</span>
                </div>
              ))}
            </div>
          )}

          {limitations.length > 0 && (
            <div style={s.card}>
              <h4 style={s.cardTitle}>Limitations</h4>
              <ul style={s.list}>
                {limitations.map((l, i) => (
                  <li key={i} style={{ marginBottom: '6px', color: '#f57c00' }}>{l}</li>
                ))}
              </ul>
            </div>
          )}

          {llmSummary?.human_review_notes && llmSummary.human_review_notes.length > 0 && (
            <div style={s.card}>
              <h4 style={s.cardTitle}>Human Review Notes</h4>
              <ul style={s.list}>
                {llmSummary.human_review_notes.map((n, i) => (
                  <li key={i} style={{ marginBottom: '6px' }}>{n}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};


/* ---- Risk Notes Tab ---- */

const RiskNotesTab: React.FC<{
  risks: { risk_type?: string; description?: string; severity?: string }[];
  warnings: string[];
}> = ({ risks, warnings }) => (
  <div>
    {risks && risks.length > 0 ? (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Risk Notes ({risks.length})</h4>
        {risks.map((r, i) => (
          <div key={i} style={s.subCard}>
            <span style={{ fontWeight: 600 }}>{r.risk_type || 'Unknown Risk'}</span>
            {r.severity && (
              <span style={{
                ...s.badge,
                marginLeft: '8px',
                backgroundColor: r.severity === 'high' ? '#f44336' : r.severity === 'medium' ? '#ff9800' : '#4caf50',
              }}>
                {r.severity}
              </span>
            )}
            <p style={{ fontSize: '13px', marginTop: '8px' }}>{r.description || '-'}</p>
          </div>
        ))}
      </div>
    ) : (
      <p>No specific risk notes.</p>
    )}
    {warnings && warnings.length > 0 && (
      <div style={{ ...s.warningBox, marginTop: '12px' }}>
        <strong>System Warnings</strong>
        <ul style={s.list}>
          {warnings.map((w, i) => (
            <li key={i} style={{ marginBottom: '6px', color: '#f57c00' }}>{w}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
);


/* ---- Final Output Input Tab ---- */

const FinalOutputInputTab: React.FC<{ input?: import('../types').FinalOutputInput }> = ({ input }) => (
  <div>
    {!input ? (
      <p>No final output input available.</p>
    ) : (
      <div style={s.card}>
        <h4 style={s.cardTitle}>Final Output Input</h4>
        <div style={s.field}>
          <strong>Ready for Final Output: </strong>
          <span style={{
            color: input.ready_for_final_output ? '#2e7d32' : '#c62828',
            fontWeight: 600,
          }}>
            {input.ready_for_final_output ? 'Yes' : 'No'}
          </span>
        </div>
        <div style={{ ...s.grid, marginTop: '12px' }}>
          <SummaryField label="Interpretability Analysis" value={input.interpretability_analysis_id} />
          <SummaryField label="Final Model" value={input.final_model_id} />
          <SummaryField label="Final Trial" value={input.final_trial_id} />
          <SummaryField label="Model Artifact" value={input.model_artifact_path} />
        </div>
        {input.global_feature_importance && input.global_feature_importance.length > 0 && (
          <div style={s.subCard}>
            <strong>Global Feature Importance: </strong>
            <span>{input.global_feature_importance.length} features included</span>
          </div>
        )}
        {input.shap_summary && (
          <div style={s.subCard}>
            <strong>SHAP Summary: </strong>
            <span>Included</span>
          </div>
        )}
        {input.material_insight_summary && (
          <div style={s.subCard}>
            <strong>Material Insight Summary: </strong>
            <span>Included</span>
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Styles ---- */

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
    borderRadius: '4px', color: '#c62828', marginBottom: '16px', fontSize: '14px',
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
  },
  subCard: {
    padding: '10px', backgroundColor: '#fff', borderRadius: '4px',
    marginBottom: '8px', border: '1px solid #eee',
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  summaryText: { marginTop: '8px', color: '#333', fontSize: '14px', lineHeight: 1.5 },
  summaryField: {
    display: 'flex', flexDirection: 'column', gap: '4px',
  },
  summaryLabel: {
    fontSize: '12px', color: '#888', fontWeight: 600, textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: '15px', color: '#333', wordBreak: 'break-all',
  },
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
  featureChips: {
    display: 'flex', flexWrap: 'wrap', gap: '6px',
    alignItems: 'center', marginTop: '8px',
  },
  chip: {
    padding: '3px 8px', borderRadius: '12px', fontSize: '11px',
    fontWeight: 500, backgroundColor: '#e0e0e0', color: '#333',
  },
  methodTag: {
    display: 'inline-block', backgroundColor: '#e8eaf6', color: '#283593',
    padding: '4px 10px', borderRadius: '4px', fontSize: '12px', fontWeight: 500,
  },
  disclaimerBox: {
    padding: '10px 14px', backgroundColor: '#fff3e0',
    border: '1px solid #ffb74d', borderRadius: '6px',
    fontSize: '13px', color: '#e65100', marginBottom: '16px',
  },
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
    maxHeight: '500px',
  },
};

export default InterpretabilityAnalysisPanel;
