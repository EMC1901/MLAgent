import React, { useState } from 'react';
import { createDatasetProfile, rerunDatasetProfile } from '../../../api/datasetProfileApi';
import { DatasetProfileResponse, DatasetFileUploadResponse } from '../types';
import FileUpload from './FileUpload';

interface DatasetProfilePanelProps {
  taskId: string;
  initialResult?: DatasetProfileResponse;
}

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
      const response = await rerunDatasetProfile(taskId);
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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'profiled': return '#4caf50';
      case 'profiled_with_warning': return '#ff9800';
      case 'failed': return '#f44336';
      case 'blocked': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const getQualityColor = (level: string) => {
    switch (level) {
      case 'good': return '#4caf50';
      case 'fair': return '#ff9800';
      case 'poor': return '#f44336';
      case 'unusable': return '#9e9e9e';
      default: return '#9e9e9e';
    }
  };

  const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
    <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
  );

  const renderProfile = () => {
    if (!profile) return null;
    return (
      <div>
        <div style={s.card}>
          <h4 style={s.cardTitle}>Profile Summary</h4>
          <div style={s.grid}>
            <div style={s.field}><strong>Profile ID:</strong> {profile.dataset_profile_id}</div>
            <div style={s.field}>
              <strong>Status: </strong>
              <Badge label={profile.status} color={getStatusColor(profile.status)} />
            </div>
          </div>
        </div>

        {profile.dataset_source && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Source</h4>
            <div style={s.field}>
              {profile.dataset_source.source_type}
              {profile.dataset_source.dataset_reference && ` (${profile.dataset_source.dataset_reference})`}
            </div>
          </div>
        )}

        {profile.dataset_schema && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Schema</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Samples:</strong> {profile.dataset_schema.n_samples}</div>
              <div style={s.field}><strong>Columns:</strong> {profile.dataset_schema.n_columns}</div>
              <div style={s.field}><strong>Input Columns:</strong> {profile.dataset_schema.input_columns.join(', ') || 'none'}</div>
              <div style={s.field}><strong>Target:</strong> {profile.dataset_schema.target_column || 'none'}</div>
            </div>
          </div>
        )}

        {profile.modality_check && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Modality Check</h4>
            <div style={s.field}>
              <span style={{
                color: profile.modality_check.is_consistent ? '#2e7d32' : '#c62828',
                fontWeight: 600,
              }}>
                {profile.modality_check.is_consistent ? 'Consistent' : 'Mismatch'}
              </span>
            </div>
          </div>
        )}

        {profile.target_profile && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Target Profile ({profile.target_profile.task_type})</h4>
            {profile.target_profile.task_type === 'regression' && (
              <div style={s.grid}>
                <div style={s.field}><strong>Range:</strong> {profile.target_profile.min?.toFixed(2)} – {profile.target_profile.max?.toFixed(2)}</div>
                <div style={s.field}><strong>Mean:</strong> {profile.target_profile.mean?.toFixed(2)}</div>
                <div style={s.field}><strong>Std:</strong> {profile.target_profile.std?.toFixed(2)}</div>
                <div style={s.field}><strong>Skewness:</strong> {profile.target_profile.skewness?.toFixed(2)}</div>
                <div style={s.field}><strong>Outliers:</strong> {profile.target_profile.outlier_count}</div>
              </div>
            )}
            {profile.target_profile.task_type === 'classification' && (
              <div style={s.grid}>
                <div style={s.field}><strong>Classes:</strong> {profile.target_profile.class_count}</div>
                {profile.target_profile.is_imbalanced && (
                  <div style={{ ...s.field, color: '#e65100' }}>Warning: Classes are imbalanced</div>
                )}
              </div>
            )}
          </div>
        )}

        {profile.data_quality && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Data Quality</h4>
            <div style={s.grid}>
              <div style={s.field}><strong>Missing:</strong> {profile.data_quality.missing_values.total_missing}</div>
              <div style={s.field}><strong>Duplicate Rows:</strong> {profile.data_quality.duplicates.duplicate_rows}</div>
            </div>
            {profile.data_quality.warnings.length > 0 && (
              <div style={{ color: '#e65100', marginTop: '4px' }}>Warnings: {profile.data_quality.warnings.length}</div>
            )}
            {profile.data_quality.errors.length > 0 && (
              <div style={{ color: '#c62828', marginTop: '4px' }}>Errors: {profile.data_quality.errors.length}</div>
            )}
          </div>
        )}

        {profile.profiling_summary && (
          <div style={s.card}>
            <h4 style={s.cardTitle}>Summary</h4>
            <div style={s.grid}>
              <div style={s.field}>
                <strong>Quality: </strong>
                <span style={{ color: getQualityColor(profile.profiling_summary.quality_level), fontWeight: 600 }}>
                  {profile.profiling_summary.quality_level}
                </span>
              </div>
              <div style={s.field}><strong>Sample Size:</strong> {profile.profiling_summary.sample_size_level}</div>
              <div style={s.field}><strong>Usable for ML:</strong> {profile.profiling_summary.is_usable_for_ml ? 'Yes' : 'No'}</div>
              {profile.profiling_summary.recommended_next_step && (
                <div style={s.field}><strong>Next:</strong> {profile.profiling_summary.recommended_next_step}</div>
              )}
            </div>
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
    { id: 'profile', label: 'Profile' },
    { id: 'json', label: 'Full JSON' },
  ];

  return (
    <div style={s.container}>
      <h3 style={s.title}>Dataset Profiling</h3>
      <p style={s.description}>
        Upload a dataset file or use the dataset referenced in the task interpretation to run profiling.
      </p>

      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {uploadResult && (
        <div style={s.uploadInfo}>
          <strong>File ready:</strong> {uploadResult.file_name}{' '}
          ({(uploadResult.file_size_bytes / 1024).toFixed(1)} KB){' | '}
          {uploadResult.n_rows} rows x {uploadResult.n_columns} columns
          <table style={s.miniTable}>
            <thead>
              <tr>
                {uploadResult.columns.map((col) => (
                  <th key={col} style={s.miniTh}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {uploadResult.preview_rows.slice(0, 5).map((row, i) => (
                <tr key={i}>
                  {uploadResult.columns.map((col) => (
                    <td key={col} style={s.miniTd}>{String(row[col] ?? '')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={s.buttonRow}>
        <button onClick={handleRunProfiling} disabled={loading} style={s.runButton}>
          {loading ? 'Running...' : 'Run Dataset Profiling'}
        </button>
        {profile && (
          <button onClick={handleRerun} disabled={loading} style={s.rerunButton}>
            {loading ? 'Running...' : 'Re-run Profiling'}
          </button>
        )}
      </div>

      {error && (
        <div style={s.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {profile && (
        <div style={s.resultBox}>
          <h4 style={s.resultTitle}>Profile Result</h4>

          <div style={s.tabBar}>
            {tabs.map(t => renderTab(t.id, t.label))}
          </div>

          <div style={s.tabContent}>
            {activeTab === 'profile' && renderProfile()}
            {activeTab === 'json' && (
              <div style={s.card}>
                <h4 style={s.cardTitle}>Full JSON</h4>
                <pre style={s.json}>{JSON.stringify(profile, null, 2)}</pre>
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
  uploadInfo: {
    marginTop: '12px', marginBottom: '12px',
    padding: '12px', backgroundColor: '#fff', border: '1px solid #e0e0e0',
    borderRadius: '6px', fontSize: '13px',
  },
  miniTable: {
    width: '100%', marginTop: '8px', borderCollapse: 'collapse' as const, fontSize: '12px',
  },
  miniTh: {
    textAlign: 'left' as const, borderBottom: '1px solid #ccc', padding: '4px 6px',
    maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
  },
  miniTd: {
    borderBottom: '1px solid #eee', padding: '2px 6px',
    maxWidth: '120px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' as const,
  },
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
    borderRadius: '8px', marginTop: '12px',
  },
  resultTitle: { margin: '0 0 12px 0', fontSize: '16px', fontWeight: 600 },
  badge: {
    display: 'inline-block', padding: '2px 8px', borderRadius: '12px',
    color: '#fff', fontSize: '12px', fontWeight: 600, margin: '0 4px',
  },
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
  json: {
    backgroundColor: '#263238', color: '#aed581', padding: '12px',
    borderRadius: '4px', overflow: 'auto', fontSize: '11px',
  },
};

export default DatasetProfilePanel;
