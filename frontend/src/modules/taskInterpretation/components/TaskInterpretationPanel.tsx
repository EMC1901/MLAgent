import React, { useState } from 'react';
import { createInterpretation, rerunInterpretation } from '../../../api/taskInterpretationApi';
import { TaskInterpretationResponse } from '../types';

interface TaskInterpretationPanelProps {
  taskId: string;
  initialResult?: TaskInterpretationResponse;
}

const TaskInterpretationPanel: React.FC<TaskInterpretationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskInterpretationResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const handleRunInterpretation = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await createInterpretation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to run interpretation.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await rerunInterpretation(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-run interpretation.');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'interpreted': return '#4caf50';
      case 'interpreted_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      case 'blocked': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>LLM Task Interpretation</h3>
      <p style={styles.description}>
        Run LLM-based semantic interpretation on the submitted task specification.
      </p>

      <div style={styles.buttonRow}>
        <button
          onClick={handleRunInterpretation}
          disabled={loading}
          style={styles.runButton}
        >
          {loading ? 'Running...' : 'Run Interpretation'}
        </button>
        <button
          onClick={handleRerun}
          disabled={loading}
          style={styles.rerunButton}
        >
          {loading ? 'Running...' : 'Re-run Interpretation'}
        </button>
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Interpretation Result</h4>

          <div style={styles.field}>
            <strong>Interpretation ID:</strong> {result.interpretation_id}
          </div>
          <div style={styles.field}>
            <strong>Status:</strong>{' '}
            <span style={{ color: getStatusColor(result.status), fontWeight: 600 }}>
              {result.status}
            </span>
          </div>
          <div style={styles.field}>
            <strong>Task Type:</strong> {result.interpreted_task_type}
          </div>
          <div style={styles.field}>
            <strong>Input Modality:</strong> {result.interpreted_input_modality}
          </div>
          <div style={styles.field}>
            <strong>Material Domain:</strong> {result.interpreted_material_domain}
          </div>
          <div style={styles.field}>
            <strong>Confidence Score:</strong> {result.confidence_score}
          </div>

          {result.interpreted_prediction_target && (
            <div style={styles.section}>
              <strong>Prediction Target:</strong>
              <div style={styles.indent}>
                Normalized: {result.interpreted_prediction_target.normalized_target}<br />
                Category: {result.interpreted_prediction_target.target_category}<br />
                Unit: {result.interpreted_prediction_target.target_unit}<br />
                Description: {result.interpreted_prediction_target.target_description}
              </div>
            </div>
          )}

          {result.modeling_intent && (
            <div style={styles.section}>
              <strong>Modeling Intent:</strong>
              <div style={styles.indent}>
                Primary Goal: {result.modeling_intent.primary_goal}<br />
                Secondary Goals: {result.modeling_intent.secondary_goals?.join(', ')}<br />
                Optimization: {result.modeling_intent.optimization_direction}<br />
                Preferred Metric: {result.modeling_intent.preferred_metric}
              </div>
            </div>
          )}

          {result.dataset_intent && (
            <div style={styles.section}>
              <strong>Dataset Intent:</strong>
              <div style={styles.indent}>
                Reference: {result.dataset_intent.dataset_reference}<br />
                Expected Input: {result.dataset_intent.expected_input_columns?.join(', ')}<br />
                Target Column: {result.dataset_intent.expected_target_column}<br />
                Requires Structure File: {result.dataset_intent.requires_structure_file ? 'Yes' : 'No'}
              </div>
            </div>
          )}

          {result.planning_hint && (
            <div style={styles.section}>
              <strong>Planning Hint:</strong>
              <div style={styles.indent}>
                Task Family: {result.planning_hint.task_family}<br />
                Input Representation: {result.planning_hint.input_representation}<br />
                Feature Engineering: {result.planning_hint.requires_feature_engineering ? 'Yes' : 'No'}<br />
                Interpretability Required: {result.planning_hint.requires_model_interpretability ? 'Yes' : 'No'}
              </div>
            </div>
          )}

          {result.constraint_interpretation && (
            <div style={styles.section}>
              <strong>Constraint Interpretation:</strong>
              <div style={styles.indent}>
                {result.constraint_interpretation.hard_constraints && result.constraint_interpretation.hard_constraints.length > 0 && (
                  <>Hard: {result.constraint_interpretation.hard_constraints.join(', ')}<br /></>
                )}
                {result.constraint_interpretation.soft_constraints && result.constraint_interpretation.soft_constraints.length > 0 && (
                  <>Soft: {result.constraint_interpretation.soft_constraints.join(', ')}<br /></>
                )}
                {result.constraint_interpretation.potential_conflicts && result.constraint_interpretation.potential_conflicts.length > 0 && (
                  <>Conflicts: {result.constraint_interpretation.potential_conflicts.join(', ')}</>
                )}
              </div>
            </div>
          )}

          {result.recommended_defaults && (
            <div style={styles.section}>
              <strong>Recommended Defaults:</strong>
              <div style={styles.indent}>
                Metric: {result.recommended_defaults.evaluation_metric}<br />
                Validation: {result.recommended_defaults.validation_strategy}<br />
                Baseline: {result.recommended_defaults.baseline_requirement ? 'Yes' : 'No'}
              </div>
            </div>
          )}

          {result.ambiguities && result.ambiguities.length > 0 && (
            <div style={styles.section}>
              <strong style={{ color: '#e65100' }}>Ambiguities:</strong>
              {result.ambiguities.map((a, i) => (
                <div key={i} style={styles.indent}>
                  [{a.severity}] {a.field}: {a.message}
                </div>
              ))}
            </div>
          )}

          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.section}>
              <strong style={{ color: '#e65100' }}>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={styles.indent}>- {w}</div>
              ))}
            </div>
          )}

          {result.llm_reasoning_summary && (
            <div style={styles.section}>
              <strong>LLM Reasoning:</strong>
              <div style={styles.indent}>{result.llm_reasoning_summary}</div>
            </div>
          )}

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
  field: {
    marginBottom: '6px',
    fontSize: '14px',
  },
  section: {
    marginTop: '10px',
    marginBottom: '6px',
    fontSize: '14px',
  },
  indent: {
    marginLeft: '16px',
    marginTop: '4px',
    fontSize: '13px',
    color: '#555',
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

export default TaskInterpretationPanel;
