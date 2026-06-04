import React, { useState } from 'react';
import { listTasks, TaskSummaryResponse } from '../../../api/taskApi';
import ModelConfigModal from './ModelConfigModal';

interface TaskHistoryListProps {
  onLoadTask: (taskId: string) => void;
  onNewTask: () => void;
  isLoading?: boolean;
  currentTaskId?: string;
}

const TaskHistoryList: React.FC<TaskHistoryListProps> = ({
  onLoadTask,
  onNewTask,
  isLoading = false,
  currentTaskId,
}) => {
  const [expanded, setExpanded] = useState(false);
  const [tasks, setTasks] = useState<TaskSummaryResponse[]>([]);
  const [fetching, setFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [modelConfigVisible, setModelConfigVisible] = useState(false);
  const [configVersion, setConfigVersion] = useState(0);

  const fetchTasks = async () => {
    setFetching(true);
    setFetchError(null);
    try {
      const response = await listTasks();
      if (response.success) {
        setTasks(response.data);
      } else {
        setFetchError(response.message);
      }
    } catch (err: any) {
      setFetchError(err.message || 'Failed to fetch task list.');
    } finally {
      setFetching(false);
    }
  };

  const handleToggle = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next) {
      await fetchTasks();
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleString();
    } catch {
      return dateStr;
    }
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      valid: '#4caf50',
      valid_with_warning: '#ff9800',
      received: '#9e9e9e',
      incomplete: '#f44336',
      invalid: '#f44336',
      updated: '#2196f3',
    };
    return (
      <span style={{ ...s.statusBadge, backgroundColor: colors[status] || '#9e9e9e' }}>
        {status}
      </span>
    );
  };

  return (
    <div style={s.container}>
      <button type="button" onClick={handleToggle} style={s.toggleButton}>
        {expanded ? 'Hide Historical Tasks' : 'Load Historical Tasks'}
      </button>

      <button
        type="button"
        onClick={() => setModelConfigVisible(true)}
        style={s.switchModelButton}
      >
        Switch Model
      </button>

      <ModelConfigModal
        visible={modelConfigVisible}
        onClose={() => setModelConfigVisible(false)}
        onConfigChanged={() => setConfigVersion((v) => v + 1)}
      />

      {expanded && (
        <div style={s.panel}>
          {fetching && <div style={s.loadingText}>Loading tasks...</div>}
          {fetchError && <div style={s.errorText}>{fetchError}</div>}

          {!fetching && !fetchError && tasks.length === 0 && (
            <div style={s.emptyText}>No historical tasks found.</div>
          )}

          {tasks.length > 0 && (
            <div style={s.tableWrapper}>
              <table style={s.table}>
                <thead>
                  <tr>
                    <th style={s.th}>Task Name</th>
                    <th style={s.th}>Type</th>
                    <th style={s.th}>Target</th>
                    <th style={s.th}>Status</th>
                    <th style={s.th}>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((task) => {
                    const isCurrent = task.task_id === currentTaskId;
                    return (
                      <tr
                        key={task.task_id}
                        onClick={() => !isLoading && onLoadTask(task.task_id)}
                        style={{
                          ...s.tr,
                          backgroundColor: isCurrent ? '#e3f2fd' : undefined,
                          cursor: isLoading ? 'default' : 'pointer',
                          opacity: isLoading ? 0.6 : 1,
                        }}
                      >
                        <td style={s.td}>
                          {task.task_name || <span style={s.muted}>Unnamed</span>}
                          {isCurrent && <span style={s.currentLabel}>current</span>}
                        </td>
                        <td style={s.td}>{task.task_type || '-'}</td>
                        <td style={s.td}>{task.prediction_target || '-'}</td>
                        <td style={s.td}>{getStatusBadge(task.status)}</td>
                        <td style={s.td}>{formatDate(task.created_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          <button type="button" onClick={onNewTask} style={s.newTaskButton}>
            + New Task
          </button>
          <button type="button" onClick={fetchTasks} disabled={fetching} style={s.refreshButton}>
            {fetching ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
      )}
    </div>
  );
};

const s: Record<string, React.CSSProperties> = {
  container: {
    marginBottom: '16px',
  },
  toggleButton: {
    padding: '8px 16px',
    backgroundColor: '#1565c0',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  switchModelButton: {
    padding: '8px 16px',
    backgroundColor: '#6a1b9a',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '14px',
    fontWeight: 600,
    cursor: 'pointer',
    marginLeft: '8px',
  },
  panel: {
    marginTop: '8px',
    padding: '12px',
    backgroundColor: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: '4px',
  },
  loadingText: {
    fontSize: '14px',
    color: '#888',
    padding: '8px',
  },
  errorText: {
    fontSize: '14px',
    color: '#c62828',
    padding: '8px',
  },
  emptyText: {
    fontSize: '14px',
    color: '#888',
    padding: '8px',
  },
  tableWrapper: {
    maxHeight: '300px',
    overflowY: 'auto',
    marginBottom: '12px',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: '13px',
  },
  th: {
    textAlign: 'left' as const,
    padding: '6px 10px',
    borderBottom: '2px solid #e0e0e0',
    fontWeight: 600,
    color: '#555',
    fontSize: '12px',
    position: 'sticky' as const,
    top: 0,
    backgroundColor: '#fff',
  },
  tr: {
    borderBottom: '1px solid #f0f0f0',
  },
  td: {
    padding: '6px 10px',
  },
  statusBadge: {
    display: 'inline-block',
    color: '#fff',
    padding: '1px 8px',
    borderRadius: '10px',
    fontSize: '11px',
  },
  muted: {
    color: '#aaa',
    fontStyle: 'italic',
  },
  currentLabel: {
    marginLeft: '6px',
    fontSize: '10px',
    color: '#1565c0',
    fontWeight: 600,
  },
  newTaskButton: {
    padding: '6px 16px',
    backgroundColor: '#4caf50',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
  },
  refreshButton: {
    padding: '6px 16px',
    backgroundColor: '#1565c0',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '13px',
    fontWeight: 600,
    cursor: 'pointer',
    marginLeft: '8px',
  },
};

export default TaskHistoryList;
