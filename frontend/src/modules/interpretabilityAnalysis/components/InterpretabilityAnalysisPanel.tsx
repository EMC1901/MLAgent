import React, { useState } from 'react';
import { Button, Space, Tabs, Card, Tag, Alert, Collapse } from 'antd';
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
  AcademicInsight,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  PROFILE_LABELS,
  CONFIDENCE_COLORS,
  EVIDENCE_COLORS,
  METHOD_LABELS,
} from '../constants';
import { pipelineAccent } from '../../../theme/pipelineColors';
import { PanelContainer, StatusBadge, WarningBox, ErrorBox, JsonViewer, EmptyState } from '../../../components/shared';

/* ---- Shared inline styles for tab renderers ---- */

const grid2Col: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: 8,
  marginBottom: 8,
};

const summaryFieldStyle: React.CSSProperties = {
  display: 'flex',
  flexDirection: 'column',
  gap: 4,
};

const summaryLabelStyle: React.CSSProperties = {
  fontSize: 12,
  color: '#888',
  fontWeight: 600,
  textTransform: 'uppercase',
};

const summaryValueStyle: React.CSSProperties = {
  fontSize: 15,
  color: '#333',
  wordBreak: 'break-all',
};

const tableStyle: React.CSSProperties = {
  width: '100%',
  borderCollapse: 'collapse',
  fontSize: 13,
};

const thStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '6px 8px',
  borderBottom: '2px solid #e0e0e0',
  fontWeight: 600,
  backgroundColor: '#fafafa',
  whiteSpace: 'nowrap',
};

const tdStyle: React.CSSProperties = {
  padding: '6px 8px',
  borderBottom: '1px solid #eee',
  verticalAlign: 'top',
  wordBreak: 'break-word',
};

const chipPositive: React.CSSProperties = {
  padding: '3px 8px',
  borderRadius: 12,
  fontSize: 11,
  fontWeight: 500,
  backgroundColor: '#e8f5e9',
  color: '#2e7d32',
};

const chipNegative: React.CSSProperties = {
  padding: '3px 8px',
  borderRadius: 12,
  fontSize: 11,
  fontWeight: 500,
  backgroundColor: '#ffebee',
  color: '#c62828',
};

const chipDefault: React.CSSProperties = {
  padding: '3px 8px',
  borderRadius: 12,
  fontSize: 11,
  fontWeight: 500,
  backgroundColor: '#e0e0e0',
  color: '#333',
};

