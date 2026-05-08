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
  DIRECTION_COLORS,
  EVIDENCE_COLORS,
  METHOD_LABELS,
} from '../constants';

interface InterpretabilityAnalysisPanelProps {
  taskId: string;
}

const InterpretabilityAnalysisPanel: React.FC<InterpretabilityAnalysisPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<InterpretabilityAnalysisResponse | null>(null);
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

  const tabs = [
    { key: 'summary', label: 'Summary' },
    { key: 'featureImportance', label: 'Feature Importance' },
    { key: 'shap', label: 'SHAP Summary' },
    { key: 'localExplanations', label: 'Local Explanations' },
    { key: 'highError', label: 'High Error Samples' },
    { key: 'materialInsight', label: 'Material Insights' },
    { key: 'riskNotes', label: 'Risk Notes' },
    { key: 'finalOutputInput', label: 'Final Output Input' },
    { key: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Interpretability Analysis</h2>

      <div style={styles.actions}>
        <button
          onClick={handleRun}
          disabled={loading || !taskId}
          style={{
            ...styles.button,
            ...styles.primaryBtn,
            ...(loading || !taskId ? styles.disabledBtn : {}),
          }}
        >
          {loading ? 'Analyzing...' : 'Run Interpretability Analysis'}
        </button>
        <button
          onClick={handleRerun}
          disabled={loading || !taskId}
          style={{
            ...styles.button,
            ...styles.secondaryBtn,
            ...(loading || !taskId ? styles.disabledBtn : {}),
          }}
        >
          Re-run Analysis
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          {error}
        </div>
      )}

      {result && (
        <div style={styles.resultContainer}>
          {/* Status bar */}
          <div style={styles.statusBar}>
            <span style={{ ...styles.statusBadge, backgroundColor: STATUS_COLORS[result.status] || '#999' }}>
              {STATUS_LABELS[result.status] || result.status}
            </span>
            {result.interpretability_analysis_id && (
              <span style={styles.idText}>ID: {result.interpretability_analysis_id}</span>
            )}
            {result.analysis_profile && (
              <span style={styles.profileTag}>
                Profile: {PROFILE_LABELS[result.analysis_profile] || result.analysis_profile}
              </span>
            )}
            {result.ready_for_final_output && (
              <span style={{ ...styles.readyBadge, backgroundColor: '#4caf50' }}>
                Ready for Final Output
              </span>
            )}
          </div>

          {/* Tab navigation */}
          <div style={styles.tabBar}>
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  ...styles.tab,
                  ...(activeTab === tab.key ? styles.activeTab : {}),
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div style={styles.tabContent}>
            {activeTab === 'summary' && <SummaryTab result={result} />}
            {activeTab === 'featureImportance' && <FeatureImportanceTab items={result.global_feature_importance} />}
            {activeTab === 'shap' && <ShapTab shap={result.shap_summary} />}
            {activeTab === 'localExplanations' && <LocalExplanationsTab items={result.local_explanations} />}
            {activeTab === 'highError' && <HighErrorTab items={result.high_error_sample_analysis} />}
            {activeTab === 'materialInsight' && <MaterialInsightTab insight={result.material_insight_summary} llmSummary={result.llm_interpretability_summary} />}
            {activeTab === 'riskNotes' && <RiskNotesTab risks={result.interpretability_risk_notes} warnings={result.warnings} />}
            {activeTab === 'finalOutputInput' && <FinalOutputInputTab input={result.final_output_input} />}
            {activeTab === 'json' && <JsonViewer data={result} />}
          </div>

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.warningsBox}>
              <strong>Warnings:</strong>
              <ul style={styles.warningList}>
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};


/* ---- Summary Tab ---- */

const SummaryTab: React.FC<{ result: InterpretabilityAnalysisResponse }> = ({ result }) => (
  <div style={styles.tabPanel}>
    <div style={styles.summaryGrid}>
      <SummaryField label="Analysis ID" value={result.interpretability_analysis_id} />
      <SummaryField label="Final Model" value={result.final_model_id} />
      <SummaryField label="Model Family" value={result.final_model_family} />
      <SummaryField label="Final Trial" value={result.final_trial_id} />
      <SummaryField label="Profile" value={PROFILE_LABELS[result.analysis_profile] || result.analysis_profile} />
      <SummaryField label="Ready for Final Output" value={result.ready_for_final_output ? 'Yes' : 'No'} />
    </div>
    {result.interpretability_methods_used && result.interpretability_methods_used.length > 0 && (
      <div style={styles.subSection}>
        <h4>Methods Used</h4>
        <div style={styles.tagContainer}>
          {result.interpretability_methods_used.map((m, i) => (
            <span key={i} style={styles.methodTag}>{METHOD_LABELS[m] || m}</span>
          ))}
        </div>
      </div>
    )}
  </div>
);

