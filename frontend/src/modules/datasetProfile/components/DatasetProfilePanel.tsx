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

  const handleUploadSuccess = (result: DatasetFileUploadResponse) => {
    setUploadResult(result);
    setError(null);
  };

  const handleRunProfiling = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await createDatasetProfile(
        taskId,
        uploadResult?.file_id,
      );
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

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Dataset Profiling</h3>
      <p style={styles.description}>
        Upload a dataset file or use the dataset referenced in the task interpretation to run profiling.
      </p>

      <FileUpload onUploadSuccess={handleUploadSuccess} />

      {uploadResult && (
        <div style={styles.uploadInfo}>
          <strong>File ready:</strong> {uploadResult.file_name}{' '}
          ({(uploadResult.file_size_bytes / 1024).toFixed(1)} KB){' | '}
          {uploadResult.n_rows} rows x {uploadResult.n_columns} columns
          <table style={styles.miniTable}>
            <thead>
              <tr>
                {uploadResult.columns.map((col) => (
                  <th key={col} style={styles.miniTh}>{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {uploadResult.preview_rows.slice(0, 5).map((row, i) => (
                <tr key={i}>
                  {uploadResult.columns.map((col) => (
                    <td key={col} style={styles.miniTd}>{String(row[col] ?? '')}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <div style={styles.buttonRow}>
        <button
          onClick={handleRunProfiling}
          disabled={loading}
          style={styles.runButton}
        >
          {loading ? 'Running...' : 'Run Dataset Profiling'}
        </button>
        {profile && (
          <button
            onClick={handleRerun}
            disabled={loading}
            style={styles.rerunButton}
          >
            {loading ? 'Running...' : 'Re-run Profiling'}
          </button>
        )}
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {profile && (
        <div style={styles.resultBox}>
          <h4 style={styles.resultTitle}>Profile Result</h4>

          <div style={styles.field}>
            <strong>Profile ID:</strong> {profile.dataset_profile_id}
          </div>
          <div style={styles.field}>
            <strong>Status:</strong>{' '}
            <span style={{ color: getStatusColor(profile.status), fontWeight: 600 }}>
              {profile.status}
            </span>
          </div>

          {profile.dataset_source && (
            <div style={styles.section}>
              <strong>Source:</strong>{' '}
              {profile.dataset_source.source_type}
              {profile.dataset_source.dataset_reference &&
                ` (${profile.dataset_source.dataset_reference})`}
            </div>
          )}

          {profile.dataset_schema && (
            <div style={styles.section}>
              <strong>Schema:</strong>{' '}
              {profile.dataset_schema.n_samples} samples, {profile.dataset_schema.n_columns} columns
              <div style={styles.indent}>
                Input: {profile.dataset_schema.input_columns.join(', ') || 'none'}<br />
                Target: {profile.dataset_schema.target_column || 'none'}
              </div>
            </div>
          )}

          {profile.modality_check && (
            <div style={styles.section}>
              <strong>Modality Check:</strong>{' '}
              <span style={{
                color: profile.modality_check.is_consistent ? '#4caf50' : '#f44336',
                fontWeight: 600,
              }}>
                {profile.modality_check.is_consistent ? 'Consistent' : 'Mismatch'}
              </span>
            </div>
          )}

          {profile.target_profile && (
            <div style={styles.section}>
              <strong>Target Profile</strong> ({profile.target_profile.task_type}):
              <div style={styles.indent}>
                {profile.target_profile.task_type === 'regression' && (
                  <>
                    Range: {profile.target_profile.min?.toFixed(2)} – {profile.target_profile.max?.toFixed(2)}<br />
                    Mean: {profile.target_profile.mean?.toFixed(2)}, Std: {profile.target_profile.std?.toFixed(2)}<br />
                    Skewness: {profile.target_profile.skewness?.toFixed(2)}, Outliers: {profile.target_profile.outlier_count}
                  </>
                )}
                {profile.target_profile.task_type === 'classification' && (
                  <>
                    Classes: {profile.target_profile.class_count}<br />
                    {profile.target_profile.is_imbalanced && 'Warning: Classes are imbalanced'}
                  </>
                )}
              </div>
            </div>
          )}

          {profile.data_quality && (
            <div style={styles.section}>
              <strong>Data Quality:</strong>
              <div style={styles.indent}>
                Missing: {profile.data_quality.missing_values.total_missing}<br />
                Duplicate rows: {profile.data_quality.duplicates.duplicate_rows}
                {profile.data_quality.warnings.length > 0 && (
                  <div style={{ color: '#e65100', marginTop: '4px' }}>
                    Warnings: {profile.data_quality.warnings.length}
                  </div>
                )}
                {profile.data_quality.errors.length > 0 && (
                  <div style={{ color: '#c62828', marginTop: '4px' }}>
                    Errors: {profile.data_quality.errors.length}
                  </div>
                )}
              </div>
            </div>
          )}

          {profile.profiling_summary && (
            <div style={styles.section}>
              <strong>Summary:</strong>
              <div style={styles.indent}>
                Quality:{' '}
                <span style={{ color: getQualityColor(profile.profiling_summary.quality_level), fontWeight: 600 }}>
                  {profile.profiling_summary.quality_level}
                </span>
                {' | '}
                Sample size: {profile.profiling_summary.sample_size_level}
                {' | '}
                Usable: {profile.profiling_summary.is_usable_for_ml ? 'Yes' : 'No'}
                {profile.profiling_summary.recommended_next_step && (
                  <><br />Next: {profile.profiling_summary.recommended_next_step}</>
                )}
              </div>
            </div>
          )}

          <details style={styles.jsonSection}>
            <summary style={{ cursor: 'pointer', fontWeight: 600, fontSize: '13px', marginBottom: '8px' }}>
              Full Result (JSON)
            </summary>
            <pre style={styles.pre}>{JSON.stringify(profile, null, 2)}</pre>
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
  uploadInfo: {
    marginTop: '12px',
    padding: '12px',
    backgroundColor: '#e8f5e9',
    border: '1px solid #4caf50',
    borderRadius: '4px',
    fontSize: '13px',
  },
  miniTable: {
    width: '100%',
    marginTop: '8px',
    borderCollapse: 'collapse' as const,
    fontSize: '12px',
  },
  miniTh: {
    textAlign: 'left' as const,
    borderBottom: '1px solid #ccc',
    padding: '4px 6px',
    maxWidth: '120px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  miniTd: {
    borderBottom: '1px solid #eee',
    padding: '2px 6px',
    maxWidth: '120px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap' as const,
  },
  buttonRow: {
    display: 'flex',
    gap: '12px',
    marginTop: '16px',
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
    marginTop: '12px',
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
    maxHeight: '300px',
  },
};

export default DatasetProfilePanel;