const cardContentStyle: React.CSSProperties = { marginTop: 8, color: '#333', fontSize: 14, lineHeight: 1.5 };

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

  return (
    <PanelContainer
      title="Interpretability Analysis"
      description="AI-powered interpretability analysis. Provides global and local explanations for model predictions, feature importance, SHAP summaries, material science insights, and risk assessments to support informed decision-making."
      accentColor={pipelineAccent.interpretabilityAnalysis}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          Run Interpretability Analysis
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Analysis
        </Button>
      </Space>

      {error && <ErrorBox message={error} />}

      {/* Show error_message directly when status is failed */}
      {result && result.status === 'failed' && result.error_message && (
        <ErrorBox message={result.error_message} />
      )}

      {result && (
        <>
          {/* Summary bar */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 12 }}>
            <div style={{ fontSize: 14 }}>
              <strong>Status: </strong>
              <StatusBadge label={STATUS_LABELS[result.status] || result.status} color={STATUS_COLORS[result.status] || '#9e9e9e'} />
            </div>
            <div style={{ fontSize: 14 }}>
              <strong>Analysis ID: </strong>
              <code>{result.interpretability_analysis_id}</code>
            </div>
            {result.analysis_profile && (
              <div style={{ fontSize: 14 }}>
                <strong>Profile: </strong>
                <span>{PROFILE_LABELS[result.analysis_profile] || result.analysis_profile}</span>
              </div>
            )}
            {result.ready_for_final_output && (
              <div style={{ fontSize: 14 }}>
                <strong>Ready: </strong>
                <span style={{ color: '#2e7d32', fontWeight: 600 }}>Ready for Final Output</span>
              </div>
            )}
            {result.current_step && (
              <div style={{ fontSize: 14 }}>
                <strong>Current Step: </strong>
                <span style={{ color: '#1976d2' }}>{result.current_step}</span>
              </div>
            )}
            {result.duration_seconds != null && (
              <div style={{ fontSize: 14 }}>
                <strong>Duration: </strong>
                <span>{result.duration_seconds.toFixed(1)}s</span>
              </div>
            )}
          </div>

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <WarningBox warnings={result.warnings} />
          )}

          {/* Tab navigation and content */}
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              { key: 'summary', label: 'Summary', children: <SummaryTab result={result} /> },
              { key: 'materialInsight', label: 'Material Insights', children: <MaterialInsightTab insight={result.material_insight_summary} llmSummary={result.llm_interpretability_summary} /> },
              { key: 'featureImportance', label: 'Feature Importance', children: <FeatureImportanceTab items={result.global_feature_importance} /> },
              { key: 'shap', label: 'SHAP Summary', children: <ShapTab shap={result.shap_summary} /> },
              { key: 'localExplanations', label: 'Local Explanations', children: <LocalExplanationsTab items={result.local_explanations} /> },
              { key: 'highError', label: 'High Error Samples', children: <HighErrorTab items={result.high_error_sample_analysis} /> },
              { key: 'riskNotes', label: 'Risk Notes', children: <RiskNotesTab risks={result.interpretability_risk_notes} warnings={result.warnings} /> },
              { key: 'finalOutputInput', label: 'Final Output Input', children: <FinalOutputInputTab input={result.final_output_input} /> },
              { key: 'debug', label: 'Debug', children: <DebugTab result={result} /> },
              { key: 'json', label: 'Full JSON', children: <Card size="small" title="Full JSON"><JsonViewer data={result} /></Card> },
            ]}
          />
        </>
      )}
    </PanelContainer>
  );
};


/* ---- Summary Tab ---- */

const SummaryField: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => (
  <div style={summaryFieldStyle}>
    <span style={summaryLabelStyle}>{label}</span>
    <span style={summaryValueStyle}>{value || '-'}</span>
  </div>
);

const SummaryTab: React.FC<{ result: InterpretabilityAnalysisResponse }> = ({ result }) => (
  <Card size="small" title="Analysis Summary">
    <div style={grid2Col}>
      <SummaryField label="Analysis ID" value={result.interpretability_analysis_id} />
      <SummaryField label="Final Model" value={result.final_model_id} />
      <SummaryField label="Model Family" value={result.final_model_family} />
      <SummaryField label="Final Trial" value={result.final_trial_id} />
      <SummaryField label="Profile" value={PROFILE_LABELS[result.analysis_profile] || result.analysis_profile} />
      <SummaryField label="Ready for Final Output" value={result.ready_for_final_output ? 'Yes' : 'No'} />
    </div>
    {result.interpretability_methods_used && result.interpretability_methods_used.length > 0 && (
      <Card size="small" style={{ marginTop: 8 }}>
        <strong>Methods Used: </strong>
        {result.interpretability_methods_used.map((m, i) => (
          <Tag key={i} color="geekblue" style={{ marginLeft: i > 0 ? 4 : 0 }}>{METHOD_LABELS[m] || m}</Tag>
        ))}
      </Card>
    )}
  </Card>
);


/* ---- Feature Importance Tab ---- */

