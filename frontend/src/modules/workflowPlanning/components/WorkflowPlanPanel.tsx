import React, { useState } from 'react';
import { createWorkflowPlan, rerunWorkflowPlan } from '../../../api/workflowPlanningApi';
import { WorkflowPlanResponse } from '../types';

interface WorkflowPlanPanelProps {
  taskId: string;
}

const WorkflowPlanPanel: React.FC<WorkflowPlanPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<WorkflowPlanResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleRunPlanning = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createWorkflowPlan(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run workflow planning.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunWorkflowPlan(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run workflow planning.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'planned': return '#4caf50';
      case 'planned_with_warning': return '#ff9800';
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

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>LLM-guided Workflow Planning</h3>
      <p style={styles.description}>
        Generate a structured machine learning workflow plan based on task specification,
        task interpretation, and dataset profiling results.
      </p>

      <div style={styles.buttonRow}>
        <button onClick={handleRunPlanning} disabled={loading} style={styles.runButton}>
          {loading ? 'Planning...' : 'Run Workflow Planning'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={styles.rerunButton}>
          {loading ? 'Planning...' : 'Re-run Planning'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Workflow Plan Result</h4>

          <div style={styles.fieldRow}>
            <div style={styles.field}><strong>Plan ID:</strong> {result.workflow_plan_id}</div>
            <div style={styles.field}>
              <strong>Status:</strong>{' '}
              <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>{result.status}</span>
            </div>
            <div style={styles.field}><strong>Confidence:</strong> {result.confidence_score}</div>
          </div>

          {/* Task Summary */}
          {result.task_summary && (
            <Section title="Task Summary">
              <div>Type: {result.task_summary.task_type}</div>
              <div>Input Modality: {result.task_summary.input_modality}</div>
              <div>Prediction Target: {result.task_summary.prediction_target}</div>
              <div>Material Domain: {result.task_summary.material_domain}</div>
              <div>Primary Goal: {result.task_summary.primary_goal}</div>
            </Section>
          )}

          {/* Data Strategy */}
          {result.data_strategy && (
            <Section title="Data Strategy">
              <div>Target Column: {result.data_strategy.target_column}</div>
              <div>Input Columns: {result.data_strategy.input_columns?.join(', ')}</div>
              <div>Duplicate Handling: {result.data_strategy.duplicate_handling}</div>
              <div>Missing Value Strategy: {result.data_strategy.missing_value_strategy}</div>
              {result.data_strategy.target_handling && (
                <div>
                  Target Handling:{' '}
                  {result.data_strategy.target_handling.requires_transformation_check
                    ? `Transform (${result.data_strategy.target_handling.recommended_transformation})`
                    : 'No transformation needed'}
                </div>
              )}
              {result.data_strategy.required_cleaning_steps && result.data_strategy.required_cleaning_steps.length > 0 && (
                <div>Cleaning Steps: {result.data_strategy.required_cleaning_steps.join(', ')}</div>
              )}
            </Section>
          )}

          {/* Feature Strategy */}
          {result.feature_strategy && (
            <Section title="Feature Strategy">
              <div>Feature Type: {result.feature_strategy.feature_type}</div>
              {result.feature_strategy.executable_featurizers && result.feature_strategy.executable_featurizers.length > 0 && (
                <div>
                  Executable Featurizers:{' '}
                  {result.feature_strategy.executable_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#2e7d32" />
                  ))}
                </div>
              )}
              {result.feature_strategy.semantic_featurizers && result.feature_strategy.semantic_featurizers.length > 0 && (
                <div>
                  Semantic Featurizers:{' '}
                  {result.feature_strategy.semantic_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#1565c0" />
                  ))}
                </div>
              )}
              {result.feature_strategy.unsupported_future_featurizers && result.feature_strategy.unsupported_future_featurizers.length > 0 && (
                <div>
                  Future/Unsupported:{' '}
                  {result.feature_strategy.unsupported_future_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#9e9e9e" />
                  ))}
                </div>
              )}
              {result.feature_strategy.recommended_featurizers && result.feature_strategy.recommended_featurizers.length > 0 && (
                <div>
                  Recommended Featurizers (legacy):{' '}
                  {result.feature_strategy.recommended_featurizers.map((f, i) => (
                    <Badge key={i} label={f} color="#6a1b9a" />
                  ))}
                </div>
              )}
              <div>Structure Features Required: {result.feature_strategy.requires_structure_features ? 'Yes' : 'No'}</div>
              <div>Feature Selection: {result.feature_strategy.feature_selection_required ? 'Yes' : 'No'}</div>
              <div>Feature Scaling: {result.feature_strategy.feature_scaling_required ? 'Yes' : 'No'}</div>
            </Section>
          )}

          {/* Model Strategy */}
          {result.model_strategy && (
            <Section title="Model Strategy">
              <div>Preferred Bias: {result.model_strategy.preferred_model_bias}</div>
              <div>
                Candidate Models:{' '}
                {result.model_strategy.candidate_model_families?.map((m, i) => (
                  <Badge key={i} label={m} color="#1565c0" />
                ))}
              </div>
              <div>
                Baseline Models:{' '}
                {result.model_strategy.baseline_models?.map((m, i) => (
                  <Badge key={i} label={m} color="#6a1b9a" />
                ))}
              </div>
              {result.model_strategy.excluded_model_families && result.model_strategy.excluded_model_families.length > 0 && (
                <div>Excluded: {result.model_strategy.excluded_model_families.join(', ')}</div>
              )}
            </Section>
          )}

          {/* Validation Strategy */}
          {result.validation_strategy && (
            <Section title="Validation Strategy">
              <div>Split: {result.validation_strategy.split_strategy}</div>
              <div>n_splits: {result.validation_strategy.n_splits}</div>
              {result.validation_strategy.test_size != null && (
                <div>Test Size: {result.validation_strategy.test_size}</div>
              )}
              <div>Random State: {result.validation_strategy.random_state}</div>
              <div>Stratification: {result.validation_strategy.stratification_required ? 'Yes' : 'No'}</div>
            </Section>
          )}

          {/* Evaluation Strategy */}
          {result.evaluation_strategy && (
            <Section title="Evaluation Strategy">
              <div>Primary Metric: <strong>{result.evaluation_strategy.primary_metric}</strong></div>
              <div>Secondary: {result.evaluation_strategy.secondary_metrics?.join(', ')}</div>
              <div>Direction: {result.evaluation_strategy.metric_direction}</div>
            </Section>
          )}

          {/* HPO Strategy */}
          {result.hpo_strategy && (
            <Section title="HPO Strategy">
              <div>Enabled: {result.hpo_strategy.enabled ? 'Yes' : 'No'}</div>
              {result.hpo_strategy.enabled && (
                <>
                  <div>Search Method: {result.hpo_strategy.search_method}</div>
                  <div>Budget: {result.hpo_strategy.budget_level} ({result.hpo_strategy.max_trials} trials)</div>
                </>
              )}
            </Section>
          )}

          {/* Interpretability Strategy */}
          {result.interpretability_strategy && (
            <Section title="Interpretability Strategy">
              <div>Enabled: {result.interpretability_strategy.enabled ? 'Yes' : 'No'}</div>
              {result.interpretability_strategy.enabled && (
                <>
                  <div>Priority: {result.interpretability_strategy.priority}</div>
                  <div>
                    Methods:{' '}
                    {result.interpretability_strategy.methods?.map((m, i) => (
                      <Badge key={i} label={m} color="#00838f" />
                    ))}
                  </div>
                </>
              )}
            </Section>
          )}

          {/* Pipeline Generation Input */}
          {result.pipeline_generation_input && (
            <Section title="Pipeline Generation Input">
              <div style={styles.pipelineSteps}>
                {result.pipeline_generation_input.pipeline_steps?.map((step, i) => (
                  <div key={i} style={styles.pipelineStep}>
                    <span style={styles.stepNumber}>{i + 1}</span>
                    <span>{step}</span>
                  </div>
                ))}
              </div>
              {result.pipeline_generation_input.required_components && (
                <div style={{ marginTop: '8px' }}>
                  <div>Data Cleaner: {result.pipeline_generation_input.required_components.data_cleaner ? 'Yes' : 'No'}</div>
                  <div>Featurizer: {result.pipeline_generation_input.required_components.featurizer ? 'Yes' : 'No'}</div>
                  <div>Model Trainer: {result.pipeline_generation_input.required_components.model_trainer ? 'Yes' : 'No'}</div>
                  <div>Evaluator: {result.pipeline_generation_input.required_components.evaluator ? 'Yes' : 'No'}</div>
                </div>
              )}
            </Section>
          )}

          {/* LLM Reasoning */}
          {result.llm_reasoning_summary && (
            <Section title="LLM Reasoning Summary">
              <div style={styles.reasoning}>{result.llm_reasoning_summary}</div>
            </Section>
          )}

          {/* Warnings */}
          {result.planning_warnings && result.planning_warnings.length > 0 && (
            <div style={styles.warningSection}>
              <strong style={{ color: '#e65100' }}>Planning Warnings:</strong>
              {result.planning_warnings.map((w, i) => (
                <div key={i} style={styles.warningItem}>⚠ {w}</div>
              ))}
            </div>
          )}

          {/* Assumptions */}
          {result.planning_assumptions && result.planning_assumptions.length > 0 && (
            <div style={styles.assumptionSection}>
              <strong style={{ color: '#1565c0' }}>Planning Assumptions:</strong>
              {result.planning_assumptions.map((a, i) => (
                <div key={i} style={styles.assumptionItem}>• {a}</div>
              ))}
            </div>
          )}

          {/* Full JSON */}
          <div style={styles.jsonSection}>
            <strong>Full Result (JSON):</strong>
            <pre style={styles.pre}>{JSON.stringify(result, null, 2)}</pre>
          </div>
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
  pipelineSteps: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
  },
  pipelineStep: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    fontSize: '13px',
  },
  stepNumber: {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    backgroundColor: '#1976d2',
    color: '#fff',
    fontSize: '11px',
    fontWeight: 600,
  },
  reasoning: {
    fontSize: '13px',
    fontStyle: 'italic',
    color: '#555',
    lineHeight: '1.5',
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
  assumptionSection: {
    marginTop: '8px',
    padding: '10px',
    backgroundColor: '#e3f2fd',
    borderRadius: '4px',
    border: '1px solid #90caf9',
    fontSize: '13px',
  },
  assumptionItem: {
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
    maxHeight: '400px',
  },
};

export default WorkflowPlanPanel;
