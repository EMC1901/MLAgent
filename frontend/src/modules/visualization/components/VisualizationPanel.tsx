import React, { useState, useEffect } from 'react';
import { Button, Space, Card, Spin, Tabs, Modal, Descriptions, Select } from 'antd';
import { getVisualizationData } from '../../../api/visualizationApi';
import { VisualizationData } from '../types';
import { PUBLICATION_EXPORT_SIZES, TASK_TYPE_LABELS } from '../constants';

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
import PublicationChartFrame from './PublicationChartFrame';
import {
  PanelContainer,
  StatusBadge,
  ErrorBox,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface VisualizationPanelProps {
  taskId: string;
  initialResult?: VisualizationData;
}

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisualizationData | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('featureAnalysis');
  const [activeFeatSubTab, setActiveFeatSubTab] = useState<string>('correlationHeatmap');
  const [activePerfSubTab, setActivePerfSubTab] = useState<string>('predictedVsActual');
  const [fullscreenChart, setFullscreenChart] = useState<{
    title: string;
    children: React.ReactNode;
  } | null>(null);
  const [exportSize, setExportSize] = useState<'single' | 'double'>('double');
  const [exportDpi, setExportDpi] = useState<number>(600);

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

  const fa = result?.feature_analysis;
  const mp = result?.model_performance;
  const rawTaskType = result?.task_type || 'regression';
  const taskType = rawTaskType.includes('classif')
    ? 'classification'
    : rawTaskType.includes('regress')
    ? 'regression'
    : rawTaskType;
  const isClassification = taskType === 'classification';

  const featSubTabsBase = [
    { id: 'correlationHeatmap', label: 'Correlation Heatmap', avail: !!fa?.correlation_matrix },
    { id: 'targetCorrelation', label: 'Target Correlations', avail: !!fa?.target_correlations?.length },
    { id: 'featureImportance', label: 'Feature Importance', avail: !!fa?.feature_importance?.length },
    { id: 'descriptorDist', label: 'Descriptor Distribution', avail: !!fa?.descriptor_distribution?.length },
  ];

  const featSubTabs = featSubTabsBase.filter((t) => t.avail);

  const modelPerfSubTabsBase = [
    ...(!isClassification
      ? [
          { id: 'predictedVsActual', label: 'Predicted vs Actual', avail: !!mp?.predicted_vs_actual },
          { id: 'residualPlot', label: 'Residual Plot', avail: !!mp?.residual_plot },
        ]
      : []),
    { id: 'trainTest', label: 'Validation by Fold', avail: !!mp?.train_test_comparison },
    { id: 'cvBoxPlot', label: 'CV Distribution', avail: !!mp?.cross_validation_box_plot },
    ...(isClassification
      ? [
          { id: 'confusionMatrix', label: 'Confusion Matrix', avail: !!mp?.confusion_matrix },
          { id: 'rocCurve', label: 'ROC / PR', avail: !!(mp?.roc_curve || mp?.pr_curve) },
        ]
      : []),
  ];

  const modelPerfSubTabs = modelPerfSubTabsBase.filter((t) => t.avail);

  useEffect(() => {
    const visibleIds = featSubTabsBase.filter((t) => t.avail).map((t) => t.id);
    if (visibleIds.length > 0 && !visibleIds.includes(activeFeatSubTab)) {
      setActiveFeatSubTab(visibleIds[0]);
    }
  }, [fa, activeFeatSubTab]);

  useEffect(() => {
    const visibleIds = modelPerfSubTabsBase.filter((t) => t.avail).map((t) => t.id);
    if (visibleIds.length > 0 && !visibleIds.includes(activePerfSubTab)) {
      setActivePerfSubTab(visibleIds[0]);
    }
  }, [taskType, mp, activePerfSubTab]);

  const exportSettings = {
    dpi: exportDpi,
    widthMm: PUBLICATION_EXPORT_SIZES[exportSize].widthMm,
  };

  const ChartWrapper: React.FC<{ title: string; chartKey: string; children: React.ReactNode }> = ({
    title,
    chartKey,
    children,
  }) => (
    <PublicationChartFrame
      title={title}
      filenameBase={`${taskId}_${chartKey}`}
      exportSettings={exportSettings}
      onFullscreen={setFullscreenChart}
    >
      {children}
    </PublicationChartFrame>
  );

  const renderSubTabBar = (
    tabs: { id: string; label: string }[],
    activeId: string,
    onSelect: (id: string) => void
  ) => (
    <Space wrap style={{ marginBottom: 16 }}>
      {tabs.map((t) => (
        <Button
          key={t.id}
          size="small"
          type={activeId === t.id ? 'primary' : 'default'}
          onClick={() => onSelect(t.id)}
        >
          {t.label}
        </Button>
      ))}
    </Space>
  );

  const featureAnalysisContent = (
    <>
      {featSubTabs.length === 0 ? (
        <EmptyState description="No feature analysis charts available. Run interpretability analysis with correlation and feature importance outputs." />
      ) : (
        renderSubTabBar(featSubTabs, activeFeatSubTab, setActiveFeatSubTab)
      )}

      {featSubTabs.length > 0 && activeFeatSubTab === 'correlationHeatmap' && (
        <ChartWrapper title="Feature Correlation Heatmap" chartKey="feature_correlation_heatmap">
          <FeatureCorrelationHeatmap data={fa?.correlation_matrix ?? null} />
        </ChartWrapper>
      )}
      {featSubTabs.length > 0 && activeFeatSubTab === 'targetCorrelation' && (
        <ChartWrapper title="Pearson / Spearman Target Correlations" chartKey="target_correlations">
          <TargetCorrelationChart data={fa?.target_correlations || []} />
        </ChartWrapper>
      )}
      {featSubTabs.length > 0 && activeFeatSubTab === 'featureImportance' && (
        <ChartWrapper title="Feature Importance" chartKey="feature_importance">
          <FeatureImportanceChart data={fa?.feature_importance || []} />
        </ChartWrapper>
      )}
      {featSubTabs.length > 0 && activeFeatSubTab === 'descriptorDist' && (
        <ChartWrapper title="Descriptor Distribution" chartKey="descriptor_distribution">
          <DescriptorDistributionChart data={fa?.descriptor_distribution || []} />
        </ChartWrapper>
      )}
    </>
  );

  const modelPerformanceContent = (
    <>
      {modelPerfSubTabs.length === 0 ? (
        <EmptyState description="No model performance charts available. Run metric evaluation and pipeline execution first." />
      ) : (
        renderSubTabBar(modelPerfSubTabs, activePerfSubTab, setActivePerfSubTab)
      )}

      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'predictedVsActual' && (
        <ChartWrapper title="Prediction vs Actual" chartKey="predicted_vs_actual">
          <PredictedVsActualChart
            data={mp?.predicted_vs_actual ?? null}
            modelId={mp?.model_id ?? null}
            modelFamily={mp?.model_family ?? null}
            modelTrialId={mp?.model_trial_id ?? null}
          />
        </ChartWrapper>
      )}
      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'residualPlot' && (
        <>
          <ChartWrapper title="Residuals Plot" chartKey="residuals_plot">
            <ResidualPlotChart data={mp?.residual_plot ?? null} variant="scatter" />
          </ChartWrapper>
          <ChartWrapper title="Residuals Distribution" chartKey="residuals_distribution">
            <ResidualPlotChart data={mp?.residual_plot ?? null} variant="distribution" />
          </ChartWrapper>
        </>
      )}
      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'trainTest' && (
        <ChartWrapper title="Validation Metric by Fold" chartKey="validation_metric_by_fold">
          <TrainTestComparisonChart data={mp?.train_test_comparison ?? null} />
        </ChartWrapper>
      )}
      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'cvBoxPlot' && (
        <ChartWrapper title="Cross-Validation Metric Distribution" chartKey="cv_metric_distribution">
          <CrossValidationBoxPlotChart data={mp?.cross_validation_box_plot ?? null} />
        </ChartWrapper>
      )}
      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'confusionMatrix' && (
        <ChartWrapper title="Confusion Matrix" chartKey="confusion_matrix">
          <ConfusionMatrixChart data={mp?.confusion_matrix ?? null} taskType={taskType} />
        </ChartWrapper>
      )}
      {modelPerfSubTabs.length > 0 && activePerfSubTab === 'rocCurve' && (
        <ChartWrapper title="ROC / PR Curves" chartKey="roc_pr_curves">
          <ROCCurveChart rocData={mp?.roc_curve ?? null} prData={mp?.pr_curve ?? null} taskType={taskType} />
        </ChartWrapper>
      )}
    </>
  );

  const tabItems = [
    { key: 'featureAnalysis', label: 'Feature Analysis', children: result ? featureAnalysisContent : null },
    { key: 'modelPerformance', label: 'Model Performance', children: result ? modelPerformanceContent : null },
  ];

  return (
    <PanelContainer
      title="Visualization & Analysis Charts"
      description="Interactive charts for model interpretability and performance analysis. Data is aggregated from interpretability analysis, metric evaluation, and dataset profiling results."
      accentColor={pipelineAccent.visualization}
    >
      <Space style={{ marginBottom: 16 }} wrap>
        <Button type="primary" onClick={handleLoad} loading={loading}>
          {loading ? 'Loading...' : 'Load Charts'}
        </Button>
        <Select
          size="small"
          value={exportSize}
          onChange={setExportSize}
          options={[
            { value: 'double', label: PUBLICATION_EXPORT_SIZES.double.label },
            { value: 'single', label: PUBLICATION_EXPORT_SIZES.single.label },
          ]}
          style={{ width: 150 }}
          aria-label="Export figure width"
        />
        <Select
          size="small"
          value={exportDpi}
          onChange={setExportDpi}
          options={[
            { value: 600, label: 'PNG 600 dpi' },
            { value: 300, label: 'PNG 300 dpi' },
          ]}
          style={{ width: 130 }}
          aria-label="Export PNG DPI"
        />
      </Space>
      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {result && (
          <>
            <Card size="small" style={{ marginBottom: 16 }}>
              <Descriptions column={3} size="small">
                <Descriptions.Item label="Task Type">
                  <StatusBadge label={TASK_TYPE_LABELS[taskType] || taskType} />
                </Descriptions.Item>
                <Descriptions.Item label="Correlations">
                  {fa?.target_correlations?.length || 0} features
                </Descriptions.Item>
                <Descriptions.Item label="Feature Importance">
                  {fa?.feature_importance?.length || 0} features
                </Descriptions.Item>
              </Descriptions>
            </Card>
            <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />
          </>
        )}

        {!result && !error && !loading && (
          <EmptyState description="No visualization data yet. Click &quot;Load Charts&quot; to fetch analysis charts." />
        )}
      </Spin>

      <Modal
        title={fullscreenChart?.title}
        open={!!fullscreenChart}
        onCancel={() => setFullscreenChart(null)}
        footer={null}
        width="95vw"
        style={{ top: 20 }}
        styles={{ body: { maxHeight: '85vh', overflow: 'auto', padding: 16 } }}
        destroyOnClose
      >
        {fullscreenChart?.children}
      </Modal>
    </PanelContainer>
  );
};

export default VisualizationPanel;
