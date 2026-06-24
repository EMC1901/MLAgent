import React, { useState, useCallback } from 'react';
import { Button, Space, Tabs, Card } from 'antd';
import {
  createFeaturePreprocessing,
  rerunFeaturePreprocessing,
} from '../../../api/featurePreprocessingApi';
import { FeaturePreprocessingResponse } from '../types';
import { pipelineAccent } from '../../../theme/pipelineColors';
import { PanelContainer, WarningBox, ErrorBox, JsonViewer } from '../../../components/shared';
import PlanTab from './PlanTab';
import ExecutionTab from './ExecutionTab';

interface FeaturePreprocessingPanelProps {
  taskId: string;
  initialResult?: FeaturePreprocessingResponse;
}

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

  return (
    <PanelContainer
      title="Data Preprocessing (AI-Guided)"
      description="Two-phase fold-safe preprocessing: global operations (analysis, filtering, leakage detection) run once on full data; fold operations (imputation, scaling, transforms) are fit inside each CV fold on train data only — preventing data leakage."
      accentColor={pipelineAccent.featurePreprocessing}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRun} loading={loading}>
          Run Data Preprocessing
        </Button>
        <Button onClick={handleRerun} loading={loading}>
          Re-run Data Preprocessing
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
                key: 'plan',
                label: 'Preprocessing Plan',
                children: <PlanTab result={result} />,
              },
              {
                key: 'execution',
                label: 'Execution & Quality',
                children: <ExecutionTab result={result} />,
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
            <ErrorBox message={result.errors.join('; ')} style={{ marginTop: 16 }} />
          )}
        </>
      )}
    </PanelContainer>
  );
};

export default FeaturePreprocessingPanel;
