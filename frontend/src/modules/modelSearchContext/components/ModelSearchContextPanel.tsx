import React, { useState } from 'react';
import { Button, Space, Tabs, Card } from 'antd';
import {
  createModelSearchContext,
  rerunModelSearchContext,
} from '../../../api/modelSearchContextApi';
import {
  ModelSearchContextResponse,
  StrategyChange,
  StrategyChangeRationale,
} from '../types';
import { pipelineAccent } from '../../../theme/pipelineColors';
import { PanelContainer, StatusBadge, WarningBox, ErrorBox, JsonViewer } from '../../../components/shared';

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

const tableThStyle: React.CSSProperties = {
  textAlign: 'left',
  padding: '6px 8px',
  borderBottom: '2px solid #e0e0e0',
  backgroundColor: '#f5f5f5',
  fontWeight: 600,
};

const tableTdStyle: React.CSSProperties = {
  padding: '4px 8px',
  verticalAlign: 'top',
  fontSize: '13px',
  overflowWrap: 'break-word',
  wordBreak: 'break-word',
};

const gridStyle: React.CSSProperties = {
  display: 'grid',
  gridTemplateColumns: '1fr 1fr',
  gap: '8px',
  marginBottom: '8px',
};

const fieldStyle: React.CSSProperties = { fontSize: '14px' };

