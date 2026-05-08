import React, { useState } from 'react';
import {
  createFinalPipelineSelection,
  rerunFinalPipelineSelection,
} from '../../../api/finalPipelineSelectionApi';
import {
  FinalPipelineSelectionResponse,
  CandidateSelectionItem,
  SystemSelectionReason,
  LLMSelectionExplanation,
  CandidateDifferenceSummary,
  FinalArtifactManifest,
  InterpretabilityAnalysisInput,
} from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  CANDIDATE_STATUS_COLORS,
  CANDIDATE_STATUS_LABELS,
  PROFILE_LABELS,
  CONFIDENCE_COLORS,
  INTEGRITY_COLORS,
} from '../constants';

interface FinalPipelineSelectionPanelProps {
  taskId: string;
}

const FinalPipelineSelectionPanel: React.FC<FinalPipelineSelectionPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FinalPipelineSelectionResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFinalPipelineSelection(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run final pipeline selection.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFinalPipelineSelection(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run final pipeline selection.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { key: 'summary', label: 'Summary' },
    { key: 'ranking', label: 'Candidate Ranking' },
    { key: 'systemReason', label: 'System Reason' },
    { key: 'llmExplanation', label: 'LLM Explanation' },
    { key: 'differences', label: 'Candidate Differences' },
    { key: 'reviewNotes', label: 'Review Notes' },
    { key: 'riskNotes', label: 'Risk Notes' },
    { key: 'constraints', label: 'Constraints' },
    { key: 'artifacts', label: 'Artifact Manifest' },
    { key: 'interpretability', label: 'Interpretability Input' },
    { key: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Final Pipeline Selection</h2>

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
          {loading ? 'Selecting...' : 'Run Final Selection'}
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
          Re-run Selection
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
            {result.final_pipeline_selection_id && (
              <span style={styles.idText}>ID: {result.final_pipeline_selection_id}</span>
            )}
            {result.selection_profile && (
              <span style={styles.profileTag}>
                Profile: {PROFILE_LABELS[result.selection_profile] || result.selection_profile}
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
            {activeTab === 'ranking' && <RankingTab result={result} />}
            {activeTab === 'systemReason' && <SystemReasonTab reason={result.system_selection_reason} />}
            {activeTab === 'llmExplanation' && <LLMExplanationTab explanation={result.llm_selection_explanation} llmUsed={result.llm_used} confidence={result.llm_confidence_level} />}
            {activeTab === 'differences' && <DifferencesTab summaries={result.candidate_difference_summary} />}
            {activeTab === 'reviewNotes' && <ReviewNotesTab notes={result.human_review_notes} />}
            {activeTab === 'riskNotes' && <RiskNotesTab notes={result.risk_notes} />}
            {activeTab === 'constraints' && <ConstraintsTab constraintResult={result.constraint_check_result} />}
            {activeTab === 'artifacts' && <ArtifactsTab manifest={result.final_artifact_manifest} />}
            {activeTab === 'interpretability' && <InterpretabilityTab input={result.interpretability_analysis_input} ready={result.ready_for_interpretability_analysis} />}
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


/* ---- Tab Content Components ---- */

const SummaryTab: React.FC<{ result: FinalPipelineSelectionResponse }> = ({ result }) => (
  <div style={styles.tabPanel}>
    <div style={styles.summaryGrid}>
      <SummaryField label="Final Model" value={result.final_model_id} />
      <SummaryField label="Model Family" value={result.final_model_family} />
      <SummaryField label="Final Trial" value={result.final_trial_id} />
      <SummaryField label="Trial Type" value={result.final_trial_type} />
      <SummaryField label="Pipeline Spec" value={result.final_pipeline_spec_id} />
      <SummaryField label="Primary Metric" value={result.primary_metric} />
      <SummaryField label="Metric Value" value={result.primary_metric_value != null ? String(result.primary_metric_value) : '-'} />
      <SummaryField label="Metric Direction" value={result.metric_direction} />
      <SummaryField label="Selection Score" value={result.selection_score != null ? result.selection_score.toFixed(4) : '-'} />
      <SummaryField label="LLM Used" value={result.llm_used ? 'Yes' : 'No'} />
      <SummaryField label="LLM Confidence" value={result.llm_confidence_level || '-'} />
      <SummaryField label="Ready for Interpretability" value={result.ready_for_interpretability_analysis ? 'Yes' : 'No'} />
    </div>

    {result.final_hyperparameters && Object.keys(result.final_hyperparameters).length > 0 && (
      <div style={styles.subSection}>
        <h4>Final Hyperparameters</h4>
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Parameter</th>
              <th style={styles.th}>Value</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(result.final_hyperparameters).map(([key, val]) => (
              <tr key={key}>
                <td style={styles.td}>{key}</td>
                <td style={styles.td}>{String(val)}</td>
              </tr>
            ))}
          </tbody>
        </table>
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

const RankingTab: React.FC<{ result: FinalPipelineSelectionResponse }> = ({ result }) => {
  const ranking = result.candidate_ranking || [];
  return (
    <div style={styles.tabPanel}>
      {ranking.length === 0 ? (
        <p>No candidate ranking available.</p>
      ) : (
        <div style={styles.tableWrapper}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>Rank</th>
                <th style={styles.th}>Model</th>
                <th style={styles.th}>Trial</th>
                <th style={styles.th}>Role</th>
                <th style={styles.th}>Metric Value</th>
                <th style={styles.th}>Selection Score</th>
                <th style={styles.th}>Stability</th>
                <th style={styles.th}>Interpret.</th>
                <th style={styles.th}>Cost</th>
                <th style={styles.th}>Status</th>
              </tr>
            </thead>
            <tbody>
              {ranking.map((c, i) => (
                <tr key={i} style={c.is_final_selected ? styles.selectedRow : {}}>
                  <td style={styles.td}>{c.selection_rank ?? '-'}</td>
                  <td style={styles.td}>{c.model_id}</td>
                  <td style={styles.td}>{c.trial_id}</td>
                  <td style={styles.td}>{c.pipeline_role}</td>
                  <td style={styles.td}>{c.primary_metric_value != null ? c.primary_metric_value : '-'}</td>
                  <td style={styles.td}>{c.selection_score.toFixed(4)}</td>
                  <td style={styles.td}>{c.stability_score.toFixed(2)}</td>
                  <td style={styles.td}>{c.interpretability_score.toFixed(2)}</td>
                  <td style={styles.td}>{c.cost_score.toFixed(2)}</td>
                  <td style={styles.td}>
                    <span style={{
                      ...styles.candidateBadge,
                      backgroundColor: CANDIDATE_STATUS_COLORS[c.candidate_status] || '#999',
                    }}>
                      {CANDIDATE_STATUS_LABELS[c.candidate_status] || c.candidate_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const SystemReasonTab: React.FC<{ reason?: SystemSelectionReason }> = ({ reason }) => (
  <div style={styles.tabPanel}>
    {!reason ? (
      <p>No system selection reason available.</p>
    ) : (
      <div>
        <div style={styles.reasonBlock}>
          <h4>Main Reason</h4>
          <p>{reason.main_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Metric Reason</h4>
          <p>{reason.metric_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Stability Reason</h4>
          <p>{reason.stability_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Baseline Reason</h4>
          <p>{reason.baseline_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Interpretability Reason</h4>
          <p>{reason.interpretability_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Cost Reason</h4>
          <p>{reason.cost_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Constraint Reason</h4>
          <p>{reason.constraint_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Artifact Reason</h4>
          <p>{reason.artifact_reason || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Trade-off Summary</h4>
          <p>{reason.tradeoff_summary || '-'}</p>
        </div>
      </div>
    )}
  </div>
);

const LLMExplanationTab: React.FC<{
  explanation?: LLMSelectionExplanation;
  llmUsed: boolean;
  confidence?: string;
}> = ({ explanation, llmUsed, confidence }) => (
  <div style={styles.tabPanel}>
    {!llmUsed && <p style={styles.infoText}>LLM explanation was not requested or not available.</p>}
    {llmUsed && !explanation && <p style={styles.infoText}>LLM explanation failed or was not produced.</p>}
    {confidence && (
      <div style={styles.confidenceBar}>
        <span>LLM Confidence:</span>
        <span style={{ ...styles.confidenceBadge, backgroundColor: CONFIDENCE_COLORS[confidence] || '#999' }}>
          {confidence}
        </span>
      </div>
    )}
    {explanation && (
      <div>
        <div style={styles.reasonBlock}>
          <h4>Why Selected</h4>
          <p>{explanation.why_selected || '-'}</p>
        </div>
        <div style={styles.reasonBlock}>
          <h4>Natural Language Rationale</h4>
          <p>{explanation.selection_rationale_natural_language || '-'}</p>
        </div>
      </div>
    )}
  </div>
);

const DifferencesTab: React.FC<{ summaries: CandidateDifferenceSummary[] }> = ({ summaries }) => (
  <div style={styles.tabPanel}>
    {!summaries || summaries.length === 0 ? (
      <p>No candidate difference summary available.</p>
    ) : (
      <div>
        {summaries.map((s, i) => (
          <div key={i} style={styles.reasonBlock}>
            <h4>{s.candidate || 'Candidate'}</h4>
            <p>{s.summary || '-'}</p>
          </div>
        ))}
      </div>
    )}
  </div>
);

const ReviewNotesTab: React.FC<{ notes: string[] }> = ({ notes }) => (
  <div style={styles.tabPanel}>
    {!notes || notes.length === 0 ? (
      <p>No human review notes available.</p>
    ) : (
      <ul style={styles.noteList}>
        {notes.map((n, i) => (
          <li key={i} style={styles.noteItem}>{n}</li>
        ))}
      </ul>
    )}
  </div>
);

const RiskNotesTab: React.FC<{ notes: string[] }> = ({ notes }) => (
  <div style={styles.tabPanel}>
    {!notes || notes.length === 0 ? (
      <p>No risk notes available.</p>
    ) : (
      <ul style={styles.noteList}>
        {notes.map((n, i) => (
          <li key={i} style={{ ...styles.noteItem, color: '#d32f2f' }}>{n}</li>
        ))}
      </ul>
    )}
  </div>
);

const ConstraintsTab: React.FC<{ constraintResult?: import('../types').ConstraintCheckResult }> = ({ constraintResult }) => (
  <div style={styles.tabPanel}>
    {!constraintResult ? (
      <p>No constraint check result available.</p>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <SummaryField label="Passed" value={constraintResult.passed ? 'Yes' : 'No'} />
          <SummaryField label="Hard Constraints Met" value={constraintResult.hard_constraints_met ? 'Yes' : 'No'} />
          <SummaryField label="Soft Constraints Met" value={constraintResult.soft_constraints_met ? 'Yes' : 'No'} />
        </div>
        {constraintResult.issues.length > 0 && (
          <div style={styles.subSection}>
            <h4>Issues</h4>
            <ul style={styles.noteList}>
              {constraintResult.issues.map((issue, i) => (
                <li key={i} style={{ ...styles.noteItem, color: '#d32f2f' }}>{issue}</li>
              ))}
            </ul>
          </div>
        )}
        {constraintResult.warnings.length > 0 && (
          <div style={styles.subSection}>
            <h4>Warnings</h4>
            <ul style={styles.noteList}>
              {constraintResult.warnings.map((w, i) => (
                <li key={i} style={{ ...styles.noteItem, color: '#f57c00' }}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )}
  </div>
);

const ArtifactsTab: React.FC<{ manifest?: FinalArtifactManifest }> = ({ manifest }) => (
  <div style={styles.tabPanel}>
    {!manifest ? (
      <p>No artifact manifest available.</p>
    ) : (
      <div>
        <div style={styles.integrityBar}>
          <span>Integrity Status:</span>
          <span style={{
            ...styles.integrityBadge,
            backgroundColor: INTEGRITY_COLORS[manifest.artifact_integrity_status] || '#999',
          }}>
            {manifest.artifact_integrity_status}
          </span>
        </div>
        <div style={styles.summaryGrid}>
          <SummaryField label="Model Artifact" value={manifest.model_artifact_path || 'N/A'} />
          <SummaryField label="Preprocessor Artifact" value={manifest.preprocessor_artifact_path || 'N/A'} />
          <SummaryField label="Model Ready Matrix" value={manifest.model_ready_matrix_path || 'N/A'} />
          <SummaryField label="Feature Matrix" value={manifest.feature_matrix_path || 'N/A'} />
          <SummaryField label="Metric Results" value={manifest.metric_results_path || 'N/A'} />
        </div>
        {manifest.prediction_artifact_paths && manifest.prediction_artifact_paths.length > 0 && (
          <div style={styles.subSection}>
            <h4>Prediction Artifacts</h4>
            <ul style={styles.noteList}>
              {manifest.prediction_artifact_paths.map((p, i) => (
                <li key={i} style={styles.noteItem}>{p}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )}
  </div>
);

const InterpretabilityTab: React.FC<{
  input?: InterpretabilityAnalysisInput;
  ready: boolean;
}> = ({ input, ready }) => (
  <div style={styles.tabPanel}>
    <div style={styles.readyBar}>
      <span>Ready for Interpretability Analysis:</span>
      <span style={{
        ...styles.readyBadge,
        backgroundColor: ready ? '#4caf50' : '#f44336',
      }}>
        {ready ? 'Yes' : 'No'}
      </span>
    </div>
    {input ? (
      <div>
        <div style={styles.summaryGrid}>
          <SummaryField label="Task Type" value={input.task_type} />
          <SummaryField label="Target Column" value={input.target_column} />
          <SummaryField label="Model" value={input.final_model_id} />
          <SummaryField label="Model Family" value={input.final_model_family} />
          <SummaryField label="Trial ID" value={input.final_trial_id} />
          <SummaryField label="Model Artifact" value={input.model_artifact_path} />
          <SummaryField label="Preprocessor" value={input.preprocessor_artifact_path} />
          <SummaryField label="Primary Metric" value={input.primary_metric} />
          <SummaryField label="Metric Value" value={input.primary_metric_value != null ? String(input.primary_metric_value) : '-'} />
        </div>
        {input.interpretability_methods_recommended && input.interpretability_methods_recommended.length > 0 && (
          <div style={styles.subSection}>
            <h4>Recommended Methods</h4>
            <div style={styles.tagContainer}>
              {input.interpretability_methods_recommended.map((m, i) => (
                <span key={i} style={styles.methodTag}>{m}</span>
              ))}
            </div>
          </div>
        )}
        {input.feature_columns && input.feature_columns.length > 0 && (
          <div style={styles.subSection}>
            <h4>Feature Columns ({input.feature_columns.length})</h4>
            <p style={styles.infoText}>{input.feature_columns.join(', ')}</p>
          </div>
        )}
      </div>
    ) : (
      <p>No interpretability analysis input available.</p>
    )}
  </div>
);

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
  selectedRow: {
    backgroundColor: '#e8f5e9',
  },
  candidateBadge: {
    color: '#fff',
    padding: '2px 8px',
    borderRadius: '10px',
    fontSize: '11px',
    fontWeight: 500,
  },
  reasonBlock: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#fafafa',
    borderRadius: '6px',
    border: '1px solid #eee',
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
  integrityBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  integrityBadge: {
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '10px',
    fontSize: '12px',
    fontWeight: 500,
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
  jsonBlock: {
    backgroundColor: '#263238',
    color: '#aed581',
    padding: '16px',
    borderRadius: '6px',
    fontSize: '12px',
    overflowX: 'auto',
    maxHeight: '600px',
    overflowY: 'auto',
  },
};

export default FinalPipelineSelectionPanel;
