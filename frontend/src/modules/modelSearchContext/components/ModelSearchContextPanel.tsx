import React, { useState } from 'react';
import {
  createModelSearchContext,
  rerunModelSearchContext,
} from '../../../api/modelSearchContextApi';
import {
  ModelSearchContextResponse,
  StrategyChange,
  StrategyChangeRationale,
  HPOPlan,
  SearchSpacePlan,
  ValidationPlan,
  EvaluationPlan,
  PipelineGenerationInput,
} from '../types';

const BUDGET_COLORS: Record<string, string> = {
  low: '#ff9800',
  moderate: '#1976d2',
  high: '#2e7d32',
};

interface ModelSearchContextPanelProps {
  taskId: string;
  initialResult?: ModelSearchContextResponse;
}

const AREA_LABELS: Record<string, string> = {
  model: 'Model Strategy',
  hpo: 'HPO Strategy',
  validation: 'Validation Strategy',
  evaluation: 'Evaluation Strategy',
};

const FIELD_LABELS: Record<string, string> = {
  candidate_model_families: 'Candidate Models',
  baseline_models: 'Baseline Models',
  preferred_model_bias: 'Model Preference',
  excluded_model_families: 'Excluded Models',
  enabled: 'HPO Enabled',
  search_method: 'Search Method',
  budget_level: 'Budget Level',
  max_trials: 'Max Trials',
  split_strategy: 'Split Strategy',
  n_splits: 'CV Folds',
  test_size: 'Test Size',
  random_state: 'Random Seed',
  stratification_required: 'Stratification',
  primary_metric: 'Primary Metric',
  secondary_metrics: 'Secondary Metrics',
  metric_direction: 'Metric Direction',
};

const CHANGE_COLORS: Record<string, string> = {
  modified: '#1565c0',
  added: '#2e7d32',
  removed: '#c62828',
  confirmed: '#757575',
};

const CHANGE_BG: Record<string, string> = {
  modified: '#e3f2fd',
  added: '#e8f5e9',
  removed: '#ffebee',
  confirmed: '#f5f5f5',
};