const ModelSearchContextPanel: React.FC<ModelSearchContextPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ModelSearchContextResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [expandedRationales, setExpandedRationales] = useState<Set<number>>(new Set());
  const [activeTab, setActiveTab] = useState<string>('changes');

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

  const renderValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) return <span style={{ color: '#9e9e9e', fontStyle: 'italic' }}>none</span>;
    if (Array.isArray(value)) {
      if (value.length === 0) return <span style={{ color: '#9e9e9e', fontStyle: 'italic' }}>none</span>;
      if (value.every((v: any) => typeof v === 'object' && v !== null && !Array.isArray(v))) {
        return (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '3px' }}>
            {value.map((v: any, i: number) => (
              <span key={i}>
                {v.model_family && <StatusBadge label={v.model_family} color={v.reason ? '#c62828' : '#1565c0'} />}
              </span>
            ))}
          </div>
        );
      }
      return (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '2px' }}>
          {value.map((v, i) => (
            <StatusBadge key={i} label={String(v)} color="#455a64" />
          ))}
        </div>
      );
    }
    if (typeof value === 'boolean') {
      return <StatusBadge label={value ? 'Yes' : 'No'} color={value ? '#2e7d32' : '#9e9e9e'} />;
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

  const renderChangesTab = () => {
    if (!result) return null;
    return (
      <div>
        <Card size="small" title="Status" style={{ marginBottom: 12 }}>
          <div style={gridStyle}>
            <div style={fieldStyle}><strong>Context ID:</strong> {result.context_id}</div>
            <div style={fieldStyle}>
              <strong>Status: </strong>
              <StatusBadge label={result.status} color={getStatusColor(result.status)} />
            </div>
            <div style={fieldStyle}><strong>Update Mode:</strong> {result.update_mode || '—'}</div>
            <div style={fieldStyle}><strong>Confidence:</strong> {result.confidence_score != null ? result.confidence_score.toFixed(2) : 'N/A'}</div>
          </div>
        </Card>

        {result.strategy_change_summary && (
          <Card size="small" title="Strategy Change Summary" style={{ marginBottom: 12 }}>
            <p style={{ margin: '6px 0 0 0', fontSize: '13px', color: '#333' }}>{result.strategy_change_summary}</p>
          </Card>
        )}

        {result.strategy_changes && result.strategy_changes.length > 0 && (
          <>
            {Object.entries(changesByArea(result.strategy_changes)).map(([area, changes]) => (
              <Card
                key={area}
                size="small"
                style={{ marginBottom: 12 }}
                title={
                  <span>
                    <span style={{
                      display: 'inline-block',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: CHANGE_COLORS[changes.some(c => c.change_type !== 'confirmed') ? 'modified' : 'confirmed'] || '#757575',
                      marginRight: '8px',
                    }} />
                    {AREA_LABELS[area] || area}
                  </span>
                }
              >
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', minWidth: '900px' }}>
                    <thead>
                      <tr>
                        <th style={{ ...tableThStyle, width: '15%' }}>Field</th>
                        <th style={{ ...tableThStyle, width: '22%' }}>Original Value</th>
                        <th style={{ ...tableThStyle, width: '22%' }}>Updated Value</th>
                        <th style={{ ...tableThStyle, width: '41%' }}>Rationale</th>
                      </tr>
                    </thead>
                    <tbody>
                      {changes.filter(change => {
                        if (change.field_path === 'model_selection_rationale_summary') return false;
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
                        const perItemReasons = extractItemReasons(change);
                        const hasItemReasons = perItemReasons.length > 0;

                        return (
                          <tr key={idx} style={{ borderLeft: `3px solid ${color}`, backgroundColor: bg }}>
                            <td style={tableTdStyle}>
                              <span style={{ fontWeight: 600 }}>
                                {FIELD_LABELS[change.field_path] || change.field_path}
                              </span>
                            </td>
                            <td style={{ ...tableTdStyle, color: '#666' }}>
                              {renderValue(change.original_value)}
                            </td>
                            <td style={{ ...tableTdStyle, fontWeight: 600 }}>
                              {renderValue(change.updated_value)}
                            </td>
                            <td style={tableTdStyle}>
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
                                    style={{ cursor: 'pointer', fontSize: '12px', fontWeight: 600, color, userSelect: 'none' as const }}
                                  >
                                    {isExpanded ? 'Hide Rationale' : 'Show Rationale'}
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
              </Card>
            ))}
          </>
        )}

        {result.llm_strategy_advice?.risk_notes && result.llm_strategy_advice.risk_notes.length > 0 && (
          <WarningBox warnings={result.llm_strategy_advice.risk_notes} />
        )}
      </div>
    );
  };

  const renderPlansTab = () => {
    if (!result) return null;
    return (
      <div>
        {result.preprocessing_summary && (
          <Card size="small" title="Preprocessing Summary" style={{ marginBottom: 12 }}>
            <div style={gridStyle}>
              <div style={fieldStyle}>
                <strong>Imputation:</strong>{' '}
                {result.preprocessing_summary.imputation_executed
                  ? <StatusBadge label="Executed" color="#2e7d32" />
                  : <StatusBadge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div style={fieldStyle}>
                <strong>Scaling:</strong>{' '}
                {result.preprocessing_summary.scaling_executed
                  ? <StatusBadge label="Executed" color="#2e7d32" />
                  : <StatusBadge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div style={fieldStyle}>
                <strong>Feature Selection:</strong>{' '}
                {result.preprocessing_summary.feature_selection_executed
                  ? <StatusBadge label="Executed" color="#2e7d32" />
                  : <StatusBadge label="Not Executed" color="#9e9e9e" />}
              </div>
              <div style={fieldStyle}>
                <strong>Categorical Encoding:</strong>{' '}
                {result.preprocessing_summary.categorical_encoding_executed
                  ? <StatusBadge label="Executed" color="#2e7d32" />
                  : <StatusBadge label="Not Executed" color="#9e9e9e" />}
              </div>
            </div>
          </Card>
        )}

        {result.hpo_plan && (
          <Card size="small" title="HPO Plan" style={{ marginBottom: 12 }}>
            <div style={gridStyle}>
              <div style={fieldStyle}>
                <strong>HPO Enabled:</strong>{' '}
                <StatusBadge label={result.hpo_plan.enabled ? 'Yes' : 'No'} color={result.hpo_plan.enabled ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div style={fieldStyle}>
                <strong>Search Method:</strong> <StatusBadge label={result.hpo_plan.search_method || 'N/A'} color="#1565c0" />
              </div>
              <div style={fieldStyle}>
                <strong>Budget Level:</strong>{' '}
                <StatusBadge label={result.hpo_plan.budget_level} color={BUDGET_COLORS[result.hpo_plan.budget_level] || '#1976d2'} />
              </div>
              <div style={fieldStyle}><strong>Max Total Trials:</strong> {result.hpo_plan.max_total_trials}</div>
              <div style={fieldStyle}><strong>Max Parallel Trials:</strong> {result.hpo_plan.max_parallel_trials}</div>
              <div style={fieldStyle}>
                <strong>Early Stopping:</strong>{' '}
                <StatusBadge label={result.hpo_plan.early_stopping ? 'Yes' : 'No'} color={result.hpo_plan.early_stopping ? '#ff9800' : '#9e9e9e'} />
              </div>
              {result.hpo_plan.fallback_method && (
                <div style={fieldStyle}><strong>Fallback:</strong> {result.hpo_plan.fallback_method}</div>
              )}
            </div>
            {result.hpo_plan.trial_allocation.length > 0 && (
              <Card size="small" style={{ marginTop: 8 }} title="Trial Allocation">
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px' }}>
                  <thead>
                    <tr>
                      <th style={{ ...tableThStyle, width: '20%' }}>Model</th>
                      <th style={{ ...tableThStyle, width: '15%' }}>Max Trials</th>
                      <th style={{ ...tableThStyle, width: '65%' }}>Rationale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.hpo_plan.trial_allocation.map((t, i) => (
                      <tr key={i}>
                        <td style={tableTdStyle}>{t.model_id}</td>
                        <td style={tableTdStyle}>
                          <StatusBadge
                            label={String(t.max_trials)}
                            color={t.max_trials === 0 ? '#9e9e9e' : '#1565c0'}
                          />
                        </td>
                        <td style={{ ...tableTdStyle, fontSize: '12px', color: '#555' }}>
                          {t.allocation_rationale || '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Card>
            )}
          </Card>
        )}

        {result.search_space_plan && result.search_space_plan.spaces.length > 0 && (
          <Card size="small" title="Search Space Plan" style={{ marginBottom: 12 }}>
            {result.search_space_plan.spaces.map((sp, i) => (
              <div key={i} style={{ marginBottom: '12px' }}>
                <strong>{sp.model_id}</strong> <span style={{ fontSize: '11px', color: '#888' }}>({sp.search_space_id})</span>
                {sp.parameters.length > 0 ? (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', marginTop: '4px', minWidth: '800px' }}>
                      <thead>
                        <tr>
                          <th style={{ ...tableThStyle, width: '18%' }}>Parameter</th>
                          <th style={{ ...tableThStyle, width: '10%' }}>Type</th>
                          <th style={{ ...tableThStyle, width: '22%' }}>Range</th>
                          <th style={{ ...tableThStyle, width: '12%' }}>Sampling</th>
                          <th style={{ ...tableThStyle, width: '10%' }}>Default</th>
                          <th style={{ ...tableThStyle, width: '28%' }}>AI Override</th>
                        </tr>
                      </thead>
                      <tbody>
                        {sp.parameters.map((p, j) => (
                          <tr key={j} style={p.override_rationale ? { backgroundColor: '#fff8e1' } : undefined}>
                            <td style={tableTdStyle}>
                              {p.name}
                              {p.override_rationale && (
                                <span style={{ marginLeft: '4px', fontSize: '10px', color: '#f57c00' }}>*</span>
                              )}
                            </td>
                            <td style={tableTdStyle}>{p.param_type}</td>
                            <td style={tableTdStyle}>
                              {p.choices.length > 0
                                ? p.choices.join(', ')
                                : `[${p.low ?? '?'}, ${p.high ?? '?'}]`}
                            </td>
                            <td style={tableTdStyle}>{p.sampling}</td>
                            <td style={tableTdStyle}>{p.default_value || '-'}</td>
                            <td style={{ ...tableTdStyle, fontSize: '11px', color: p.override_rationale ? '#e65100' : '#9e9e9e', fontStyle: p.override_rationale ? 'normal' : 'italic' }}>
                              {p.override_rationale || 'template default'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ fontSize: '12px', color: '#888', marginLeft: '16px' }}>No HPO parameters (no HPO needed)</div>
                )}
              </div>
            ))}
          </Card>
        )}

        {result.validation_plan && (
          <Card size="small" title="Validation Plan" style={{ marginBottom: 12 }}>
            <div style={gridStyle}>
              <div style={fieldStyle}><strong>Split Strategy:</strong> {result.validation_plan.split_strategy}</div>
              <div style={fieldStyle}><strong>CV Splits:</strong> {result.validation_plan.n_splits}</div>
              <div style={fieldStyle}><strong>Random State:</strong> {result.validation_plan.random_state}</div>
              <div style={fieldStyle}>
                <strong>Shuffle:</strong>{' '}
                <StatusBadge label={result.validation_plan.shuffle ? 'Yes' : 'No'} color={result.validation_plan.shuffle ? '#2e7d32' : '#9e9e9e'} />
              </div>
              <div style={fieldStyle}>
                <strong>Benchmark Split:</strong>{' '}
                <StatusBadge label={result.validation_plan.benchmark_split ? 'Yes' : 'No'} color={result.validation_plan.benchmark_split ? '#ff9800' : '#9e9e9e'} />
              </div>
            </div>
          </Card>
        )}

        {result.evaluation_plan && (
          <Card size="small" title="Evaluation Plan" style={{ marginBottom: 12 }}>
            <div style={gridStyle}>
              <div style={fieldStyle}><strong>Primary Metric:</strong> {result.evaluation_plan.primary_metric || 'N/A'}</div>
              <div style={fieldStyle}><strong>Direction:</strong> {result.evaluation_plan.metric_direction}</div>
              <div style={fieldStyle}><strong>Scorer ID:</strong> {result.evaluation_plan.scorer_id || 'default'}</div>
              {result.evaluation_plan.secondary_metrics.length > 0 && (
                <div style={fieldStyle}><strong>Secondary:</strong> {result.evaluation_plan.secondary_metrics.join(', ')}</div>
              )}
            </div>
          </Card>
        )}

        {result.pipeline_generation_input && (
          <Card size="small" title="Pipeline Generation Input" style={{ marginBottom: 12 }}>
            <div style={gridStyle}>
              <div style={fieldStyle}>
                <strong>Ready:</strong>{' '}
                <span style={{ color: result.pipeline_generation_input.ready_for_pipeline_generation ? '#2e7d32' : '#c62828', fontWeight: 600 }}>
                  {result.pipeline_generation_input.ready_for_pipeline_generation ? 'Yes' : 'No'}
                </span>
              </div>
              <div style={fieldStyle}><strong>Target Column:</strong> {result.pipeline_generation_input.target_column || 'N/A'}</div>
              <div style={fieldStyle}><strong>Feature Columns:</strong> {result.pipeline_generation_input.feature_columns.length} columns</div>
            </div>
          </Card>
        )}
      </div>
    );
  };

  return (
    <PanelContainer
      title="Model Search Plan"
      description="AI-guided strategy planning and execution plan generation. Analyzes the preprocessed dataset to recommend model families, HPO settings, and produces concrete execution plans with search spaces and trial allocation."
      accentColor={pipelineAccent.modelSearchContext}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          Run Context Update
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Update
        </Button>
      </Space>

      {error && <ErrorBox message={error} />}

      {result && (
        <>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'changes',
                label: 'Strategy Changes',
                children: renderChangesTab(),
              },
              {
                key: 'plans',
                label: 'Plans & Execution',
                children: renderPlansTab(),
              },
              {
                key: 'json',
                label: 'Full JSON',
                children: (
                  <Card size="small" title="Full JSON">
                    <JsonViewer data={result} />
                  </Card>
                ),
              },
            ]}
          />

          {result.warnings && result.warnings.length > 0 && (
            <WarningBox warnings={result.warnings} style={{ marginTop: 16 }} />
          )}

          {result.errors && result.errors.length > 0 && (
            <ErrorBox message={result.errors.map((e: string) => e).join('; ')} style={{ marginTop: 16 }} />
          )}

          {result.error_message && (
            <ErrorBox message={result.error_message} style={{ marginTop: 16 }} />
          )}
        </>
      )}
    </PanelContainer>
  );
};

export default ModelSearchContextPanel;
