import React, { useState } from 'react';
import { Button, Space, Card, Descriptions, Spin, Tabs } from 'antd';
import { createDatasetProfile, rerunDatasetProfile } from '../../../api/datasetProfileApi';
import { DatasetProfileResponse, DatasetFileUploadResponse } from '../types';
import FileUpload from './FileUpload';
import {
  PanelContainer,
  StatusBadge,
  WarningBox,
  ErrorBox,
  JsonViewer,
  EmptyState,
} from '../../../components/shared';
import { pipelineAccent } from '../../../theme/pipelineColors';

interface DatasetProfilePanelProps {
  taskId: string;
  initialResult?: DatasetProfileResponse;
}

const STATUS_COLORS: Record<string, string> = {
  profiled: 'success',
  profiled_with_warning: 'warning',
  failed: 'error',
  blocked: 'default',
};

const QUALITY_COLORS: Record<string, string> = {
  good: 'success',
  fair: 'warning',
  poor: 'error',
  unusable: 'default',
};

const DatasetProfilePanel: React.FC<DatasetProfilePanelProps> = ({ taskId, initialResult }) => {
  const [uploadResult, setUploadResult] = useState<DatasetFileUploadResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [profile, setProfile] = useState<DatasetProfileResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string>('profile');

  const handleUploadSuccess = (result: DatasetFileUploadResponse) => {
    setUploadResult(result);
    setError(null);
  };

  const handleRunProfiling = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await createDatasetProfile(taskId, uploadResult?.file_id);
      if (response.success) {
        setProfile(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Profiling failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await rerunDatasetProfile(taskId, uploadResult?.file_id);
      if (response.success) {
        setProfile(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Re-run failed.');
    } finally {
      setLoading(false);
    }
  };

  const renderProfile = () => {
    if (!profile) return <EmptyState description="No profile data available." />;

    return (
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        <Card size="small" title="Profile Summary">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Profile ID">{profile.dataset_profile_id}</Descriptions.Item>
            <Descriptions.Item label="Status">
              <StatusBadge label={profile.status} color={STATUS_COLORS[profile.status]} />
            </Descriptions.Item>
          </Descriptions>
        </Card>

        {profile.status === 'failed' && profile.error_message && (
          <ErrorBox message={profile.error_message} />
        )}

        {profile.dataset_source && (
          <Card size="small" title="Source">
            <p style={{ margin: 0 }}>
              {profile.dataset_source.source_type}
              {profile.dataset_source.dataset_reference && ` (${profile.dataset_source.dataset_reference})`}
            </p>
          </Card>
        )}

        {profile.dataset_schema && (
          <Card size="small" title="Schema">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Samples">{profile.dataset_schema.n_samples}</Descriptions.Item>
              <Descriptions.Item label="Columns">{profile.dataset_schema.n_columns}</Descriptions.Item>
              <Descriptions.Item label="Input Columns">
                {profile.dataset_schema.input_columns?.join(', ') || 'none'}
              </Descriptions.Item>
              <Descriptions.Item label="Target">
                {profile.dataset_schema.target_column || 'none'}
              </Descriptions.Item>
            </Descriptions>
          </Card>
        )}

        {profile.modality_check && (
          <Card size="small" title="Modality Check">
            <StatusBadge
              label={profile.modality_check.is_consistent ? 'Consistent' : 'Mismatch'}
              color={profile.modality_check.is_consistent ? 'success' : 'error'}
            />
          </Card>
        )}

        {profile.target_profile && (
          <Card size="small" title={`Target Profile (${profile.target_profile.task_type})`}>
            {profile.target_profile.task_type === 'regression' ? (
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Range">
                  {profile.target_profile.min?.toFixed(2)} – {profile.target_profile.max?.toFixed(2)}
                </Descriptions.Item>
                <Descriptions.Item label="Mean">{profile.target_profile.mean?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="Std">{profile.target_profile.std?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="Skewness">{profile.target_profile.skewness?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="Outliers">{profile.target_profile.outlier_count}</Descriptions.Item>
              </Descriptions>
            ) : (
              <Descriptions column={2} size="small">
                <Descriptions.Item label="Classes">{profile.target_profile.class_count}</Descriptions.Item>
                {profile.target_profile.is_imbalanced && (
                  <Descriptions.Item label="Warning">
                    <span style={{ color: '#e65100', fontWeight: 600 }}>Classes are imbalanced</span>
                  </Descriptions.Item>
                )}
              </Descriptions>
            )}
          </Card>
        )}

        {profile.data_quality && (
          <Card size="small" title="Data Quality">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Missing Values">
                {profile.data_quality.missing_values.total_missing}
              </Descriptions.Item>
              <Descriptions.Item label="Duplicate Rows">
                {profile.data_quality.duplicates.duplicate_rows}
              </Descriptions.Item>
            </Descriptions>
            {profile.data_quality.warnings.length > 0 && (
              <WarningBox warnings={profile.data_quality.warnings} />
            )}
            {profile.data_quality.errors.length > 0 && (
              <ErrorBox message={`${profile.data_quality.errors.length} data quality error(s)`} style={{ marginBottom: 0 }} />
            )}
          </Card>
        )}

        {profile.profiling_summary && (
          <Card size="small" title="Summary">
            <Descriptions column={2} size="small">
              <Descriptions.Item label="Quality">
                <StatusBadge
                  label={profile.profiling_summary.quality_level}
                  color={QUALITY_COLORS[profile.profiling_summary.quality_level]}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Sample Size">
                {profile.profiling_summary.sample_size_level}
              </Descriptions.Item>
              <Descriptions.Item label="Usable for ML">
                {profile.profiling_summary.is_usable_for_ml ? 'Yes' : 'No'}
              </Descriptions.Item>
              {profile.profiling_summary.recommended_next_step && (
                <Descriptions.Item label="Next">
                  {profile.profiling_summary.recommended_next_step}
                </Descriptions.Item>
              )}
            </Descriptions>
          </Card>
        )}
      </Space>
    );
  };

  const tabItems = [
    { key: 'profile', label: 'Profile', children: renderProfile() },
    {
      key: 'json',
      label: 'Full JSON',
      children: profile ? (
        <JsonViewer data={profile} />
      ) : (
        <EmptyState description="Run profiling to see JSON output." />
      ),
    },
  ];

  return (
    <PanelContainer
      title="Dataset Profiling"
      description="Upload a dataset file or use the dataset referenced in the task interpretation to run profiling."
      accentColor={pipelineAccent.datasetProfile}
    >
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" onClick={handleRunProfiling} loading={loading}>
          {loading ? 'Running...' : 'Run Dataset Profiling'}
        </Button>
        {profile && (
          <Button onClick={handleRerun} loading={loading}>
            Re-run Profiling
          </Button>
        )}
      </Space>
      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {uploadResult && (
        <Card
          size="small"
          title="Uploaded File"
          style={{ marginTop: 12, marginBottom: 12 }}
        >
          <Descriptions column={2} size="small">
            <Descriptions.Item label="File">{uploadResult.file_name}</Descriptions.Item>
            <Descriptions.Item label="Size">
              {(uploadResult.file_size_bytes / 1024).toFixed(1)} KB
            </Descriptions.Item>
            <Descriptions.Item label="Rows">{uploadResult.n_rows}</Descriptions.Item>
            <Descriptions.Item label="Columns">{uploadResult.n_columns}</Descriptions.Item>
          </Descriptions>
          <div style={{ marginTop: 8, overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }} aria-label="Uploaded dataset preview">
              <caption style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0,0,0,0)', whiteSpace: 'nowrap' }}>
                Preview of uploaded dataset: first 5 rows of {uploadResult.columns.length} columns
              </caption>
              <thead>
                <tr>
                  {uploadResult.columns.map((col) => (
                    <th
                      scope="col"
                      key={col}
                      style={{
                        textAlign: 'left', borderBottom: '1px solid #ccc', padding: '4px 6px',
                        maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                      }}
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {uploadResult.preview_rows.slice(0, 5).map((row, i) => (
                  <tr key={i}>
                    {uploadResult.columns.map((col) => (
                      <td
                        key={col}
                        style={{
                          borderBottom: '1px solid #eee', padding: '2px 6px',
                          maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                        }}
                      >
                        {String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      <Spin spinning={loading}>
        {error && <ErrorBox message={error} />}

        {profile && <Tabs activeKey={activeTab} onChange={setActiveTab} items={tabItems} />}

        {!profile && !error && !loading && !uploadResult && (
          <EmptyState description="No profile data yet. Upload a dataset and click &quot;Run Dataset Profiling&quot; to start." />
        )}
      </Spin>
    </PanelContainer>
  );
};

export default DatasetProfilePanel;
