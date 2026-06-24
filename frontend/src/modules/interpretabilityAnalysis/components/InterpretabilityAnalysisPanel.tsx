import React, { useState } from 'react';
import { Button, Space, Tabs, Card, Tag, Alert } from 'antd';
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
              { key: 'featureImportance', label: 'Feature Importance', children: <FeatureImportanceTab items={result.global_feature_importance} /> },
              { key: 'shap', label: 'SHAP Summary', children: <ShapTab shap={result.shap_summary} /> },
              { key: 'localExplanations', label: 'Local Explanations', children: <LocalExplanationsTab items={result.local_explanations} /> },
              { key: 'highError', label: 'High Error Samples', children: <HighErrorTab items={result.high_error_sample_analysis} /> },
              { key: 'materialInsight', label: 'Material Insights', children: <MaterialInsightTab insight={result.material_insight_summary} llmSummary={result.llm_interpretability_summary} /> },
              { key: 'riskNotes', label: 'Risk Notes', children: <RiskNotesTab risks={result.interpretability_risk_notes} warnings={result.warnings} /> },
              { key: 'finalOutputInput', label: 'Final Output Input', children: <FinalOutputInputTab input={result.final_output_input} /> },
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
  const groups = insight?.feature_groups_interpretation || llmSummary?.feature_groups_interpretation || [];
  const hypotheses = insight?.domain_hypotheses || llmSummary?.domain_hypotheses || [];
  const limitations = insight?.limitations || llmSummary?.limitations || [];
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

      {patterns.length === 0 && hypotheses.length === 0 ? (
        <EmptyState description="No material insights available (AI summary may have failed or was not requested)." />
      ) : (
        <div>
          {patterns.length > 0 && (
            <Card size="small" title={`Top Material Patterns (${patterns.length})`} style={{ marginBottom: 12 }}>
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

          {llmSummary?.human_review_notes && llmSummary.human_review_notes.length > 0 && (
            <Card size="small" title="Human Review Notes" style={{ marginBottom: 12 }}>
              <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
                {llmSummary.human_review_notes.map((n, i) => (
                  <li key={i} style={{ marginBottom: 6 }}>{n}</li>
                ))}
              </ul>
            </Card>
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


export default InterpretabilityAnalysisPanel;
