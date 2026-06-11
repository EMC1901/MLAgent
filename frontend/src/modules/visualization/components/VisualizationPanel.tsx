import React, { useState, useEffect } from 'react';
import { getVisualizationData } from '../../../api/visualizationApi';
import { VisualizationData } from '../types';
import { TASK_TYPE_LABELS } from '../constants';

import FeatureCorrelationHeatmap from './charts/FeatureCorrelationHeatmap';
import TargetCorrelationChart from './charts/TargetCorrelationChart';
import FeatureImportanceChart from './charts/FeatureImportanceChart';
import DescriptorDistributionChart from './charts/DescriptorDistributionChart';
import PredictedVsActualChart from './charts/PredictedVsActualChart';
import ResidualPlotChart from './charts/ResidualPlotChart';
import TrainTestComparisonChart from './charts/TrainTestComparisonChart';
import CrossValidationBoxPlotChart from './charts/CrossValidationBoxPlotChart';
import ConfusionMatrixChart from './charts/ConfusionMatrixChart';
import ROCCurveChart from './charts/ROCCurveChart';

interface VisualizationPanelProps {
  taskId: string;
  initialResult?: VisualizationData;
}

const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
  <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
);

interface FullscreenState {
  title: string;
  children: React.ReactNode;
}

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisualizationData | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('featureAnalysis');
  const [activeFeatSubTab, setActiveFeatSubTab] = useState<string>('correlationHeatmap');
  const [activePerfSubTab, setActivePerfSubTab] = useState<string>('predictedVsActual');
  const [fullscreen, setFullscreen] = useState<FullscreenState | null>(null);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && fullscreen) setFullscreen(null);
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [fullscreen]);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await getVisualizationData(taskId);
      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to load visualization data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!initialResult && !result && !loading) {
      handleLoad();
    }
  }, [taskId]);

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

  const renderSubTab = (tabId: string, label: string, isActive: boolean, onClick: () => void) => (
    <button
      key={tabId}
      onClick={onClick}
      style={{
        padding: '4px 12px',
        border: 'none',
        borderRadius: '12px',
        fontSize: '12px',
        fontWeight: 600,
        cursor: 'pointer',
        backgroundColor: isActive ? '#7b1fa2' : '#e0e0e0',
        color: isActive ? '#fff' : '#333',
      }}
    >
      {label}
    </button>
  );

  const fa = result?.feature_analysis;
  const mp = result?.model_performance;
  const rawTaskType = result?.task_type || 'regression';
  const taskType = rawTaskType.includes('classif') ? 'classification'
    : rawTaskType.includes('regress') ? 'regression'
    : rawTaskType;

  const featSubTabs = [
    { id: 'correlationHeatmap', label: 'Correlation Heatmap' },
    { id: 'targetCorrelation', label: 'Target Correlations' },
    { id: 'featureImportance', label: 'Feature Importance' },
    { id: 'descriptorDist', label: 'Descriptor Distribution' },
  ];

  const ChartCard: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
    <div style={s.card}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <h4 style={{ ...s.cardTitle, margin: 0 }}>{title}</h4>
        <button
          onClick={() => setFullscreen({ title, children })}
          title="Fullscreen"
          style={{
            padding: '4px 8px', border: '1px solid #ccc', borderRadius: '4px',
            backgroundColor: '#fff', cursor: 'pointer', fontSize: 14, lineHeight: 1,
          }}
        >
          &#x26F6;
        </button>
      </div>
      {children}
    </div>
  );

  const isClassification = taskType === 'classification';

  const modelPerfSubTabs = [
    ...(!isClassification ? [
      { id: 'predictedVsActual', label: 'Predicted vs Actual', avail: !!mp?.predicted_vs_actual },
      { id: 'residualPlot', label: 'Residual Plot', avail: !!mp?.residual_plot },
    ] : []),
    { id: 'trainTest', label: 'Train/Test', avail: !!mp?.train_test_comparison },
    { id: 'cvBoxPlot', label: 'CV Box Plot', avail: !!mp?.cross_validation_box_plot },
    ...(isClassification ? [
      { id: 'confusionMatrix', label: 'Confusion Matrix', avail: !!mp?.confusion_matrix },
      { id: 'rocCurve', label: 'ROC / PR', avail: !!(mp?.roc_curve || mp?.pr_curve) },
    ] : []),
  ];

  // Keep active sub-tab in sync: when task type changes (e.g. data loaded),
  // switch to first visible tab if the current one is no longer available.
  useEffect(() => {
    const visibleIds = modelPerfSubTabs.filter(t => t.avail).map(t => t.id);
    if (visibleIds.length > 0 && !visibleIds.includes(activePerfSubTab)) {
      setActivePerfSubTab(visibleIds[0]);
    }
  }, [taskType, mp, activePerfSubTab]);

  return (
    <div style={s.container}>
      <h3 style={s.title}>Visualization &amp; Analysis Charts</h3>
      <p style={s.description}>
        Interactive charts for model interpretability and performance analysis. Data is aggregated
        from interpretability analysis, metric evaluation, and dataset profiling results.
      </p>

      <div style={s.buttonRow}>
        <button onClick={handleLoad} disabled={loading} style={s.runButton}>
          {loading ? 'Loading...' : 'Load Charts'}
        </button>
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {result && (
        <div style={s.resultBox}>
          {/* Summary */}
          <div style={s.fieldRow}>
            <div style={s.field}>
              <strong>Task Type: </strong>
              <Badge label={TASK_TYPE_LABELS[taskType] || taskType} color="#1976d2" />
            </div>
            <div style={s.field}>
              <strong>Correlations: </strong>
              <span>{fa?.target_correlations?.length || 0} features</span>
            </div>
            <div style={s.field}>
              <strong>Feature Importance: </strong>
              <span>{fa?.feature_importance?.length || 0} features</span>
            </div>
          </div>

          {/* Tab navigation */}
          <div style={s.tabBar}>
            {renderTab('featureAnalysis', 'Feature Analysis')}
            {renderTab('modelPerformance', 'Model Performance')}
          </div>

          {/* Tab content */}
          <div style={s.tabContent}>
            {activeTab === 'featureAnalysis' && (
              <div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 16 }}>
                  {featSubTabs.map(t => (
                    renderSubTab(t.id, t.label, activeFeatSubTab === t.id, () => setActiveFeatSubTab(t.id))
                  ))}
                </div>

                {activeFeatSubTab === 'correlationHeatmap' && (
                  <ChartCard title="Feature Correlation Heatmap">
                    <FeatureCorrelationHeatmap data={fa?.correlation_matrix ?? null} />
                  </ChartCard>
                )}

                {activeFeatSubTab === 'targetCorrelation' && (
                  <ChartCard title="Pearson / Spearman Target Correlations">
                    <TargetCorrelationChart data={fa?.target_correlations || []} />
                  </ChartCard>
                )}

                {activeFeatSubTab === 'featureImportance' && (
                  <ChartCard title="Feature Importance">
                    <FeatureImportanceChart data={fa?.feature_importance || []} />
                  </ChartCard>
                )}

                {activeFeatSubTab === 'descriptorDist' && (
                  <ChartCard title="Descriptor Distribution">
                    <DescriptorDistributionChart data={fa?.descriptor_distribution || []} />
                  </ChartCard>
                )}
              </div>
            )}

            {activeTab === 'modelPerformance' && (
              <div>
                {/* Sub-tabs */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 16 }}>
                  {modelPerfSubTabs.filter(t => t.avail).map(t => (
                    renderSubTab(t.id, t.label, activePerfSubTab === t.id, () => setActivePerfSubTab(t.id))
                  ))}
                </div>

                {activePerfSubTab === 'predictedVsActual' && (
                  <ChartCard title="Predicted vs Actual">
                    <PredictedVsActualChart
                      data={mp?.predicted_vs_actual ?? null}
                      modelId={mp?.model_id ?? null}
                      modelFamily={mp?.model_family ?? null}
                      modelTrialId={mp?.model_trial_id ?? null}
                    />
                  </ChartCard>
                )}

                {activePerfSubTab === 'residualPlot' && (
                  <ChartCard title="Residual Plot">
                    <ResidualPlotChart data={mp?.residual_plot ?? null} />
                  </ChartCard>
                )}

                {activePerfSubTab === 'trainTest' && (
                  <ChartCard title="Train / Test Comparison (by fold)">
                    <TrainTestComparisonChart data={mp?.train_test_comparison ?? null} />
                  </ChartCard>
                )}

                {activePerfSubTab === 'cvBoxPlot' && (
                  <ChartCard title="Cross-Validation Distribution">
                    <CrossValidationBoxPlotChart data={mp?.cross_validation_box_plot ?? null} />
                  </ChartCard>
                )}

                {activePerfSubTab === 'confusionMatrix' && (
                  <ChartCard title="Confusion Matrix">
                    <ConfusionMatrixChart data={mp?.confusion_matrix ?? null} taskType={taskType} />
                  </ChartCard>
                )}

                {activePerfSubTab === 'rocCurve' && (
                  <ChartCard title="ROC / PR Curves">
                    <ROCCurveChart rocData={mp?.roc_curve ?? null} prData={mp?.pr_curve ?? null} taskType={taskType} />
                  </ChartCard>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Fullscreen overlay */}
      {fullscreen && (
        <div style={s.fullscreenOverlay} onClick={() => setFullscreen(null)}>
          <div style={s.fullscreenContent} onClick={e => e.stopPropagation()}>
            <div style={s.fullscreenHeader}>
              <h4 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>{fullscreen.title}</h4>
              <button
                onClick={() => setFullscreen(null)}
                style={s.fullscreenClose}
                title="Close (Esc)"
              >
                ✕
              </button>
            </div>
            <div style={s.fullscreenBody}>
              {fullscreen.children}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


/* ---- Styles ---- */

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
    padding: '10px 20px', backgroundColor: '#7b1fa2', color: '#fff',
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
  fieldRow: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' },
  field: { fontSize: '14px' },
  badge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '12px',
    color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px',
  },
  tabBar: { display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '16px' },
  tabButton: {
    padding: '6px 14px', border: 'none', borderRadius: '16px',
    fontSize: '13px', fontWeight: 600, cursor: 'pointer',
  },
  tabContent: { minHeight: '200px', maxHeight: '65vh', overflowY: 'auto' as const },
  card: {
    padding: '12px', backgroundColor: '#f5f5f5', borderRadius: '6px',
    marginBottom: '12px', border: '1px solid #e0e0e0',
  },
  cardTitle: { margin: '0 0 10px 0', fontSize: '15px', fontWeight: 600 },
  fullscreenOverlay: {
    position: 'fixed' as const, top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.7)', zIndex: 9999,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  },
  fullscreenContent: {
    backgroundColor: '#fff', borderRadius: '8px',
    width: '95vw', height: '90vh', display: 'flex', flexDirection: 'column' as const,
    overflow: 'hidden',
  },
  fullscreenHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    padding: '12px 16px', borderBottom: '1px solid #e0e0e0',
    flexShrink: 0,
  },
  fullscreenClose: {
    padding: '4px 10px', border: 'none', borderRadius: '4px',
    backgroundColor: '#f44336', color: '#fff', fontSize: '16px',
    fontWeight: 600, cursor: 'pointer',
  },
  fullscreenBody: {
    flex: 1, overflow: 'auto', padding: '16px',
  },
};

export default VisualizationPanel;
