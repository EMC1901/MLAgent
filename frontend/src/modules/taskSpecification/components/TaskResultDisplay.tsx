import React from 'react';
import { TaskSpecificationResponse } from '../../../api/taskApi';

interface TaskResultDisplayProps {
  result: TaskSpecificationResponse;
}

const STATUS_COLORS: Record<string, string> = {
  valid: '#4caf50',
  valid_with_warning: '#ff9800',
  incomplete: '#ff9800',
  invalid: '#f44336',
};

const styles = {
  resultBox: {
    marginTop: '24px', padding: '16px', backgroundColor: '#e8f5e9',
    border: '1px solid #4caf50', borderRadius: '4px',
  } as React.CSSProperties,
  resultTitle: { margin: '0 0 12px 0', fontSize: '18px', fontWeight: 600 } as React.CSSProperties,
  resultField: { marginBottom: '8px', fontSize: '14px' } as React.CSSProperties,
  messageList: { margin: '4px 0', paddingLeft: '20px' } as React.CSSProperties,
  resultJson: { marginTop: '16px' } as React.CSSProperties,
  pre: {
    backgroundColor: '#fff', padding: '12px', borderRadius: '4px',
    overflow: 'auto', fontSize: '12px', marginTop: '8px',
  } as React.CSSProperties,
};

const TaskResultDisplay: React.FC<TaskResultDisplayProps> = ({ result }) => {
  return (
    <div style={styles.resultBox}>
      <h3 style={styles.resultTitle}>Task Specification Result</h3>
      <div style={styles.resultField}>
        <strong>Task ID:</strong> {result.task_id}
      </div>
      <div style={styles.resultField}>
        <strong>Status:</strong>{' '}
        <span style={{ color: STATUS_COLORS[result.status] || '#9e9e9e' }}>
          {result.status}
        </span>
      </div>
      {result.missing_fields && result.missing_fields.length > 0 && (
        <div style={styles.resultField}>
          <strong>Missing Fields:</strong> {result.missing_fields.join(', ')}
        </div>
      )}
      {result.validation_messages && result.validation_messages.length > 0 && (
        <div style={styles.resultField}>
          <strong>Validation Messages:</strong>
          <ul style={styles.messageList}>
            {result.validation_messages.map((msg, index) => (
              <li key={index}>{msg}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={styles.resultJson}>
        <strong>Full Result:</strong>
        <pre style={styles.pre}>{JSON.stringify(result, null, 2)}</pre>
      </div>
    </div>
  );
};

export default TaskResultDisplay;
