import React, { useState } from 'react';
import {
  createFinalOutput,
  rerunFinalOutput,
} from '../../../api/finalOutputApi';
import { FinalOutputResponse } from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
  PROFILE_LABELS,
  CONFIDENCE_COLORS,
  PACKAGE_STATUS_LABELS,
  PACKAGE_STATUS_COLORS,
} from '../constants';

interface FinalOutputPanelProps {
  taskId: string;
}

const FinalOutputPanel: React.FC<FinalOutputPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FinalOutputResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('summary');

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFinalOutput(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to generate final output.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFinalOutput(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-generate final output.');
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { key: 'summary', label: 'Output Summary' },
    { key: 'model', label: 'Final Model' },
    { key: 'metric', label: 'Final Metrics' },
    { key: 'report', label: 'Final Report' },
    { key: 'interpretability', label: 'Interpretability' },
    { key: 'workflow', label: 'Workflow Trace' },
    { key: 'reproducibility', label: 'Reproducibility' },
    { key: 'artifacts', label: 'Artifact Manifest' },
    { key: 'downloads', label: 'Download Links' },
    { key: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>
        <span role="img" aria-label="package">Final Output</span>
      </h2>

      <div style={styles.actions}>
        <button
          onClick={handleGenerate}
          disabled={loading || !taskId}
          style={{
            ...styles.button,
            ...styles.primaryBtn,
            ...(loading || !taskId ? styles.disabledBtn : {}),
          }}
        >
          {loading ? 'Generating...' : 'Generate Final Output'}
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
          Re-generate Output
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
            {result.final_output_id && (
              <span style={styles.idText}>ID: {result.final_output_id}</span>
            )}
            {result.report_profile && (
              <span style={styles.profileTag}>
                {PROFILE_LABELS[result.report_profile] || result.report_profile}
              </span>
            )}
            {result.ready_for_delivery ? (
              <span style={{ ...styles.readyBadge, backgroundColor: '#4caf50' }}>
                Ready for Delivery
              </span>
            ) : (
              <span style={{ ...styles.readyBadge, backgroundColor: '#f44336' }}>
                Not Ready
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
            {activeTab === 'model' && <ModelTab summary={result.final_model_summary} />}
            {activeTab === 'metric' && <MetricTab summary={result.final_metric_summary} />}
            {activeTab === 'report' && <ReportTab report={result.final_report} llmReport={result.llm_report_summary} />}
            {activeTab === 'interpretability' && <InterpretabilityTab summary={result.interpretability_summary} />}
            {activeTab === 'workflow' && <WorkflowTraceTab trace={result.workflow_trace_summary} />}
            {activeTab === 'reproducibility' && <ReproducibilityTab summary={result.reproducibility_summary} />}
            {activeTab === 'artifacts' && <ArtifactManifestTab manifest={result.final_artifact_manifest} />}
            {activeTab === 'downloads' && <DownloadLinksTab links={result.download_links} />}
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

          {/* Error message */}
          {result.error_message && (
            <div style={styles.errorBox}>
              <strong>Error:</strong> {result.error_message}
            </div>
          )}
        </div>
      )}
    </div>
  );
};


/* ---- Summary Tab ---- */

const SummaryTab: React.FC<{ result: FinalOutputResponse }> = ({ result }) => (
  <div style={styles.tabPanel}>
    <div style={styles.summaryGrid}>
      <Field label="Final Output ID" value={result.final_output_id} />
      <Field label="Task ID" value={result.task_id} />
      <Field label="Status" value={STATUS_LABELS[result.status] || result.status} />
      <Field label="Report Profile" value={PROFILE_LABELS[result.report_profile] || result.report_profile} />
      <Field label="Ready for Delivery" value={result.ready_for_delivery ? 'Yes' : 'No'} />
      <Field label="Interpretability Analysis" value={result.interpretability_analysis_id} />
      <Field label="Final Pipeline Selection" value={result.final_pipeline_selection_id} />
      {result.created_at && <Field label="Generated At" value={new Date(result.created_at).toLocaleString()} />}
    </div>
    {result.final_model_summary && (
      <div style={styles.subSection}>
        <h4>Model Quick View</h4>
        <p style={{ fontSize: '14px' }}>
          Model: <strong>{(result.final_model_summary as any).final_model_id || '-'}</strong>
          {((result.final_model_summary as any).final_trial_id) && (
            <> | Trial: <strong>{(result.final_model_summary as any).final_trial_id}</strong></>
          )}
        </p>
      </div>
    )}
    {result.final_metric_summary && (
      <div style={styles.subSection}>
        <h4>Metric Quick View</h4>
        <p style={{ fontSize: '14px' }}>
          {(result.final_metric_summary as any).primary_metric}:{' '}
          <strong>{(result.final_metric_summary as any).primary_metric_value ?? '-'}</strong>
        </p>
      </div>
    )}
  </div>
);


/* ---- Model Tab ---- */

const ModelTab: React.FC<{ summary?: Record<string, unknown> }> = ({ summary }) => (
  <div style={styles.tabPanel}>
    {!summary ? (
      <p>No model summary available.</p>
    ) : (
      <div style={styles.summaryGrid}>
        <Field label="Model ID" value={summary.final_model_id as string} />
        <Field label="Model Family" value={summary.final_model_family as string} />
        <Field label="Trial ID" value={summary.final_trial_id as string} />
        <Field label="Pipeline Spec ID" value={summary.final_pipeline_spec_id as string} />
        <Field label="Artifact Path" value={summary.model_artifact_path as string} />
        <Field label="Selection Reason" value={summary.selection_reason_summary as string} />
      </div>
    )}
  </div>
);


/* ---- Metric Tab ---- */

const MetricTab: React.FC<{ summary?: Record<string, unknown> }> = ({ summary }) => (
  <div style={styles.tabPanel}>
    {!summary ? (
      <p>No metric summary available.</p>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <Field label="Primary Metric" value={summary.primary_metric as string} />
          <Field label="Value" value={summary.primary_metric_value != null ? String(summary.primary_metric_value) : '-'} />
          <Field label="Direction" value={summary.metric_direction as string} />
          <Field label="Ranking Position" value={summary.model_ranking_position != null ? `#${summary.model_ranking_position}` : '-'} />
        </div>
        {!!summary.secondary_metrics && Object.keys(summary.secondary_metrics as object).length > 0 && (
          <div style={styles.subSection}>
            <h4>Secondary Metrics</h4>
            <pre style={styles.smallJson}>{JSON.stringify(summary.secondary_metrics, null, 2)}</pre>
          </div>
        )}
        {!!summary.baseline_comparison && Object.keys(summary.baseline_comparison as object).length > 0 && (
          <div style={styles.subSection}>
            <h4>Baseline Comparison</h4>
            <pre style={styles.smallJson}>{JSON.stringify(summary.baseline_comparison, null, 2)}</pre>
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Report Tab ---- */

const ReportTab: React.FC<{
  report?: Record<string, unknown>;
  llmReport?: Record<string, unknown>;
}> = ({ report, llmReport }) => {
  const sections = [
    'executive_summary', 'task_overview', 'dataset_summary', 'workflow_summary',
    'feature_engineering_summary', 'model_search_summary', 'final_model_summary',
    'metric_summary', 'interpretability_summary', 'material_insight_summary',
    'limitations_and_risks', 'reproducibility_notes', 'artifact_summary', 'next_steps',
  ];

  if (!report || Object.keys(report).length === 0) {
    return <div style={styles.tabPanel}><p>No report available.</p></div>;
  }

  return (
    <div style={styles.tabPanel}>
      <h3 style={{ margin: '0 0 12px 0' }}>{(report.title as string) || 'Final Report'}</h3>

      {llmReport && (
        <div style={{
          ...styles.infoBox,
          backgroundColor: (llmReport as any).confidence_level ? '#e3f2fd' : '#fff3e0',
        }}>
          {llmReport ? 'LLM-generated report' : 'System fallback report'}
          {(llmReport as any).confidence_level && (
            <span style={{
              ...styles.confidenceBadge,
              backgroundColor: CONFIDENCE_COLORS[(llmReport as any).confidence_level] || '#999',
              marginLeft: '8px',
            }}>
              {(llmReport as any).confidence_level}
            </span>
          )}
        </div>
      )}

      {sections.map((section) => {
        const content = report[section] as string;
        if (!content) return null;
        const label = section.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
        return (
          <div key={section} style={styles.reportSection}>
            <h4 style={styles.reportHeading}>{label}</h4>
            <p style={styles.reportText}>{content}</p>
          </div>
        );
      })}
    </div>
  );
};


/* ---- Interpretability Tab ---- */

const InterpretabilityTab: React.FC<{ summary?: Record<string, unknown> }> = ({ summary }) => (
  <div style={styles.tabPanel}>
    {!summary ? (
      <p>No interpretability summary available.</p>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <Field label="Analysis ID" value={summary.interpretability_analysis_id as string} />
          <Field label="Methods Used" value={Array.isArray(summary.methods_used) ? (summary.methods_used as string[]).join(', ') : '-'} />
        </div>
        {!!summary.top_features && Array.isArray(summary.top_features) && (summary.top_features as any[]).length > 0 && (
          <div style={styles.subSection}>
            <h4>Top Features</h4>
            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Rank</th>
                    <th style={styles.th}>Feature</th>
                    <th style={styles.th}>Importance</th>
                    <th style={styles.th}>Method</th>
                  </tr>
                </thead>
                <tbody>
                  {(summary.top_features as any[]).map((fi: any, i: number) => (
                    <tr key={i}>
                      <td style={styles.td}>{fi.importance_rank}</td>
                      <td style={styles.td}>{fi.feature_name}</td>
                      <td style={styles.td}>{fi.importance_value?.toFixed?.(6) ?? fi.importance_value}</td>
                      <td style={styles.td}>{fi.importance_method}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {!!summary.shap_summary && (
          <div style={styles.subSection}>
            <h4>SHAP Summary Available</h4>
          </div>
        )}
        {!!summary.material_insight_summary && (
          <div style={styles.subSection}>
            <h4>Material Insight Summary Available</h4>
            <div style={styles.disclaimerBox}>
              These insights are model-based interpretations, not causal conclusions.
            </div>
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Workflow Trace Tab ---- */

const WorkflowTraceTab: React.FC<{ trace?: Record<string, unknown> }> = ({ trace }) => {
  const modules = [
    { key: 'task_specification_id', label: 'Task Specification' },
    { key: 'task_interpretation_id', label: 'Task Interpretation' },
    { key: 'dataset_profile_id', label: 'Dataset Profile' },
    { key: 'workflow_plan_id', label: 'Workflow Plan' },
    { key: 'feature_engineering_id', label: 'Feature Engineering' },
    { key: 'feature_preprocessing_id', label: 'Feature Preprocessing' },
    { key: 'model_search_context_id', label: 'Model Search Context' },
    { key: 'model_search_plan_id', label: 'Model Search Plan' },
    { key: 'pipeline_generation_id', label: 'Pipeline Generation' },
    { key: 'pipeline_execution_id', label: 'Pipeline Execution' },
    { key: 'metric_evaluation_id', label: 'Metric Evaluation' },
    { key: 'result_diagnosis_id', label: 'Result Diagnosis' },
    { key: 'workflow_refinement_id', label: 'Workflow Refinement' },
    { key: 'final_pipeline_selection_id', label: 'Final Pipeline Selection' },
    { key: 'interpretability_analysis_id', label: 'Interpretability Analysis' },
  ];

  return (
    <div style={styles.tabPanel}>
      {!trace ? (
        <p>No workflow trace available.</p>
      ) : (
        <div>
          <div style={styles.summaryGrid}>
            <Field label="Iteration Count" value={String(trace.iteration_count ?? 0)} />
          </div>
          <div style={styles.subSection}>
            <h4>Pipeline Modules</h4>
            <div style={styles.tableWrapper}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>Step</th>
                    <th style={styles.th}>Module</th>
                    <th style={styles.th}>ID</th>
                  </tr>
                </thead>
                <tbody>
                  {modules.map((mod, i) => {
                    const id = trace[mod.key] as string | undefined;
                    return (
                      <tr key={mod.key} style={{ backgroundColor: id ? '#fff' : '#fafafa' }}>
                        <td style={styles.td}>{i + 1}</td>
                        <td style={styles.td}>{mod.label}</td>
                        <td style={{ ...styles.td, fontFamily: id ? 'monospace' : 'inherit', color: id ? '#333' : '#999' }}>
                          {id || '(not traced)'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          {!!trace.workflow_trace_artifacts && Object.keys(trace.workflow_trace_artifacts as object).length > 0 && (
            <div style={styles.subSection}>
              <h4>Module Summaries</h4>
              <pre style={styles.smallJson}>{JSON.stringify(trace.workflow_trace_artifacts, null, 2)}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
};


/* ---- Reproducibility Tab ---- */

const ReproducibilityTab: React.FC<{ summary?: Record<string, unknown> }> = ({ summary }) => (
  <div style={styles.tabPanel}>
    {!summary ? (
      <p>No reproducibility summary available.</p>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <Field label="Dataset Source" value={summary.dataset_source as string} />
          <Field label="Target Column" value={summary.target_column as string} />
          <Field label="Feature Count" value={summary.feature_columns_count != null ? String(summary.feature_columns_count) : '-'} />
          <Field label="Model Artifact" value={summary.model_artifact_path as string} />
          <Field label="Random State" value={summary.random_state != null ? String(summary.random_state) : '-'} />
        </div>
        {!!summary.environment_summary && Object.keys(summary.environment_summary as object).length > 0 && (
          <div style={styles.subSection}>
            <h4>Environment</h4>
            <pre style={styles.smallJson}>{JSON.stringify(summary.environment_summary, null, 2)}</pre>
          </div>
        )}
        {!!summary.prediction_artifact_paths && Array.isArray(summary.prediction_artifact_paths) && (
          <div style={styles.subSection}>
            <h4>Prediction Artifacts ({(summary.prediction_artifact_paths as string[]).length})</h4>
            {(summary.prediction_artifact_paths as string[]).map((p, i) => (
              <div key={i} style={styles.pathItem}>{p}</div>
            ))}
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Artifact Manifest Tab ---- */

const ArtifactManifestTab: React.FC<{ manifest?: Record<string, unknown> }> = ({ manifest }) => (
  <div style={styles.tabPanel}>
    {!manifest ? (
      <p>No artifact manifest available.</p>
    ) : (
      <div>
        <div style={{
          ...styles.statusBadge,
          backgroundColor: PACKAGE_STATUS_COLORS[manifest.artifact_integrity_status as string] || '#999',
          display: 'inline-block',
          marginBottom: '12px',
        }}>
          {PACKAGE_STATUS_LABELS[manifest.artifact_integrity_status as string] || manifest.artifact_integrity_status as string}
        </div>
        <div style={styles.summaryGrid}>
          <Field label="Model Artifact" value={manifest.model_artifact_path as string} />
          <Field label="JSON Report" value={manifest.final_report_json_path as string} />
          <Field label="Markdown Report" value={manifest.final_report_md_path as string} />
          <Field label="Workflow Trace" value={manifest.workflow_trace_path as string} />
          <Field label="Reproducibility Summary" value={manifest.reproducibility_summary_path as string} />
          <Field label="Manifest" value={manifest.manifest_path as string} />
        </div>
        {!!manifest.prediction_artifact_paths && Array.isArray(manifest.prediction_artifact_paths) && (manifest.prediction_artifact_paths as string[]).length > 0 && (
          <div style={styles.subSection}>
            <h4>Prediction Artifacts</h4>
            {(manifest.prediction_artifact_paths as string[]).map((p, i) => (
              <div key={i} style={styles.pathItem}>{p}</div>
            ))}
          </div>
        )}
        {!!manifest.missing_artifacts && Array.isArray(manifest.missing_artifacts) && (manifest.missing_artifacts as string[]).length > 0 && (
          <div style={styles.warningsBox}>
            <strong>Missing Artifacts:</strong>
            <ul style={styles.warningList}>
              {(manifest.missing_artifacts as string[]).map((m, i) => (
                <li key={i}>{m}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    )}
  </div>
);


/* ---- Download Links Tab ---- */

const DownloadLinksTab: React.FC<{ links?: Record<string, unknown> }> = ({ links }) => (
  <div style={styles.tabPanel}>
    {!links ? (
      <p>No download links available.</p>
    ) : (
      <div>
        <div style={styles.summaryGrid}>
          <Field label="JSON Report" value={links.json_report as string} />
          <Field label="Markdown Report" value={links.markdown_report as string} />
          <Field label="Manifest" value={links.manifest as string} />
          <Field label="Workflow Trace" value={links.workflow_trace as string} />
          <Field label="Reproducibility Summary" value={links.reproducibility_summary as string} />
          <Field label="Output Package Dir" value={links.output_package_dir as string} />
          <Field label="Model Artifact Ref" value={links.model_artifact_ref as string} />
        </div>
        {!!links.prediction_artifact_refs && Array.isArray(links.prediction_artifact_refs) && (links.prediction_artifact_refs as string[]).length > 0 && (
          <div style={styles.subSection}>
            <h4>Prediction Artifact Refs</h4>
            {(links.prediction_artifact_refs as string[]).map((p, i) => (
              <div key={i} style={styles.pathItem}>{p}</div>
            ))}
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


/* ---- Shared Components ---- */

const Field: React.FC<{ label: string; value?: string | null }> = ({ label, value }) => (
  <div style={styles.summaryField}>
    <span style={styles.summaryLabel}>{label}</span>
    <span style={styles.summaryValue}>{value || '-'}</span>
  </div>
);


/* ---- Styles ---- */

const styles: Record<string, React.CSSProperties> = {
  container: {
    border: '1px solid #4caf50',
    borderRadius: '8px',
    padding: '20px',
    marginTop: '16px',
    backgroundColor: '#f1f8e9',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '20px',
    fontWeight: 600,
    color: '#2e7d32',
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
    backgroundColor: '#2e7d32',
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
    backgroundColor: '#e8f5e9',
    color: '#2e7d32',
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
  reportSection: {
    marginBottom: '20px',
    padding: '12px',
    backgroundColor: '#fafafa',
    borderRadius: '6px',
    border: '1px solid #eee',
  },
  reportHeading: {
    margin: '0 0 8px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#555',
    textTransform: 'capitalize',
  },
  reportText: {
    fontSize: '14px',
    lineHeight: 1.6,
    color: '#333',
    margin: 0,
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
  pathItem: {
    fontFamily: 'monospace',
    fontSize: '12px',
    color: '#555',
    padding: '4px 0',
    wordBreak: 'break-all',
  },
  infoBox: {
    padding: '10px 14px',
    borderRadius: '6px',
    fontSize: '13px',
    marginBottom: '16px',
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
  confidenceBadge: {
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '10px',
    fontSize: '12px',
    fontWeight: 500,
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
  smallJson: {
    backgroundColor: '#f5f5f5',
    padding: '10px',
    borderRadius: '4px',
    fontSize: '12px',
    overflowX: 'auto',
    maxHeight: '300px',
    overflowY: 'auto',
    fontFamily: 'monospace',
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

export default FinalOutputPanel;
