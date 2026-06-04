import React, { useState, useCallback } from 'react';
import {
  createFeaturePreprocessing,
  rerunFeaturePreprocessing,
} from '../../../api/featurePreprocessingApi';
import { FeaturePreprocessingResponse } from '../types';
import { STATUS_COLORS } from '../constants';
import { sharedStyles as s } from './styles';
import PlanTab from './PlanTab';
import ExecutionTab from './ExecutionTab';

interface FeaturePreprocessingPanelProps {
  taskId: string;
  initialResult?: FeaturePreprocessingResponse;
}

const TabButton: React.FC<{ tabId: string; label: string; activeTab: string; onSelect: (id: string) => void }> =
  React.memo(({ tabId, label, activeTab, onSelect }) => (
    <button
      onClick={() => onSelect(tabId)}
      style={{
        ...s.tabButton,
        backgroundColor: activeTab === tabId ? '#1976d2' : '#e0e0e0',
        color: activeTab === tabId ? '#fff' : '#333',
      }}
    >
      {label}
    </button>
  ));

TabButton.displayName = 'TabButton';

const FeaturePreprocessingPanel: React.FC<FeaturePreprocessingPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FeaturePreprocessingResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('plan');

  const extractErrorMessage = (err: unknown): string => {
    const detail = (err as { response?: { data?: { detail?: unknown } } })?.response?.data?.detail;
    if (typeof detail === 'object' && detail !== null) {
      return (detail as { message?: string }).message ?? JSON.stringify(detail);
    }
    if (typeof detail === 'string') return detail;
    return (err as { message?: string })?.message || 'Failed to run data preprocessing.';
  };

  const handleRun = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFeaturePreprocessing(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  const handleRerun = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFeaturePreprocessing(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: unknown) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  const getStatusColor = (status: string): string => {
    const colorMap: Record<string, string> = {
      preprocessed: '#4caf50',
      preprocessed_with_warning: '#ff9800',
      failed: '#f44336',
      blocked: '#9e9e9e',
    };
    return colorMap[status] || '#9e9e9e';
  };

  const handleTabSelect = useCallback((id: string) => setActiveTab(id), []);

  const tabs = [
    { id: 'plan', label: 'Preprocessing Plan' },
    { id: 'execution', label: 'Execution & Quality' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Data Preprocessing (AI-Guided)</h3>
      <p style={s.description}>
        Two-phase fold-safe preprocessing: global operations (analysis, filtering,
        leakage detection) run once on full data; fold operations (imputation, scaling,
        transforms) are fit inside each CV fold on train data only — preventing data leakage.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleRun} disabled={loading} style={s.runButton}>
          {loading ? 'Running...' : 'Run Data Preprocessing'}
        </button>
        <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
          {loading ? 'Running...' : 'Re-run Data Preprocessing'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Data Preprocessing Result</h4>

          <div style={s.tabBar}>
            {tabs.map(t => (
              <TabButton key={t.id} tabId={t.id} label={t.label} activeTab={activeTab} onSelect={handleTabSelect} />
            ))}
          </div>

          <div style={s.tabContent}>
            {activeTab === 'plan' && <PlanTab result={result} />}
            {activeTab === 'execution' && <ExecutionTab result={result} />}
            {activeTab === 'json' && (
              <div style={s.card}>
                <h4 style={s.cardTitle}>Full JSON</h4>
                <pre style={s.json}>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div style={{ ...s.warningBox, marginTop: '16px' }}>
              <strong>Warnings:</strong>
              {result.warnings.map((w, i) => (
                <div key={i} style={{ marginTop: '4px' }}>{w}</div>
              ))}
            </div>
          )}

          {result.errors && result.errors.length > 0 && (
            <div style={{ ...s.errorBox, marginTop: '16px', marginBottom: '0' }}>
              <strong>Errors:</strong>
              {result.errors.map((e, i) => (
                <div key={i} style={{ marginTop: '4px' }}>{e}</div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FeaturePreprocessingPanel;
