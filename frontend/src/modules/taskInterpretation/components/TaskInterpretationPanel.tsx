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
  const [activeTab, setActiveTab] = useState<string>('interpretation');

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

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const renderInterpretation = () => {
    if (!result) return null;
    return (
      <div>
        <div style={s.card}>
          <h4 style={s.cardTitle}>Interpretation Result</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Interpretation ID:</strong> {result.interpretation_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={result.status} color={getStatusColor(result.status)} />
            </div>
            <div style={s.field}><strong>Task Type:</strong> {result.interpreted_task_type}</div>
            <div style={s.field}><strong>Input Modality:</strong> {result.interpreted_input_modality}</div>
            <div style={s.field}><strong>Material Domain:</strong> {result.interpreted_material_domain}</div>
            <div style={s.field}><strong>Confidence Score:</strong> {result.confidence_score}</div>
          </div>
        </div>

        {result.interpreted_prediction_target && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Prediction Target</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Normalized:</strong> {result.interpreted_prediction_target.normalized_target}</div>
              <div style={s.field}><strong>Category:</strong> {result.interpreted_prediction_target.target_category}</div>
              <div style={s.field}><strong>Unit:</strong> {result.interpreted_prediction_target.target_unit}</div>
              <div style={s.field}><strong>Description:</strong> {result.interpreted_prediction_target.target_description}</div>
            </div>
          </div>
        )}

        {result.modeling_intent && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Modeling Intent</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Primary Goal:</strong> {result.modeling_intent.primary_goal}</div>
              <div style={s.field}><strong>Secondary Goals:</strong> {result.modeling_intent.secondary_goals?.join(', ')}</div>
              <div style={s.field}><strong>Optimization:</strong> {result.modeling_intent.optimization_direction}</div>
              <div style={s.field}><strong>Preferred Metric:</strong> {result.modeling_intent.preferred_metric}</div>
            </div>
          </div>
        )}

        {result.dataset_intent && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Dataset Intent</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Reference:</strong> {result.dataset_intent.dataset_reference}</div>
              <div style={s.field}><strong>Expected Input:</strong> {result.dataset_intent.expected_input_columns?.join(', ')}</div>
              <div style={s.field}><strong>Target Column:</strong> {result.dataset_intent.expected_target_column}</div>
              <div style={s.field}><strong>Requires Structure File:</strong> {result.dataset_intent.requires_structure_file ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}

        {result.planning_hint && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Planning Hint</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Task Family:</strong> {result.planning_hint.task_family}</div>
              <div style={s.field}><strong>Input Representation:</strong> {result.planning_hint.input_representation}</div>
              <div style={s.field}><strong>Feature Engineering:</strong> {result.planning_hint.requires_feature_engineering ? 'Yes' : 'No'}</div>
              <div style={s.field}><strong>Interpretability Required:</strong> {result.planning_hint.requires_model_interpretability ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}

        {result.constraint_interpretation && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Constraint Interpretation</h4>
            {result.constraint_interpretation.hard_constraints && result.constraint_interpretation.hard_constraints.length > 0 && (
              <div style={s.field}><strong>Hard:</strong> {result.constraint_interpretation.hard_constraints.join(', ')}</div>
            )}
            {result.constraint_interpretation.soft_constraints && result.constraint_interpretation.soft_constraints.length > 0 && (
              <div style={s.field}><strong>Soft:</strong> {result.constraint_interpretation.soft_constraints.join(', ')}</div>
            )}
            {result.constraint_interpretation.potential_conflicts && result.constraint_interpretation.potential_conflicts.length > 0 && (
              <div style={s.field}><strong>Conflicts:</strong> {result.constraint_interpretation.potential_conflicts.join(', ')}</div>
            )}
          </div>
        )}

        {result.recommended_defaults && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Recommended Defaults</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Metric:</strong> {result.recommended_defaults.evaluation_metric}</div>
              <div style={s.field}><strong>Validation:</strong> {result.recommended_defaults.validation_strategy}</div>
              <div style={s.field}><strong>Baseline Required:</strong> {result.recommended_defaults.baseline_requirement ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}

        {result.ambiguities && result.ambiguities.length > 0 && (
          <div style={s.warningBox}>
            <strong>Ambiguities:</strong>
            <ul style={s.list}>
              {result.ambiguities.map((a, i) => (
                <li key={i}>[{a.severity}] {a.field}: {a.message}</li>
              ))}
            </ul>
          </div>
        )}

        {result.warnings && result.warnings.length > 0 && (
          <div style={s.warningBox}>
            <strong>Warnings:</strong>
            <ul style={s.list}>
              {result.warnings.map((w, i) => <li key={i}>{w}</li>)}
            </ul>
          </div>
        )}

        {result.llm_reasoning_summary && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>AI Reasoning</h4>
            <p style={s.summaryText}>{result.llm_reasoning_summary}</p>
          </div>
        )}
      </div>
    );
  };

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

  const tabs = [
    { id: 'interpretation', label: 'Interpretation' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>AI Task Interpretation</h3>
      <p style={s.description}>
        Run AI-based semantic interpretation on the submitted task specification.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRunInterpretation} disabled={loading} style={s.runButton}>
          {loading ? 'Running...' : 'Run Interpretation'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Interpretation'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Interpretation Result</h4>

          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          <div style={s.tabContent}>
            {activeTab === 'interpretation' && renderInterpretation()}
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
    padding: '10px 20px', backgroundColor: '#1976d2', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  rerunButton: {
    padding: '10px 20px', backgroundColor: '#f57c00', color: '#fff',
    border: 'none', borderRadius: '4px', fontSize: '14px', fontWeight: 600, cursor: 'pointer',
  },
  errorBox: {
    padding: '12px', backgroundColor: '#ffebee', border: '1px solid #f44336',
    borderRadius: '4px', color: '#c62828', marginBottom: '16px',
  },
  resultBox: {
    padding: '16px', backgroundColor: '#fff', border: '1px solid #e0e0e0',
    borderRadius: '8px',
  },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
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
    overflowX: 'auto' as const,
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '8px' },
  field: { fontSize: '14px' },
  summaryText: { marginTop: '8px', color: '#333', fontSize: '14px', lineHeight: 1.5 },
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
  },
};

export default TaskInterpretationPanel;