const ModelSearchContextPanel: React.FC<ModelSearchContextPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ModelSearchContextResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [expandedRationales, setExpandedRationales] = useState<Set<number>>(new Set());

  const toggleRationale = (index: number) => {
    setExpandedRationales(prev => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createModelSearchContext(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run model search context update.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunModelSearchContext(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run model search context update.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'updated': return '#4caf50';
      case 'updated_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      case 'blocked': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...styles.badge, backgroundColor: color }}>{label}</span>
  );

  const Section: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={styles.section}>
      <strong style={styles.sectionTitle}>{title}</strong>
      <div style={styles.sectionContent}>{children}</div>
    </div>
  );

  const renderValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) return <span style={{ color: '#9e9e9e', fontStyle: 'italic' }}>none</span>;
    if (Array.isArray(value)) {
      if (value.length === 0) return <span style={{ color: '#9e9e9e', fontStyle: 'italic' }}>none</span>;
      // Array of objects: render each with structured display
      if (value.every((v: any) => typeof v === 'object' && v !== null && !Array.isArray(v))) {
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {value.map((v: any, i: number) => (
              <span key={i}>
                {v.model_family && <Badge label={v.model_family} color={v.reason ? '#c62828' : '#1565c0'} />}
              </span>
            ))}
          </div>
        );
      }
      // Array of primitives: render as badges
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
          {value.map((v, i) => (
            <Badge key={i} label={String(v)} color="#455a64" />
          ))}
        </div>
      );
    }
    if (typeof value === 'boolean') {
      return <Badge label={value ? 'Yes' : 'No'} color={value ? '#2e7d32' : '#9e9e9e'} />;
    }
    if (typeof value === 'number') return String(value);
    if (typeof value === 'object') {
      return (
        <div style={{ fontSize: '11px' }}>
          {Object.entries(value).map(([k, v]) => (
            <div key={k}><strong>{k}:</strong> {typeof v === 'object' ? JSON.stringify(v) : String(v)}</div>
          ))}
        </div>
      );
    }
    return String(value);
  };

  const renderRationale = (r: StrategyChangeRationale | null | undefined): React.ReactNode => {
    if (!r) return <span style={{ color: '#9e9e9e', fontStyle: 'italic' }}>No rationale provided</span>;
    return (
      <div style={{ fontSize: '12px', lineHeight: '1.5' }}>
        {r.reason && (
          <div style={{ marginBottom: '6px' }}>
            <strong>Reason:</strong> {r.reason}
          </div>
        )}
        {r.evidence && r.evidence.length > 0 && (
          <div style={{ marginBottom: '6px' }}>
            <strong>Evidence:</strong>
            <ul style={{ margin: '2px 0 0 16px', padding: 0 }}>
              {r.evidence.map((e, i) => <li key={i}>{e}</li>)}
            </ul>
          </div>
        )}
        {r.expected_benefit && (
          <div style={{ marginBottom: '6px' }}>
            <strong>Expected Benefit:</strong> {r.expected_benefit}
          </div>
        )}
        {r.risk && (
          <div style={{ marginBottom: '6px' }}>
            <strong style={{ color: '#c62828' }}>Risk:</strong> {r.risk}
          </div>
        )}
        {r.fallback && (
          <div style={{ marginBottom: '2px' }}>
            <strong>Fallback:</strong> {r.fallback}
          </div>
        )}
      </div>
    );
  };

  const extractItemReasons = (change: StrategyChange): { family: string; reason: string }[] => {
    // Extract per-item reasons from rejected_model_actions or selected_model_actions
    const items = change.original_value || change.updated_value || [];
    if (!Array.isArray(items)) return [];
    return items
      .filter((v: any) => typeof v === 'object' && v !== null && v.reason)
      .map((v: any) => ({ family: v.model_family || v.family || '?', reason: v.reason }));
  };

  const changesByArea = (changes: StrategyChange[]): Record<string, StrategyChange[]> => {
    const groups: Record<string, StrategyChange[]> = {};
    for (const c of changes) {
      const area = c.strategy_area || 'other';
      if (!groups[area]) groups[area] = [];
      groups[area].push(c);
    }
    return groups;
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Model Search Plan</h3>
      <p style={styles.description}>
        LLM-guided strategy planning and execution plan generation. Analyzes the
        preprocessed dataset to recommend model families, HPO settings, and produces
        concrete execution plans with search spaces and trial allocation.
      </p>

      <div style={styles.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={styles.runButton}>
          {loading ? 'Running...' : 'Run Context Update'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={styles.rerunButton}>
          {loading ? 'Running...' : 'Re-run Update'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Model Search Context Result</h4>

          <div style={styles.fieldRow}>
            <div style={styles.field}><strong>Context ID:</strong> {result.context_id}</div>
            <div style={styles.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={styles.field}><strong>Update Mode:</strong> {result.update_mode}</div>
            <div style={styles.field}><strong>Confidence:</strong> {result.confidence_score != null ? result.confidence_score.toFixed(2) : 'N/A'}</div>
          </div>

          {/* Strategy Change Summary */}
          {result.strategy_change_summary && (
            <div style={styles.summaryBox}>
              <strong>Strategy Change Summary</strong>
              <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#333' }}>{result.strategy_change_summary}</p>
            </div>
          )}

          {/* Strategy Changes Table (grouped by area) */}
          {result.strategy_changes && result.strategy_changes.length > 0 && (
            <div>
              {Object.entries(changesByArea(result.strategy_changes)).map(([area, changes]) => (
                <div key={area} style={styles.strategyAreaBlock}>
                  <h5 style={styles.strategyAreaTitle}>
                    <span style={{
                      display: 'inline-block',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: CHANGE_COLORS[changes.some(c => c.change_type !== 'confirmed') ? 'modified' : 'confirmed'] || '#757575',
                      marginRight: '8px',
                    }} />
                    {AREA_LABELS[area] || area}
                  </h5>
                  <table style={styles.diffTable}>
                    <thead>
                      <tr>
                        <th style={{ ...styles.th, width: '15%' }}>Field</th>
                        <th style={{ ...styles.th, width: '22%' }}>Original Value</th>
                        <th style={{ ...styles.th, width: '22%' }}>Updated Value</th>
                        <th style={{ ...styles.th, width: '41%' }}>Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {changes.filter(change => {
                        // Hide model_selection_rationale_summary — it's free-form narrative, not useful as a diff row
                        if (change.field_path === 'model_selection_rationale_summary') return false;
                        // Hide rows where both original and updated are null/None — nothing to show
                        const origNull = change.original_value === null || change.original_value === undefined;
                        const updatedNull = change.updated_value === null || change.updated_value === undefined;
                        if (origNull && updatedNull) return false;
                        return true;
                      }).map((change, idx) => {
                        const globalIdx = result.strategy_changes.indexOf(change);
                        const isExpanded = expandedRationales.has(globalIdx);
                        const color = CHANGE_COLORS[change.change_type] || '#757575';
                        const bg = CHANGE_BG[change.change_type] || '#f5f5f5';
                        const hasRationale = change.decision_rationale && change.decision_rationale.reason;
                        // For rejected_model_actions / selected_model_actions, extract per-item reasons
                        const perItemReasons = extractItemReasons(change);
                        const hasItemReasons = perItemReasons.length > 0;

                        return (
                          <tr key={idx} style={{ borderLeft: `3px solid ${color}`, backgroundColor: bg }}>
                            <td style={styles.td}>
                              <span style={{ fontWeight: 600 }}>
                                {FIELD_LABELS[change.field_path] || change.field_path}
                              </span>
                            </td>
                            <td style={styles.tdOrig}>
                              {renderValue(change.original_value)}
                            </td>
                            <td style={styles.tdUpdated}>
                              {renderValue(change.updated_value)}
                            </td>
                            <td style={styles.tdRationale}>
                              {hasItemReasons && (
                                <div style={{ marginBottom: hasRationale ? '8px' : '0' }}>
                                  {perItemReasons.map((r, ri) => (
                                    <div key={ri} style={{ fontSize: '11px', marginBottom: '4px', color: '#c62828' }}>
                                      <strong>{r.family}:</strong> {r.reason}
                                    </div>
                                  ))}
                                </div>
                              )}
                              {hasRationale ? (
                                <>
                                  <div
                                    onClick={() => toggleRationale(globalIdx)}
                                    style={{ ...styles.rationaleToggle, color }}
                                  >
                                    {isExpanded ? '▼ Hide Rationale' : '▶ Show Rationale'}
                                  </div>
                                  {isExpanded && (
                                    <div style={{ marginTop: '6px', padding: '8px', backgroundColor: '#fafafa', borderRadius: '4px' }}>
                                      {renderRationale(change.decision_rationale)}
                                    </div>
                                  )}
                                </>
                              ) : (
                                !hasItemReasons && <span style={{ color: '#9e9e9e', fontStyle: 'italic', fontSize: '11px' }}>No rationale</span>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              ))}
            </div>
          )}

          {/* Risk Notes */}
          {result.llm_strategy_advice?.risk_notes && result.llm_strategy_advice.risk_notes.length > 0 && (
            <Section title="Risk Notes">
              {result.llm_strategy_advice.risk_notes.map((r, i) => (
                <div key={i} style={styles.riskItem}>⚠ {r}</div>
              ))}
            </Section>
          )}

          {/* Preprocessing Summary */}
          {result.preprocessing_summary && (
            <Section title="Preprocessing Summary">
              <div>
                Imputation:{' '}
                {result.preprocessing_summary.imputation_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Scaling:{' '}
                {result.preprocessing_summary.scaling_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Feature Selection:{' '}
                {result.preprocessing_summary.feature_selection_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div>
                Categorical Encoding:{' '}
                {result.preprocessing_summary.categorical_encoding_executed
                  ? <Badge label="Executed" color="#2e7d32" />
                  : <Badge label="Not Executed" color="#9e9e9e" />}
              </div>
            </Section>
          )}

          {/* HPO Plan */}
          {result.hpo_plan && (
            <Section title="HPO Plan">
              <div>
                HPO Enabled:{' '}
                <Badge label={result.hpo_plan.enabled ? 'Yes' : 'No'} color={result.hpo_plan.enabled ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div>Search Method: <Badge label={result.hpo_plan.search_method || 'N/A'} color="#1565c0" /></div>
              <div>
                Budget Level:{' '}
                <Badge label={result.hpo_plan.budget_level} color={BUDGET_COLORS[result.hpo_plan.budget_level] || '#1976d2'} />
              </div>
              <div>Max Total Trials: <strong>{result.hpo_plan.max_total_trials}</strong></div>
              <div>Max Parallel Trials: {result.hpo_plan.max_parallel_trials}</div>
              <div>
                Early Stopping:{' '}
                <Badge label={result.hpo_plan.early_stopping ? 'Yes' : 'No'} color={result.hpo_plan.early_stopping ? '#ff9800' : '#9e9e9e'} />
              </div>
              {result.hpo_plan.fallback_method && (
                <div>Fallback Method: {result.hpo_plan.fallback_method}</div>
              )}
              {result.hpo_plan.trial_allocation.length > 0 && (
                <div style={{ marginTop: '8px' }}>
                  <strong>Trial Allocation:</strong>
                  <table style={styles.table}>
                    <thead>
                      <tr>
                        <th style={{ ...styles.th, width: '18%' }}>Model</th>
                        <th style={{ ...styles.th, width: '12%' }}>Max Trials</th>
                        <th style={{ ...styles.th, width: '70%' }}>Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {result.hpo_plan.trial_allocation.map((t, i) => (
                        <tr key={i}>
                          <td style={styles.td}>{t.model_id}</td>
                          <td style={styles.td}>
                            <Badge
                              label={String(t.max_trials)}
                              color={t.max_trials === 0 ? '#9e9e9e' : '#1565c0'}
                            />
                          </td>
                          <td style={{ ...styles.td, fontSize: '11px', color: '#555' }}>
                            {t.allocation_rationale || '-'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Section>
          )}

          {/* Search Space Plan */}
          {result.search_space_plan && result.search_space_plan.spaces.length > 0 && (
            <Section title="Search Space Plan">
              {result.search_space_plan.spaces.map((sp, i) => (
                <div key={i} style={{ marginBottom: '8px' }}>
                  <strong>{sp.model_id}</strong> <span style={{ fontSize: '11px', color: '#888' }}>({sp.search_space_id})</span>
                  {sp.parameters.length > 0 ? (
                    <table style={{ ...styles.table, marginTop: '4px' }}>
                      <thead>
                        <tr>
                          <th style={{ ...styles.th, width: '18%' }}>Parameter</th>
                          <th style={{ ...styles.th, width: '10%' }}>Type</th>
                          <th style={{ ...styles.th, width: '22%' }}>Range</th>
                          <th style={{ ...styles.th, width: '12%' }}>Sampling</th>
                          <th style={{ ...styles.th, width: '10%' }}>Default</th>
                          <th style={{ ...styles.th, width: '28%' }}>LLM Override</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sp.parameters.map((p, j) => (
                          <tr key={j} style={p.override_rationale ? { backgroundColor: '#fff8e1' } : undefined}>
                            <td style={styles.td}>
                              {p.name}
                              {p.override_rationale && (
                                <span style={{ marginLeft: '4px', fontSize: '10px', color: '#f57c00' }}>⚡</span>
                              )}
                            </td>
                            <td style={styles.td}>{p.param_type}</td>
                            <td style={styles.td}>
                              {p.choices.length > 0
                                ? p.choices.join(', ')
                                : `[${p.low ?? '?'}, ${p.high ?? '?'}]`}
                            </td>
                            <td style={styles.td}>{p.sampling}</td>
                            <td style={styles.td}>{p.default_value || '-'}</td>
                            <td style={{ ...styles.td, fontSize: '11px', color: p.override_rationale ? '#e65100' : '#9e9e9e', fontStyle: p.override_rationale ? 'normal' : 'italic' }}>
                              {p.override_rationale || 'template default'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div style={{ fontSize: '12px', color: '#888', marginLeft: '16px' }}>No HPO parameters (no HPO needed)</div>
                  )}
                </div>
              ))}
            </Section>
          )}

          {/* Validation Plan */}
          {result.validation_plan && (
            <Section title="Validation Plan">
              <div>Split Strategy: {result.validation_plan.split_strategy}</div>
              <div>CV Splits: {result.validation_plan.n_splits}</div>
              <div>Random State: {result.validation_plan.random_state}</div>
              <div>Shuffle: <Badge label={result.validation_plan.shuffle ? 'Yes' : 'No'} color={result.validation_plan.shuffle ? '#2e7d32' : '#9e9e9e'} /></div>
              <div>Benchmark Split: <Badge label={result.validation_plan.benchmark_split ? 'Yes' : 'No'} color={result.validation_plan.benchmark_split ? '#ff9800' : '#9e9e9e'} /></div>
            </Section>
          )}

          {/* Evaluation Plan */}
          {result.evaluation_plan && (
            <Section title="Evaluation Plan">
              <div>Primary Metric: {result.evaluation_plan.primary_metric || 'N/A'}</div>
              <div>Direction: {result.evaluation_plan.metric_direction}</div>
              <div>Scorer ID: {result.evaluation_plan.scorer_id || 'default'}</div>
              {result.evaluation_plan.secondary_metrics.length > 0 && (
                <div>Secondary Metrics: {result.evaluation_plan.secondary_metrics.join(', ')}</div>
              )}
            </Section>
          )}

          {/* Pipeline Generation Input */}
          {result.pipeline_generation_input && (
            <Section title="Pipeline Generation Input">
              <div>
                Ready for Pipeline Generation:{' '}
                <span style={{ color: result.pipeline_generation_input.ready_for_pipeline_generation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.pipeline_generation_input.ready_for_pipeline_generation ? 'Yes' : 'No'}
                </span>
              </div>
              <div>Target Column: {result.pipeline_generation_input.target_column || 'N/A'}</div>
              <div>Feature Columns: {result.pipeline_generation_input.feature_columns.length} columns</div>
            </Section>
          )}

          {/* Warnings */}
          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.warningSection}>
              <strong style={{ color: '#e65100' }}>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={styles.warningItem}>⚠ {w}</div>
              ))}
            </div>
          )}

          {/* Errors */}
          {result.errors && result.errors.length > 0 && (
            <div style={styles.errorSection}>
              <strong style={{ color: '#c62828' }}>Errors:</strong>
              {result.errors.map((e, i) => (
                <div key={i} style={styles.errorItem}>{e}</div>
              ))}
            </div>
          )}

          {/* Error Message */}
          {result.error_message && (
            <div style={styles.errorSection}>
              <strong style={{ color: '#c62828' }}>Error Message:</strong>
              <div style={{ marginTop: '4px', fontSize: '12px' }}>{result.error_message}</div>
            </div>
          )}

          {/* Full JSON (collapsed by default) */}
          <details style={styles.jsonSection}>
            <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '13px', marginBottom: '8px' }}>
              Full Result (JSON)
            </summary>
            <pre style={styles.pre}>{JSON.stringify(result, null, 2)}</pre>
          </details>
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#f3f4f6',
    border: '1px solid #9e9e9e',
    borderRadius: '8px',
    maxHeight: '70vh',
    overflowY: 'auto',
  },
  title: {
    margin: '0 0 8px 0',
    fontSize: '18px',
    fontWeight: 600,
    color: '#333',
  },
  description: {
    margin: '0 0 16px 0',
    fontSize: '14px',
    color: '#666',
  },
  buttonRow: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
  },
  runButton: {
    padding: '10px 20px',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px',
    backgroundColor: '#6c757d',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  errorBox: {
    marginBottom: '16px',
    padding: '12px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '4px',
    color: '#c62828',
    fontSize: '14px',
  },
  resultBox: {
    padding: '16px',
    backgroundColor: '#e8f5e9',
    border: '1px solid #4caf50',
    borderRadius: '4px',
  },
  resultTitle: {
    margin: '0 0 12px 0',
    fontSize: '16px',
    fontWeight: 600,
  },
  fieldRow: {
    display: 'flex',
    flexWrap: 'wrap',
    gap: '24px',
    marginBottom: '12px',
  },
  field: {
    fontSize: '14px',
  },
  summaryBox: {
    marginTop: '8px',
    marginBottom: '12px',
    padding: '12px',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    border: '1px solid #1565c0',
    fontSize: '13px',
  },
  strategyAreaBlock: {
    marginBottom: '16px',
  },
  strategyAreaTitle: {
    margin: '0 0 8px 0',
    fontSize: '14px',
    fontWeight: 600,
    color: '#333',
    display: 'flex',
    alignItems: 'center',
  },
  diffTable: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: '12px',
    tableLayout: 'fixed' as const,
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    marginTop: '4px',
    fontSize: '12px',
  },
  th: {
    textAlign: 'left' as const,
    padding: '6px 8px',
    borderBottom: '2px solid #e0e0e0',
    fontWeight: 600,
    color: '#555',
    backgroundColor: '#fafafa',
  },
  td: {
    padding: '3px 8px',
    borderBottom: '1px solid #f0f0f0',
    verticalAlign: 'top',
    overflowWrap: 'break-word' as const,
    wordBreak: 'break-word' as const,
  },
  tdOrig: {
    padding: '8px',
    borderBottom: '1px solid #e0e0e0',
    verticalAlign: 'top',
    overflowWrap: 'break-word' as const,
    wordBreak: 'break-word' as const,
    color: '#666',
  },
  tdUpdated: {
    padding: '8px',
    borderBottom: '1px solid #e0e0e0',
    verticalAlign: 'top',
    overflowWrap: 'break-word' as const,
    wordBreak: 'break-word' as const,
    fontWeight: 600,
  },
  tdRationale: {
    padding: '8px',
    borderBottom: '1px solid #e0e0e0',
    verticalAlign: 'top',
    overflowWrap: 'break-word' as const,
    wordBreak: 'break-word' as const,
  },
  rationaleToggle: {
    cursor: 'pointer',
    fontSize: '12px',
    fontWeight: 600,
    userSelect: 'none' as const,
  },
  riskItem: {
    marginTop: '4px',
    marginLeft: '8px',
    fontSize: '12px',
    color: '#c62828',
  },
  section: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#fff',
    borderRadius: '4px',
    border: '1px solid #e0e0e0',
  },
  sectionTitle: {
    fontSize: '13px',
    fontWeight: 600,
    color: '#555',
    textTransform: 'uppercase' as const,
    display: 'block',
    marginBottom: '6px',
  },
  sectionContent: {
    fontSize: '13px',
    color: '#333',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '3px',
  },
  badge: {
    display: 'inline-block',
    color: '#fff',
    padding: '1px 8px',
    borderRadius: '10px',
    fontSize: '11px',
    marginLeft: '4px',
    marginBottom: '2px',
  },
  warningSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#fff3e0',
    borderRadius: '4px',
    border: '1px solid #ffcc02',
    fontSize: '13px',
  },
  warningItem: {
    marginTop: '4px',
    marginLeft: '8px',
    fontSize: '12px',
  },
  errorSection: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#ffebee',
    borderRadius: '4px',
    border: '1px solid #f44336',
    fontSize: '13px',
  },
  errorItem: {
    marginTop: '4px',
    marginLeft: '8px',
    fontSize: '12px',
  },
  jsonSection: {
    marginTop: '16px',
  },
  pre: {
    backgroundColor: '#fff',
    padding: '12px',
    borderRadius: '4px',
    overflow: 'auto',
    fontSize: '12px',
    marginTop: '8px',
    maxHeight: '300px',
  },
};

export default ModelSearchContextPanel;
