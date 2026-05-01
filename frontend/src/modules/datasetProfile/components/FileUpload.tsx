import React, { useState, useRef } from 'react';
import { uploadDatasetFile } from '../../../api/datasetProfileApi';
import { DatasetFileUploadResponse } from '../types';

interface FileUploadProps {
  onUploadSuccess: (result: DatasetFileUploadResponse) => void;
}

const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

const FileUpload: React.FC<FileUploadProps> = ({ onUploadSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndUpload = async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setError(`Unsupported file type "${ext}". Allowed: ${ALLOWED_EXTENSIONS.join(', ')}`);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await uploadDatasetFile(file);
      if (response.success) {
        onUploadSuccess(response.data);
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      const msg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
      setError(msg || err.message || 'Upload failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      validateAndUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      validateAndUpload(file);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div style={styles.container}>
      <h4 style={styles.title}>Upload Dataset</h4>

      <div
        onClick={handleClick}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        style={{
          ...styles.dropZone,
          ...(dragOver ? styles.dropZoneActive : {}),
          ...(loading ? styles.dropZoneDisabled : {}),
        }}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
        {loading ? (
          <span>Uploading...</span>
        ) : (
          <>
            <span style={styles.dropIcon}>+</span>
            <span>Click or drag a .csv / .xlsx file here</span>
          </>
        )}
      </div>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

const styles: Record<string, React.CSSProperties> = {
  container: {
    marginTop: '12px',
  },
  title: {
    margin: '0 0 8px 0',
    fontSize: '15px',
    fontWeight: 600,
    color: '#333',
  },
  dropZone: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    gap: '8px',
    padding: '24px',
    border: '2px dashed #bbb',
    borderRadius: '8px',
    cursor: 'pointer',
    color: '#666',
    fontSize: '14px',
    transition: 'border-color 0.2s',
  },
  dropZoneActive: {
    borderColor: '#1976d2',
    backgroundColor: '#e3f2fd',
  },
  dropZoneDisabled: {
    opacity: 0.6,
    cursor: 'not-allowed',
  },
  dropIcon: {
    fontSize: '28px',
    fontWeight: 300,
    color: '#999',
  },
  errorBox: {
    marginTop: '12px',
    padding: '10px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '4px',
    color: '#c62828',
    fontSize: '13px',
  },
};

export default FileUpload;
