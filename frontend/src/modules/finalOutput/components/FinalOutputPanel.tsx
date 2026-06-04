import React, { useState, useMemo } from 'react';
import {
  createFinalOutput,
  rerunFinalOutput,
  downloadArtifactZip,
} from '../../../api/finalOutputApi';
import { FinalOutputResponse } from '../types';
import {
  STATUS_COLORS,
  STATUS_LABELS,
} from '../constants';

interface FinalOutputPanelProps {
  taskId: string;
  initialResult?: FinalOutputResponse;
}

const FinalOutputPanel: React.FC<FinalOutputPanelProps> = ({ taskId, initialResult }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<FinalOutputResponse | null>(initialResult ?? null);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await createFinalOutput(taskId);
      if (response.success) {
        setResult(response.data);
        const foId = response.data?.final_output_id;
        if (foId) {
          downloadArtifactZip(foId);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to generate final output.');
    } finally {
      setLoading(false);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const response = await rerunFinalOutput(taskId);
      if (response.success) {
        setResult(response.data);
        const foId = response.data?.final_output_id;
        if (foId) {
          downloadArtifactZip(foId);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Failed to re-generate final output.');
    } finally {
      setLoading(false);
    }
  };

  const topicFileLabels: Record<string, string> = {
    task_specification: 'Task Specification — how the system understood the task',
    dataset_profile: 'Dataset Profile — scale, target distribution, missing values, quality',
    workflow_plan: 'Workflow Plan — feature, preprocessing, model, validation, metric strategies',
    model_ready_feature_summary: 'Model-Ready Feature Summary — final feature count, dropped/kept features',
    candidate_model_plan: 'Candidate Model Plan — candidate and excluded models',
    hpo_plan: 'HPO Plan — search method, trial count, search space',
    pipeline_specs: 'Pipeline Specs — proof that workflow is executable',
    training_evaluation_results: 'Training / Evaluation Results — performance report',
    interpretability_analysis: 'Interpretability Analysis — feature importance, SHAP, material insights',
    final_output_package: 'Final Output Package — proof that reports, model, logs, reproducibility files are generated',
  };

  const downloadedFiles = useMemo(() => {
    const topics = result?.topic_files;
    if (!topics || topics.length === 0) return [];
    return topics.map((t) => ({
      name: topicFileLabels[t.topic] || t.topic,
      path: t.file,
    }));
  }, [result]);

  return (
    <div style={styles.container}>
      <h2 style={styles.title}>Final Output</h2>

      <div style={styles.actions}>
        <button
          onClick={handleGenerate}
          disabled={loading || !taskId}
          style={{
            ...styles.button,
            ...styles.primaryBtn,
            ...(loading || !taskId ? styles.disabledBtn : {}),
          }}
        >
          {loading ? 'Generating...' : 'Generate Final Output'}
        </button>
        <button
          onClick={handleRerun}
          disabled={loading || !taskId}
          style={{
            ...styles.button,
            ...styles.secondaryBtn,
            ...(loading || !taskId ? styles.disabledBtn : {}),
          }}
        >
          Re-generate Output
        </button>
      </div>

      {error && <div style={styles.errorBox}>{error}</div>}

      {result && (
        <div style={styles.resultContainer}>
          <div style={styles.statusBar}>
            <span style={{ ...styles.statusBadge, backgroundColor: STATUS_COLORS[result.status] || '#999' }}>
              {STATUS_LABELS[result.status] || result.status}
            </span>
            <span style={styles.idText}>ID: {result.final_output_id}</span>
            {result.ready_for_delivery && (
              <span style={styles.readyBadge}>Ready for Delivery</span>
            )}
          </div>

          <div style={styles.section}>
            <h3 style={styles.sectionTitle}>Downloaded Files</h3>
            {downloadedFiles.length === 0 ? (
              <p style={styles.emptyText}>No artifact information available.</p>
            ) : (
              <div style={styles.fileList}>
                {downloadedFiles.map((f, i) => (
                  <div key={i} style={styles.fileItem}>
                    <span style={styles.fileIcon}>📄</span>
                    <span style={styles.fileName}>{f.name}</span>
                    <span style={styles.filePath}>{f.path}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {result.warnings && result.warnings.length > 0 && (
            <div style={styles.warningsBox}>
              <strong>Warnings:</strong>
              <ul style={styles.warningList}>
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {result.error_message && (
            <div style={styles.errorBox}>
              <strong>Error:</strong> {result.error_message}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    border: '1px solid #4caf50',
    borderRadius: '8px',
    padding: '20px',
    marginTop: '16px',
    backgroundColor: '#f1f8e9',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '20px',
    fontWeight: 600,
    color: '#2e7d32',
  },
  actions: {
    display: 'flex',
    gap: '12px',
    marginBottom: '16px',
  },
  button: {
    padding: '10px 24px',
    borderRadius: '6px',
    border: 'none',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: 500,
  },
  primaryBtn: {
    backgroundColor: '#2e7d32',
    color: '#fff',
  },
  secondaryBtn: {
    backgroundColor: '#f5f5f5',
    color: '#333',
    border: '1px solid #ccc',
  },
  disabledBtn: {
    opacity: 0.5,
    cursor: 'not-allowed',
  },
  errorBox: {
    backgroundColor: '#ffebee',
    color: '#c62828',
    padding: '12px',
    borderRadius: '6px',
    marginBottom: '16px',
    fontSize: '14px',
  },
  resultContainer: {
    marginTop: '16px',
  },
  statusBar: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '16px',
    flexWrap: 'wrap',
  },
  statusBadge: {
    color: '#fff',
    padding: '4px 12px',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: 500,
  },
  idText: {
    fontSize: '13px',
    color: '#666',
    fontFamily: 'monospace',
  },
  readyBadge: {
    backgroundColor: '#4caf50',
    color: '#fff',
    padding: '2px 10px',
    borderRadius: '10px',
    fontSize: '12px',
    fontWeight: 500,
  },
  section: {
    marginTop: '8px',
  },
  sectionTitle: {
    fontSize: '15px',
    fontWeight: 600,
    color: '#333',
    margin: '0 0 10px 0',
  },
  emptyText: {
    fontSize: '14px',
    color: '#999',
  },
  fileList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '6px',
  },
  fileItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '10px',
    padding: '8px 12px',
    backgroundColor: '#fff',
    borderRadius: '6px',
    border: '1px solid #e0e0e0',
    fontSize: '14px',
  },
  fileIcon: {
    flexShrink: 0,
  },
  fileName: {
    fontWeight: 500,
    color: '#333',
    minWidth: '180px',
  },
  filePath: {
    color: '#888',
    fontSize: '12px',
    fontFamily: 'monospace',
    wordBreak: 'break-all',
  },
  warningsBox: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#fff3e0',
    border: '1px solid #ffe0b2',
    borderRadius: '6px',
    fontSize: '13px',
  },
  warningList: {
    margin: '8px 0 0 0',
    paddingLeft: '20px',
  },
};

export default FinalOutputPanel;