const FeatureImportanceTab: React.FC<{ items: GlobalFeatureImportanceItem[] }> = ({ items }) => (
  <div>
    {!items || items.length === 0 ? (
      <EmptyState description="No feature importance data available." />
    ) : (
      <Card size="small" title="Global Feature Importance">
        <div style={{ overflowX: 'auto' }}>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Rank</th>
                <th style={thStyle}>Feature</th>
                <th style={thStyle}>Importance</th>
                <th style={thStyle}>Method</th>
                <th style={thStyle}>Feature Group</th>
                <th style={thStyle}>Hint</th>
              </tr>
            </thead>
            <tbody>
              {items.map((fi, i) => (
                <tr key={i}>
                  <td style={tdStyle}>{fi.importance_rank}</td>
                  <td style={tdStyle}>{fi.feature_name}</td>
                  <td style={tdStyle}>{fi.importance_value.toFixed(6)}</td>
                  <td style={tdStyle}>
                    <Tag color="geekblue">{METHOD_LABELS[fi.importance_method] || fi.importance_method}</Tag>
                  </td>
                  <td style={tdStyle}>{fi.feature_group}</td>
                  <td style={{ ...tdStyle, fontSize: '12px', color: '#666' }}>{fi.interpretation_hint}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    )}
  </div>
);


/* ---- SHAP Tab ---- */

const ShapTab: React.FC<{ shap?: ShapSummary }> = ({ shap }) => (
  <div>
    {!shap ? (
      <EmptyState description="No SHAP summary available." />
    ) : !shap.shap_available ? (
      <Card size="small" title="SHAP Summary">
        <p style={{ color: '#888', fontStyle: 'italic' }}>SHAP was not available for this model.</p>
        {shap.warnings && shap.warnings.length > 0 && (
          <WarningBox warnings={shap.warnings} />
        )}
      </Card>
    ) : (
      <Card size="small" title="SHAP Summary">
        <div style={grid2Col}>
          <SummaryField label="Explainer Type" value={shap.explainer_type} />
          <SummaryField label="Samples Explained" value={String(shap.n_samples_explained)} />
        </div>
        {shap.top_shap_features && shap.top_shap_features.length > 0 && (
          <Card size="small" style={{ marginTop: 8 }} title="Top SHAP Features">
            <table style={{ ...tableStyle, minWidth: 'auto' }}>
              <thead>
                <tr>
                  <th style={thStyle}>Rank</th>
                  <th style={thStyle}>Feature</th>
                  <th style={thStyle}>Mean |SHAP|</th>
                  <th style={thStyle}>Summary</th>
                </tr>
              </thead>
              <tbody>
                {shap.top_shap_features.map((f, i) => (
                  <tr key={i}>
                    <td style={tdStyle}>{f.rank}</td>
                    <td style={tdStyle}>{f.feature_name}</td>
                    <td style={tdStyle}>{f.mean_abs_shap.toFixed(6)}</td>
                    <td style={{ ...tdStyle, wordBreak: 'break-word' }}>{f.direction_summary}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
        {shap.warnings && shap.warnings.length > 0 && (
          <WarningBox warnings={shap.warnings} style={{ marginTop: 12 }} />
        )}
      </Card>
    )}
  </div>
);


/* ---- Local Explanations Tab ---- */

const LocalExplanationsTab: React.FC<{ items: LocalExplanationItem[] }> = ({ items }) => (
  <div>
    <Alert
      type="info"
      showIcon
      message="Per-sample prediction explanations using SHAP values. Shows up to 10 representative samples with their top positive and negative feature contributions. Green chips indicate features that pushed the prediction higher; red chips indicate features that pushed it lower."
      style={{ marginBottom: 16 }}
    />
    {!items || items.length === 0 ? (
      <EmptyState description="No local explanations available." />
    ) : (
      <div>
        {items.map((item, i) => (
          <Card
            key={i}
            size="small"
            style={{ marginBottom: 12 }}
            title={
              <span>
                <span>Sample {item.sample_id}</span>
                {item.y_true != null && <span> &mdash; True: {item.y_true}</span>}
                {item.y_pred != null && <span> &mdash; Pred: {item.y_pred.toFixed(4)}</span>}
                {item.prediction_error != null && (
                  <span style={{ color: item.prediction_error > 0.5 ? '#f44336' : '#4caf50' }}>
                    {' '}&mdash; Error: {item.prediction_error.toFixed(4)}
                  </span>
                )}
              </span>
            }
          >
            {item.top_positive_features && item.top_positive_features.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', marginTop: 8 }}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top positive: </span>
                {item.top_positive_features.map((f, j) => (
                  <span key={j} style={chipPositive}>
                    {f.feature} (+{f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            {item.top_negative_features && item.top_negative_features.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', marginTop: 8 }}>
                <span style={{ fontSize: '12px', color: '#888' }}>Top negative: </span>
                {item.top_negative_features.map((f, j) => (
                  <span key={j} style={chipNegative}>
                    {f.feature} ({f.contribution.toFixed(4)})
                  </span>
                ))}
              </div>
            )}
            <p style={cardContentStyle}>{item.local_explanation_summary}</p>
          </Card>
        ))}
      </div>
    )}
  </div>
);


/* ---- High Error Tab ---- */

const HighErrorTab: React.FC<{ items: HighErrorSampleAnalysis[] }> = ({ items }) => (
  <div>
    {!items || items.length === 0 ? (
      <EmptyState description="No high-error sample analysis available." />
    ) : (
      <div>
        {items.map((item, i) => (
          <Card
            key={i}
            size="small"
            style={{ marginBottom: 12 }}
            title={
              <span>
                Rank #{item.error_rank}: Sample {item.sample_id}
                <span style={{ color: '#f44336', marginLeft: 8, fontSize: 13, fontWeight: 400 }}>
                  Abs Error: {item.absolute_error.toFixed(4)}
                  {item.relative_error != null && ` (${(item.relative_error * 100).toFixed(1)}%)`}
                </span>
              </span>
            }
          >
            <Card size="small" style={{ marginBottom: 8 }}>
              <strong>Possible Error Factors:</strong>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {item.possible_error_factors.map((f, j) => (
                  <li key={j}>{f}</li>
                ))}
              </ul>
            </Card>
            <p style={cardContentStyle}>{item.feature_pattern_summary}</p>
            <p style={{ fontSize: 13, color: '#1976d2', fontStyle: 'italic', margin: '4px 0 0 0' }}>
              {item.review_suggestion}
            </p>
          </Card>
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
  const academicInsights = insight?.academic_insights || llmSummary?.academic_insights || [];
  const groups = insight?.feature_groups_interpretation || llmSummary?.feature_groups_interpretation || [];
  const hypotheses = insight?.domain_hypotheses || llmSummary?.domain_hypotheses || [];
  const limitations = insight?.limitations || llmSummary?.limitations || [];
  const humanReviewNotes = insight?.human_review_notes || llmSummary?.human_review_notes || [];
  const confidence = insight?.confidence_level || llmSummary?.confidence_level || '';

  return (
    <div>
      <Alert
        type="warning"
        showIcon
        message="Important: These insights are model-based interpretations, not causal conclusions."
        style={{ marginBottom: 16 }}
      />

      {confidence && (
        <Card size="small" style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 14 }}>
            <strong>Interpretation Confidence: </strong>
            <StatusBadge label={confidence} color={CONFIDENCE_COLORS[confidence] || '#9e9e9e'} />
          </div>
        </Card>
      )}

      {patterns.length === 0 && academicInsights.length === 0 && hypotheses.length === 0 ? (
        <EmptyState description="No material insights available (AI summary may have failed or was not requested)." />
      ) : (
        <div>
          {academicInsights.length > 0 && (
            <Card size="small" title={`Academic Insights (${academicInsights.length})`} style={{ marginBottom: 12 }}>
              {academicInsights.map((insightItem: AcademicInsight, i: number) => (
                <Card key={insightItem.claim_id || i} size="small" style={{ marginBottom: 8 }}>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
                    <Tag color="blue">{insightItem.claim_type}</Tag>
                    <Tag color={EVIDENCE_COLORS[insightItem.evidence_strength] || 'default'}>
                      {insightItem.evidence_strength}
                    </Tag>
                    <Tag>{insightItem.validation_status}</Tag>
                    <Tag>{insightItem.confidence}</Tag>
                  </div>
                  <p style={{ fontWeight: 600, margin: '0 0 6px 0' }}>{insightItem.claim}</p>
                  {insightItem.material_meaning && (
                    <p style={{ fontSize: 13, color: '#555', margin: '4px 0' }}>{insightItem.material_meaning}</p>
                  )}
                  {insightItem.supporting_evidence_ids?.length > 0 && (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', marginTop: 8 }}>
                      <span style={{ fontSize: 12, color: '#888' }}>Evidence IDs: </span>
                      {insightItem.supporting_evidence_ids.slice(0, 6).map((id) => (
                        <span key={id} style={chipDefault}>{id}</span>
                      ))}
                    </div>
                  )}
                  {insightItem.falsifiable_prediction && (
                    <p style={{ fontSize: 12, color: '#1976d2', margin: '8px 0 0 0' }}>
                      <strong>Falsifiable prediction:</strong> {insightItem.falsifiable_prediction}
                    </p>
                  )}
                  {insightItem.counterexamples_or_risks && insightItem.counterexamples_or_risks.length > 0 && (
                    <p style={{ fontSize: 12, color: '#f57c00', margin: '6px 0 0 0' }}>
                      <strong>Risks:</strong> {insightItem.counterexamples_or_risks.slice(0, 2).join('; ')}
                    </p>
                  )}
                </Card>
              ))}
            </Card>
          )}
          {hypotheses.length > 0 && (
            <Card size="small" title="Domain Hypotheses" style={{ marginBottom: 12 }}>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {hypotheses.map((h, i) => (
                  <li key={i} style={{ marginBottom: 6, fontSize: 14, lineHeight: 1.5 }}>{h}</li>
                ))}
              </ul>
            </Card>
          )}

          {groups.length > 0 && (
            <Card size="small" title="Feature Groups Interpretation" style={{ marginBottom: 12 }}>
              {groups.map((g: { feature_group: string; summary: string }, i: number) => (
                <Card key={i} size="small" style={{ marginBottom: 8 }}>
                  <strong>{g.feature_group}:</strong>
                  <span style={{ marginLeft: 8, fontSize: 14 }}>{g.summary}</span>
                </Card>
              ))}
            </Card>
          )}

          {limitations.length > 0 && (
            <Card size="small" title="Limitations" style={{ marginBottom: 12 }}>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {limitations.map((l, i) => (
                  <li key={i} style={{ marginBottom: 6, color: '#f57c00' }}>{l}</li>
                ))}
              </ul>
            </Card>
          )}

          {humanReviewNotes.length > 0 && (
            <Card size="small" title="Human Review Notes" style={{ marginBottom: 12 }}>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {humanReviewNotes.map((n, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>{n}</li>
                ))}
              </ul>
            </Card>
          )}
          {patterns.length > 0 && (
            <Collapse
              size="small"
              style={{ marginBottom: 12 }}
              items={[
                {
                  key: 'supporting-model-derived-rules',
                  label: `Supporting Model-Derived Rules (${patterns.length})`,
                  children: (
                    <div>
                      {patterns.map((p: MaterialPattern, i: number) => (
                        <Card key={i} size="small" style={{ marginBottom: 8 }}>
                          <p style={{ fontWeight: 600, margin: '0 0 4px 0' }}>{p.pattern}</p>
                          <p style={{ fontSize: 13, color: '#555', margin: '4px 0' }}>{p.possible_material_meaning}</p>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, alignItems: 'center', marginTop: 8 }}>
                            <span style={{ fontSize: 12, color: '#888' }}>Supporting features: </span>
                            {p.supporting_features.map((f, j) => (
                              <span key={j} style={chipDefault}>{f}</span>
                            ))}
                          </div>
                          <div style={{ marginTop: 8, fontSize: 12 }}>
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
                          <p style={{ fontSize: 11, color: '#f57c00', fontStyle: 'italic', margin: '4px 0 0 0' }}>
                            {p.caution}
                          </p>
                        </Card>
                      ))}
                    </div>
                  ),
                },
              ]}
            />
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
      <Card size="small" title={`Risk Notes (${risks.length})`}>
        {risks.map((r, i) => (
          <Card key={i} size="small" style={{ marginBottom: 8 }}>
            <span style={{ fontWeight: 600 }}>{r.risk_type || 'Unknown Risk'}</span>
            {r.severity && (
              <StatusBadge
                label={r.severity}
                color={r.severity === 'high' ? '#f44336' : r.severity === 'medium' ? '#ff9800' : '#4caf50'}
              />
            )}
            <p style={{ fontSize: 13, marginTop: 8 }}>{r.description || '-'}</p>
          </Card>
        ))}
      </Card>
    ) : (
      <EmptyState description="No specific risk notes." />
    )}
    {warnings && warnings.length > 0 && (
      <WarningBox warnings={warnings} style={{ marginTop: 12 }} />
    )}
  </div>
);


/* ---- Final Output Input Tab ---- */

const FinalOutputInputTab: React.FC<{ input?: import('../types').FinalOutputInput }> = ({ input }) => (
  <div>
    {!input ? (
      <EmptyState description="No final output input available." />
    ) : (
      <Card size="small" title="Final Output Input">
        <div style={{ fontSize: 14 }}>
          <strong>Ready for Final Output: </strong>
          <span style={{
            color: input.ready_for_final_output ? '#2e7d32' : '#c62828',
            fontWeight: 600,
          }}>
            {input.ready_for_final_output ? 'Yes' : 'No'}
          </span>
        </div>
        <div style={{ ...grid2Col, marginTop: 12 }}>
          <SummaryField label="Interpretability Analysis" value={input.interpretability_analysis_id} />
          <SummaryField label="Final Model" value={input.final_model_id} />
          <SummaryField label="Final Trial" value={input.final_trial_id} />
          <SummaryField label="Model Artifact" value={input.model_artifact_path} />
        </div>
        {input.global_feature_importance && input.global_feature_importance.length > 0 && (
          <Card size="small" style={{ marginTop: 8 }}>
            <strong>Global Feature Importance: </strong>
            <span>{input.global_feature_importance.length} features included</span>
          </Card>
        )}
        {input.shap_summary && (
          <Card size="small" style={{ marginTop: 8 }}>
            <strong>SHAP Summary: </strong>
            <span>Included</span>
          </Card>
        )}
        {input.material_insight_summary && (
          <Card size="small" style={{ marginTop: 8 }}>
            <strong>Material Insight Summary: </strong>
            <span>Included</span>
          </Card>
        )}
      </Card>
    )}
  </div>
);


/* ---- Debug Tab ---- */

const DebugTab: React.FC<{ result: InterpretabilityAnalysisResponse }> = ({ result }) => {
  const trace = result.debug_trace;
  const debugWarnings = result.debug_warnings ?? [];
  const stepLabelStyle: React.CSSProperties = {
    display: 'inline-block',
    minWidth: 200,
    fontFamily: 'monospace',
    fontSize: 12,
  };
  const statusChip = (status: string) => {
    const colors: Record<string, string> = {
      completed: '#4caf50',
      running: '#2196f3',
      failed: '#f44336',
      pending: '#9e9e9e',
    };
    return (
      <span style={{
        display: 'inline-block',
        width: 10,
        height: 10,
        borderRadius: '50%',
        backgroundColor: colors[status] || '#999',
        marginRight: 4,
      }} />
    );
  };

  return (
    <div>
      {/* Overview card */}
      <Card size="small" title="Debug Overview" style={{ marginBottom: 12 }}>
        <div style={{ ...grid2Col, marginBottom: 8 }}>
          <SummaryField label="Run ID" value={trace?.run_id || result.interpretability_analysis_id} />
          <SummaryField label="Current Step" value={result.current_step || '-'} />
          <SummaryField label="Last Completed" value={result.last_completed_step || '-'} />
          <SummaryField label="Duration" value={result.duration_seconds != null ? `${result.duration_seconds.toFixed(1)}s` : '-'} />
          <SummaryField label="Started" value={result.started_at ? new Date(result.started_at).toLocaleString() : '-'} />
          <SummaryField label="Finished" value={result.finished_at ? new Date(result.finished_at).toLocaleString() : '-'} />
          {trace?.cache_hit && (
            <SummaryField label="Cache Hit" value={`Yes (from ${trace.cached_from_ia_id})`} />
          )}
        </div>
      </Card>

      {/* Step timeline */}
      {trace && trace.steps && trace.steps.length > 0 && (
        <Card size="small" title={`Step Timeline (${trace.steps.length} steps)`} style={{ marginBottom: 12 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={{ ...thStyle, width: 40 }}></th>
                  <th style={thStyle}>Step</th>
                  <th style={thStyle}>Name</th>
                  <th style={thStyle}>Duration</th>
                  <th style={thStyle}>Output</th>
                </tr>
              </thead>
              <tbody>
                {trace.steps.map((s, i) => (
                  <tr key={i} style={{
                    backgroundColor: s.status === 'failed' && !s.recoverable ? '#fff5f5' :
                                     s.status === 'failed' ? '#fffde7' : 'transparent',
                  }}>
                    <td style={tdStyle}>{statusChip(s.status)}</td>
                    <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: 11 }}>{s.step}</td>
                    <td style={tdStyle}>{s.step_name}</td>
                    <td style={tdStyle}>{s.duration_seconds != null ? `${s.duration_seconds.toFixed(2)}s` : '-'}</td>
                    <td style={{ ...tdStyle, fontSize: 11, maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {s.output_summary ? JSON.stringify(s.output_summary).slice(0, 120) : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Failed steps detail */}
      {trace && trace.steps.filter(s => s.status === 'failed').length > 0 && (
        <Card size="small" title="Failed Steps" style={{ marginBottom: 12 }}>
          {trace.steps.filter(s => s.status === 'failed').map((s, i) => (
            <Card key={i} size="small" style={{ marginBottom: 8, borderLeft: '3px solid #f44336' }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>
                {s.step}: {s.step_name}
                {s.recoverable && <Tag color="orange" style={{ marginLeft: 8 }}>recoverable</Tag>}
                {!s.recoverable && <Tag color="red" style={{ marginLeft: 8 }}>FATAL</Tag>}
              </div>
              {s.error_type && (
                <div style={{ fontSize: 13, marginBottom: 4 }}>
                  <strong>Error type: </strong>
                  <code>{s.error_type}</code>
                </div>
              )}
              {s.error_message && (
                <div style={{ fontSize: 13, color: '#c62828', marginBottom: 4 }}>
                  {s.error_message}
                </div>
              )}
              {s.error_traceback && (
                <details style={{ marginTop: 8 }}>
                  <summary style={{ cursor: 'pointer', fontSize: 12, color: '#888' }}>Traceback</summary>
                  <pre style={{
                    fontSize: 10,
                    backgroundColor: '#f5f5f5',
                    padding: 8,
                    borderRadius: 4,
                    maxHeight: 300,
                    overflow: 'auto',
                    marginTop: 4,
                  }}>
                    {s.error_traceback}
                  </pre>
                </details>
              )}
            </Card>
          ))}
        </Card>
      )}

      {/* Structured warnings */}
      {debugWarnings.length > 0 && (
        <Card size="small" title={`Structured Warnings (${debugWarnings.length})`} style={{ marginBottom: 12 }}>
          <div style={{ overflowX: 'auto' }}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Step</th>
                  <th style={thStyle}>Code</th>
                  <th style={thStyle}>Severity</th>
                  <th style={thStyle}>Message</th>
                </tr>
              </thead>
              <tbody>
                {debugWarnings.map((w, i) => (
                  <tr key={i}>
                    <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: 11 }}>{w.step}</td>
                    <td style={{ ...tdStyle, fontFamily: 'monospace', fontSize: 11 }}>{w.code}</td>
                    <td style={tdStyle}>
                      <Tag color={w.severity === 'error' ? 'red' : 'orange'}>{w.severity}</Tag>
                    </td>
                    <td style={{ ...tdStyle, fontSize: 12, wordBreak: 'break-word' }}>{w.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Environment info */}
      {trace && trace.environment && Object.keys(trace.environment).length > 0 && (
        <Card size="small" title="Run Environment">
          <pre style={{ fontSize: 11, backgroundColor: '#f5f5f5', padding: 8, borderRadius: 4, overflow: 'auto' }}>
            {JSON.stringify(trace.environment, null, 2)}
          </pre>
        </Card>
      )}

      {!trace && (
        <EmptyState description="No debug trace available for this run." />
      )}
    </div>
  );
};


export default InterpretabilityAnalysisPanel;