const SummaryField: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => (
  <div style={styles.summaryField}>
    <span style={styles.summaryLabel}>{label}</span>
    <span style={styles.summaryValue}>{value || '-'}</span>
  </div>
);


/* ---- Feature Importance Tab ---- */

const FeatureImportanceTab: React.FC<{ items: GlobalFeatureImportanceItem[] }> = ({ items }) => (
  <div style={styles.tabPanel}>
    {!items || items.length === 0 ? (
      <p>No feature importance data available.</p>
    ) : (
      <div style={styles.tableWrapper}>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Rank</th>
              <th style={styles.th}>Feature</th>
              <th style={styles.th}>Importance</th>
              <th style={styles.th}>Method</th>
              <th style={styles.th}>Direction</th>
              <th style={styles.th}>Feature Group</th>
              <th style={styles.th}>Hint</th>
            </tr>
          </thead>
          <tbody>
            {items.map((fi, i) => (
              <tr key={i}>
                <td style={styles.td}>{fi.importance_rank}</td>
                <td style={styles.td}>{fi.feature_name}</td>
                <td style={styles.td}>{fi.importance_value.toFixed(6)}</td>
                <td style={styles.td}>
                  <span style={{ ...styles.methodTag, fontSize: '11px' }}>
                    {METHOD_LABELS[fi.importance_method] || fi.importance_method}
                  </span>
                </td>
                <td style={styles.td}>
                  <span style={{
                    color: '#fff',
                    padding: '2px 6px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    backgroundColor: DIRECTION_COLORS[fi.direction] || '#999',
                  }}>
                    {fi.direction}
                  </span>
                </td>
                <td style={styles.td}>{fi.feature_group}</td>
                <td style={{ ...styles.td, fontSize: '12px', color: '#666' }}>{fi.interpretation_hint}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )}
  </div>
);


/* ---- SHAP Tab ---- */

const ShapTab: React.FC<{ shap?: ShapSummary }> = ({ shap }) => (
  <div style={styles.tabPanel}>
    {!shap ? (
      <p>No SHAP summary available.</p>
    ) : !shap.shap_available ? (
      <div>
        <p style={styles.infoText}>SHAP was not available for this model.</p>
        {shap.warnings && shap.warnings.length > 0 && (
          <div style={styles.warningsBox}>
            {shap.warnings.map((w, i) => <p key={i} style={{ margin: '4px 0' }}>{w}</p>)}
          </div>
        )}
      </div>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <SummaryField label="Explainer Type" value={shap.explainer_type} />
          <SummaryField label="Samples Explained" value={String(shap.n_samples_explained)} />
        </div>
        {shap.top_shap_features && shap.top_shap_features.length > 0 && (
          <div style={styles.subSection}>
            <h4>Top SHAP Features</h4>
            <table style={styles.table}>
              <thead>
                <tr>
                  <th style={styles.th}>Rank</th>
                  <th style={styles.th}>Feature</th>
                  <th style={styles.th}>Mean |SHAP|</th>
                  <th style={styles.th}>Direction</th>
                </tr>
              </thead>
              <tbody>
                {shap.top_shap_features.map((f, i) => (
                  <tr key={i}>
                    <td style={styles.td}>{f.rank}</td>
                    <td style={styles.td}>{f.feature_name}</td>
                    <td style={styles.td}>{f.mean_abs_shap.toFixed(6)}</td>
                    <td style={styles.td}>{f.direction_summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {shap.warnings && shap.warnings.length > 0 && (
          <div style={styles.warningsBox}>
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
  <div style={styles.tabPanel}>
    {!items || items.length === 0 ? (
      <p>No local explanations available.</p>
    ) : (
      <div>
        {items.map((item, i) => (
          <div key={i} style={styles.reasonBlock}>
            <div style={styles.reasonHeader}>
              <span style={{ fontWeight: 600 }}>Sample {item.sample_id}</span>
              {item.y_true != null && <span> True: {item.y_true}</span>}
              {item.y_pred != null && <span> Pred: {item.y_pred.toFixed(4)}</span>}
              {item.prediction_error != null && (
                <span style={{ color: item.prediction_error > 0.5 ? '#f44336' : '#4caf50' }}>
                  {' '}Error: {item.prediction_error.toFixed(4)}
                </span>
              )}
            </div>
            {item.top_positive_features && item.top_positive_features.length > 0 && (
              <div style={styles.featureChips}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top positive: </span>
                {item.top_positive_features.map((f, j) => (
                  <span key={j} style={{ ...styles.chip, backgroundColor: '#e8f5e9', color: '#2e7d32' }}>
                    {f.feature} (+{f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            {item.top_negative_features && item.top_negative_features.length > 0 && (
              <div style={styles.featureChips}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top negative: </span>
                {item.top_negative_features.map((f, j) => (
                  <span key={j} style={{ ...styles.chip, backgroundColor: '#ffebee', color: '#c62828' }}>
                    {f.feature} ({f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            <p style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>{item.local_explanation_summary}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);


/* ---- High Error Tab ---- */

const HighErrorTab: React.FC<{ items: HighErrorSampleAnalysis[] }> = ({ items }) => (
  <div style={styles.tabPanel}>
    {!items || items.length === 0 ? (
      <p>No high-error sample analysis available.</p>
    ) : (
      <div>
        {items.map((item, i) => (
          <div key={i} style={styles.reasonBlock}>
            <div style={styles.reasonHeader}>
              <span style={{ fontWeight: 600 }}>Rank #{item.error_rank}: Sample {item.sample_id}</span>
              <span style={{ color: '#f44336', marginLeft: '8px' }}>
                Abs Error: {item.absolute_error.toFixed(4)}
                {item.relative_error != null && ` (${(item.relative_error * 100).toFixed(1)}%)`}
              </span>
            </div>
            <div style={{ marginTop: '8px' }}>
              <h5 style={{ margin: '4px 0', fontSize: '13px' }}>Possible Error Factors:</h5>
              <ul style={{ margin: '4px 0', paddingLeft: '20px', fontSize: '13px' }}>
                {item.possible_error_factors.map((f, j) => (
                  <li key={j}>{f}</li>
                ))}
              </ul>
            </div>
            <p style={{ fontSize: '12px', color: '#666', margin: '4px 0' }}>{item.feature_pattern_summary}</p>
            <p style={{ fontSize: '12px', color: '#1976d2', fontStyle: 'italic', margin: '4px 0' }}>
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
    <div style={styles.tabPanel}>
      <div style={styles.disclaimerBox}>
        <strong>Important:</strong> These insights are model-based interpretations, not causal conclusions.
      </div>
      {confidence && (
        <div style={styles.confidenceBar}>
          <span>Interpretation Confidence:</span>
          <span style={{ ...styles.confidenceBadge, backgroundColor: CONFIDENCE_COLORS[confidence] || '#999' }}>
            {confidence}
          </span>
        </div>
      )}
      {patterns.length === 0 && hypotheses.length === 0 ? (
        <p>No material insights available (LLM summary may have failed or was not requested).</p>
      ) : (
        <div>
          {patterns.length > 0 && (
            <div style={styles.subSection}>
              <h4>Top Material Patterns</h4>
              {patterns.map((p: MaterialPattern, i: number) => (
                <div key={i} style={styles.reasonBlock}>
                  <p style={{ fontWeight: 500 }}>{p.pattern}</p>
                  <p style={{ fontSize: '13px', color: '#555' }}>{p.possible_material_meaning}</p>
                  <div style={styles.featureChips}>
                    <span style={{ fontSize: '12px', color: '#888' }}>Supporting features: </span>
                    {p.supporting_features.map((f, j) => (
                      <span key={j} style={styles.chip}>{f}</span>
                    ))}
                  </div>
                  <div style={{ display: 'flex', gap: '12px', marginTop: '8px', fontSize: '12px' }}>
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
                  <p style={{ fontSize: '11px', color: '#f57c00', fontStyle: 'italic', marginTop: '4px' }}>
                    {p.caution}
                  </p>
                </div>
              ))}
            </div>
          )}
          {hypotheses.length > 0 && (
            <div style={styles.subSection}>
              <h4>Domain Hypotheses</h4>
              <ul style={styles.noteList}>
                {hypotheses.map((h, i) => (
                  <li key={i} style={styles.noteItem}>{h}</li>
                ))}
              </ul>
            </div>
          )}
          {groups.length > 0 && (
            <div style={styles.subSection}>
              <h4>Feature Groups Interpretation</h4>
              {groups.map((g: { feature_group: string; summary: string }, i: number) => (
                <div key={i} style={{ ...styles.reasonBlock, margin: '8px 0' }}>
                  <span style={{ fontWeight: 600, fontSize: '13px' }}>{g.feature_group}:</span>
                  <span style={{ fontSize: '13px', marginLeft: '8px' }}>{g.summary}</span>
                </div>
              ))}
            </div>
          )}
          {limitations.length > 0 && (
            <div style={styles.subSection}>
              <h4>Limitations</h4>
              <ul style={styles.noteList}>
                {limitations.map((l, i) => (
                  <li key={i} style={{ ...styles.noteItem, color: '#f57c00' }}>{l}</li>
                ))}
              </ul>
            </div>
          )}
          {llmSummary?.human_review_notes && llmSummary.human_review_notes.length > 0 && (
            <div style={styles.subSection}>
              <h4>Human Review Notes</h4>
              <ul style={styles.noteList}>
                {llmSummary.human_review_notes.map((n, i) => (
                  <li key={i} style={styles.noteItem}>{n}</li>
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
  <div style={styles.tabPanel}>
    {risks && risks.length > 0 ? (
      <div>
        {risks.map((r, i) => (
          <div key={i} style={styles.reasonBlock}>
            <span style={{ fontWeight: 600 }}>{r.risk_type || 'Unknown Risk'}</span>
            {r.severity && (
              <span style={{
                marginLeft: '8px',
                padding: '2px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                backgroundColor: r.severity === 'high' ? '#f44336' : r.severity === 'medium' ? '#ff9800' : '#4caf50',
                color: '#fff',
              }}>
                {r.severity}
              </span>
            )}
            <p style={{ fontSize: '13px', marginTop: '4px' }}>{r.description || '-'}</p>
          </div>
        ))}
      </div>
    ) : (
      <p>No specific risk notes.</p>
    )}
    {warnings && warnings.length > 0 && (
      <div style={styles.subSection}>
        <h4>System Warnings</h4>
        <ul style={styles.noteList}>
          {warnings.map((w, i) => (
            <li key={i} style={{ ...styles.noteItem, color: '#f57c00' }}>{w}</li>
          ))}
        </ul>
      </div>
    )}
  </div>
);


/* ---- Final Output Input Tab ---- */

const FinalOutputInputTab: React.FC<{ input?: import('../types').FinalOutputInput }> = ({ input }) => (
  <div style={styles.tabPanel}>
    {!input ? (
      <p>No final output input available.</p>
    ) : (
      <div>
        <div style={styles.readyBar}>
          <span>Ready for Final Output:</span>
          <span style={{
            ...styles.readyBadge,
            backgroundColor: input.ready_for_final_output ? '#4caf50' : '#f44336',
          }}>
            {input.ready_for_final_output ? 'Yes' : 'No'}
          </span>
        </div>
        <div style={styles.summaryGrid}>
          <SummaryField label="Interpretability Analysis" value={input.interpretability_analysis_id} />
          <SummaryField label="Final Pipeline Selection" value={input.final_pipeline_selection_id} />
          <SummaryField label="Final Model" value={input.final_model_id} />
          <SummaryField label="Final Trial" value={input.final_trial_id} />
          <SummaryField label="Model Artifact" value={input.model_artifact_path} />
        </div>
        {input.global_feature_importance && input.global_feature_importance.length > 0 && (
          <div style={styles.subSection}>
            <h4>Global Feature Importance ({input.global_feature_importance.length} features)</h4>
          </div>
        )}
        {input.shap_summary && (
          <div style={styles.subSection}>
            <h4>SHAP Summary Included</h4>
          </div>
        )}
        {input.material_insight_summary && (
          <div style={styles.subSection}>
            <h4>Material Insight Summary Included</h4>
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- JSON Viewer ---- */

const JsonViewer: React.FC<{ data: unknown }> = ({ data }) => (
  <div style={styles.tabPanel}>
    <pre style={styles.jsonBlock}>
      {JSON.stringify(data, null, 2)}
    </pre>
  </div>
);


/* ---- Styles ---- */

const styles: Record<string, React.CSSProperties> = {
  container: {
    border: '1px solid #ddd',
    borderRadius: '8px',
    padding: '20px',
    marginTop: '16px',
    backgroundColor: '#fff',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '20px',
    fontWeight: 600,
  },
  actions: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
  },
  button: {
    padding: '10px 24px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
  },
  primaryBtn: {
    backgroundColor: '#1976d2',
    color: '#fff',
  },
  secondaryBtn: {
    backgroundColor: '#f5f5f5',
    color: '#333',
    border: '1px solid #ccc',
  },
  disabledBtn: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  errorBox: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  resultContainer: {
    marginTop: '16px',
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  statusBadge: {
    color: '#fff',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: 500,
  },
  idText: {
    fontSize: '13px',
    color: '#666',
    fontFamily: 'monospace',
  },
  profileTag: {
    fontSize: '12px',
    backgroundColor: '#e3f2fd',
    color: '#1565c0',
    padding: '2px 8px',
    borderRadius: '4px',
  },
  readyBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  readyBadge: {
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '10px',
    fontSize: '12px',
    fontWeight: 500,
  },
  tabBar: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '4px',
    borderBottom: '2px solid #e0e0e0',
    marginBottom: '16px',
    paddingBottom: '8px',
  },
  tab: {
    padding: '6px 14px',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    fontSize: '13px',
    borderRadius: '4px',
    color: '#666',
  },
  activeTab: {
    backgroundColor: '#e3f2fd',
    color: '#1565c0',
    fontWeight: 600,
  },
  tabContent: {
    minHeight: '200px',
  },
  tabPanel: {
    padding: '8px 0',
  },
  summaryGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
    gap: '12px',
    marginBottom: '16px',
  },
  summaryField: {
    display: 'flex',
    flexDirection: 'column',
    gap: '4px',
  },
  summaryLabel: {
    fontSize: '12px',
    color: '#888',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  summaryValue: {
    fontSize: '15px',
    color: '#333',
    wordBreak: 'break-all',
  },
  subSection: {
    marginTop: '16px',
    marginBottom: '16px',
  },
  tableWrapper: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '8px 10px',
    borderBottom: '2px solid #e0e0e0',
    fontWeight: 600,
    color: '#555',
    backgroundColor: '#fafafa',
  },
  td: {
    padding: '8px 10px',
    borderBottom: '1px solid #f0f0f0',
  },
  infoText: {
    color: '#888',
    fontStyle: 'italic',
  },
  noteList: {
    margin: '8px 0',
    paddingLeft: '20px',
  },
  noteItem: {
    marginBottom: '6px',
    fontSize: '14px',
    lineHeight: 1.5,
  },
  warningsBox: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#fff3e0',
    border: '1px solid #ffe0b2',
    borderRadius: '6px',
    fontSize: '13px',
  },
  warningList: {
    margin: '8px 0 0 0',
    paddingLeft: '20px',
  },
  reasonBlock: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#fafafa',
    borderRadius: '6px',
    border: '1px solid #eee',
  },
  reasonHeader: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flexWrap: 'wrap',
    fontSize: '14px',
  },
  featureChips: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
    alignItems: 'center',
    marginTop: '8px',
  },
  chip: {
    padding: '3px 8px',
    borderRadius: '12px',
    fontSize: '11px',
    fontWeight: 500,
    backgroundColor: '#e0e0e0',
    color: '#333',
  },
  tagContainer: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '6px',
  },
  methodTag: {
    backgroundColor: '#e8eaf6',
    color: '#283593',
    padding: '4px 10px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: 500,
  },
  confidenceBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  confidenceBadge: {
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '10px',
    fontSize: '12px',
    fontWeight: 500,
  },
  disclaimerBox: {
    padding: '10px 14px',
    backgroundColor: '#fff3e0',
    border: '1px solid #ffb74d',
    borderRadius: '6px',
    fontSize: '13px',
    color: '#e65100',
    marginBottom: '16px',
  },
  jsonBlock: {
    backgroundColor: '#263238',
    color: '#aed581',
    padding: '16px',
    borderRadius: '6px',
    fontSize: '12px',
    overflowX: 'auto',
    maxHeight: '600px',
    overflowY: 'auto',
    fontFamily: 'monospace',
  },
};

export default InterpretabilityAnalysisPanel;
