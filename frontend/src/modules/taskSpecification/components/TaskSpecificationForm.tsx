import React, { useState } from 'react';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import {
  taskSpecificationSchema,
  TaskSpecificationFormData,
  TASK_TYPE_OPTIONS,
  INPUT_TYPE_OPTIONS,
  MATERIAL_SYSTEM_OPTIONS,
  EVALUATION_METRIC_OPTIONS,
  USER_PRIORITY_OPTIONS,
} from '../constants';
import TaskFieldGroup from './TaskFieldGroup';
import TaskHistoryList from './TaskHistoryList';
import { createTask, getTask, TaskSpecificationResponse } from '../../../api/taskApi';
import { getLatestInterpretation } from '../../../api/taskInterpretationApi';
import { getLatestDatasetProfileByTaskId } from '../../../api/datasetProfileApi';
import { getLatestWorkflowPlanByTaskId } from '../../../api/workflowPlanningApi';
import { getLatestFeatureEngineeringByTaskId } from '../../../api/featureEngineeringApi';
import { getLatestFeaturePreprocessingByTaskId } from '../../../api/featurePreprocessingApi';
import { getLatestModelSearchContextByTaskId } from '../../../api/modelSearchContextApi';
import { getLatestModelSearchPlanByTaskId } from '../../../api/modelSearchApi';
import { getLatestPipelineGenerationByTaskId } from '../../../api/pipelineGenerationApi';
import { getLatestPipelineExecutionByTaskId } from '../../../api/pipelineExecutionApi';
import { getLatestMetricEvaluationByTaskId } from '../../../api/metricEvaluationApi';
import { getLatestResultDiagnosisByTaskId } from '../../../api/resultDiagnosisApi';
import { getLatestWorkflowRefinementByTaskId } from '../../../api/workflowRefinementApi';
import { getLatestFinalPipelineSelection } from '../../../api/finalPipelineSelectionApi';
import { getLatestInterpretabilityAnalysis } from '../../../api/interpretabilityAnalysisApi';
import { getLatestFinalOutput } from '../../../api/finalOutputApi';
import TaskInterpretationPanel from '../../taskInterpretation/components/TaskInterpretationPanel';
import DatasetProfilePanel from '../../datasetProfile/components/DatasetProfilePanel';
import WorkflowPlanPanel from '../../workflowPlanning/components/WorkflowPlanPanel';
import FeatureEngineeringPanel from '../../featureEngineering/components/FeatureEngineeringPanel';
import FeaturePreprocessingPanel from '../../featurePreprocessing/components/FeaturePreprocessingPanel';
import ModelSearchContextPanel from '../../modelSearchContext/components/ModelSearchContextPanel';
import ModelSearchPlanPanel from '../../modelSearch/components/ModelSearchPlanPanel';
import PipelineGenerationPanel from '../../pipelineGeneration/components/PipelineGenerationPanel';
import PipelineExecutionPanel from '../../pipelineExecution/components/PipelineExecutionPanel';
import MetricEvaluationPanel from '../../metricEvaluation/components/MetricEvaluationPanel';
import ResultDiagnosisPanel from '../../resultDiagnosis/components/ResultDiagnosisPanel';
import WorkflowRefinementPanel from '../../workflowRefinement/components/WorkflowRefinementPanel';
import FinalPipelineSelectionPanel from '../../finalPipelineSelection/components/FinalPipelineSelectionPanel';
import InterpretabilityAnalysisPanel from '../../interpretabilityAnalysis/components/InterpretabilityAnalysisPanel';
import FinalOutputPanel from '../../finalOutput/components/FinalOutputPanel';

interface TaskSpecificationFormProps {
  onSubmitSuccess?: (result: TaskSpecificationResponse) => void;
}

const defaultValues = {
  task_name: '',
  task_description: '',
  material_system: '',
  prediction_target: '',
  task_type: '',
  dataset_description: '',
  input_type: '',
  target_column: '',
  evaluation_metric: '',
  user_priority: [],
  constraints: '',
};

const TaskSpecificationForm: React.FC<TaskSpecificationFormProps> = ({ onSubmitSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<TaskSpecificationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [panelResults, setPanelResults] = useState<Record<string, any>>({});
  const [loadingTask, setLoadingTask] = useState(false);

  const {
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<TaskSpecificationFormData>({
    resolver: zodResolver(taskSpecificationSchema),
    defaultValues,
  });

  const taskType = watch('task_type');

  const onSubmit = async (data: TaskSpecificationFormData) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const constraintsArray = data.constraints
        ? data.constraints.split('\n').filter((c) => c.trim())
        : [];

      const request = {
        task_name: data.task_name,
        task_description: data.task_description,
        material_system: data.material_system,
        prediction_target: data.prediction_target,
        task_type: data.task_type,
        dataset_description: data.dataset_description,
        input_type: data.input_type,
        target_column: data.target_column,
        evaluation_metric: data.evaluation_metric,
        user_priority: data.user_priority || [],
        constraints: constraintsArray,
      };

      const response = await createTask(request);

      if (response.success) {
        setResult(response.data);
        setActiveTaskId(response.data.task_id);
        setPanelResults({});
        if (onSubmitSuccess) {
          onSubmitSuccess(response.data);
        }
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      console.error('[Form] Submit error - full error object:', err);

      if (err.code === 'ERR_NETWORK' || err.code === 'ECONNREFUSED' || err.message?.includes('Network Error')) {
        setError(
          `Network Error: Cannot reach backend at http://localhost:8000. Make sure the backend server is running.\n` +
          `Run: cd backend && uvicorn app.main:app --reload --port 8000`
        );
      } else if (err.code === 'ERR_CANCELED') {
        setError('Request timeout (>15s): Backend took too long to respond. Check if the database is running.');
      } else if (err.response) {
        const status = err.response.status;
        const detail = err.response.data?.detail;
        const detailMsg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
        const backendMsg = detailMsg ||
          err.response.data?.message ||
          JSON.stringify(err.response.data);
        setError(`HTTP ${status}: ${backendMsg}`);
      } else {
        setError(`Request failed: ${err.message || 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const loadTask = async (taskId: string) => {
    setLoadingTask(true);
    setError(null);
    setPanelResults({});

    try {
      const taskResponse = await getTask(taskId);
      if (!taskResponse.success) {
        setError(taskResponse.message);
        return;
      }
      const taskData = taskResponse.data;

      reset({
        task_name: taskData.task_name || '',
        task_description: taskData.task_description || '',
        material_system: taskData.material_system || '',
        prediction_target: taskData.prediction_target || '',
        task_type: taskData.task_type || '',
        dataset_description: taskData.dataset_description || '',
        input_type: taskData.input_type || '',
        target_column: taskData.target_column || '',
        evaluation_metric: taskData.evaluation_metric || '',
        user_priority: taskData.user_priority || [],
        constraints: (taskData.constraints || []).join('\n'),
      });

      const results: Record<string, any> = {};

      const fetchers: [string, () => Promise<any>][] = [
        ['interpretation', () => getLatestInterpretation(taskId)],
        ['datasetProfile', () => getLatestDatasetProfileByTaskId(taskId)],
        ['workflowPlan', () => getLatestWorkflowPlanByTaskId(taskId)],
        ['featureEngineering', () => getLatestFeatureEngineeringByTaskId(taskId)],
        ['featurePreprocessing', () => getLatestFeaturePreprocessingByTaskId(taskId)],
        ['modelSearchContext', () => getLatestModelSearchContextByTaskId(taskId)],
        ['modelSearchPlan', () => getLatestModelSearchPlanByTaskId(taskId)],
        ['pipelineGeneration', () => getLatestPipelineGenerationByTaskId(taskId)],
        ['pipelineExecution', () => getLatestPipelineExecutionByTaskId(taskId)],
        ['metricEvaluation', () => getLatestMetricEvaluationByTaskId(taskId)],
        ['resultDiagnosis', () => getLatestResultDiagnosisByTaskId(taskId)],
        ['workflowRefinement', () => getLatestWorkflowRefinementByTaskId(taskId)],
        ['finalPipelineSelection', () => getLatestFinalPipelineSelection(taskId)],
        ['interpretabilityAnalysis', () => getLatestInterpretabilityAnalysis(taskId)],
        ['finalOutput', () => getLatestFinalOutput(taskId)],
      ];

      const settleResults = await Promise.allSettled(
        fetchers.map(([, fn]) => fn())
      );

      settleResults.forEach((settled, index) => {
        if (settled.status === 'fulfilled' && settled.value?.success) {
          results[fetchers[index][0]] = settled.value.data;
        }
      });

      setPanelResults(results);
      setActiveTaskId(taskId);
      setResult(taskData);
    } catch (err: any) {
      setError(err.message || 'Failed to load task.');
    } finally {
      setLoadingTask(false);
    }
  };

  const handleNewTask = () => {
    reset(defaultValues);
    setResult(null);
    setActiveTaskId(null);
    setPanelResults({});
    setError(null);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'valid':
        return '#4caf50';
      case 'incomplete':
        return '#ff9800';
      case 'invalid':
        return '#f44336';
      case 'valid_with_warning':
        return '#ff9800';
      default:
        return '#9e9e9e';
    }
  };

  return (
    <div>
      <TaskHistoryList
        onLoadTask={loadTask}
        onNewTask={handleNewTask}
        isLoading={loadingTask}
        currentTaskId={activeTaskId || undefined}
      />

      <form onSubmit={handleSubmit(onSubmit)}>
        <TaskFieldGroup title="Basic Task Information">
          <div style={styles.fieldContainer}>
            <label style={styles.label}>Task Name</label>
            <Controller
              name="task_name"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  style={styles.input}
                  placeholder="e.g., Band gap prediction"
                />
              )}
            />
            {errors.task_name && <span style={styles.error}>{errors.task_name.message}</span>}
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Task Description</label>
            <Controller
              name="task_description"
              control={control}
              render={({ field }) => (
                <textarea
                  {...field}
                  style={styles.textarea}
                  placeholder="e.g., Predict experimental band gaps from chemical compositions."
                  rows={3}
                />
              )}
            />
            {errors.task_description && (
              <span style={styles.error}>{errors.task_description.message}</span>
            )}
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Material System</label>
            <Controller
              name="material_system"
              control={control}
              render={({ field }) => (
                <select {...field} style={styles.select} defaultValue="">
                  <option value="" disabled>
                    Select material system
                  </option>
                  {MATERIAL_SYSTEM_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            />
            {errors.material_system && (
              <span style={styles.error}>{errors.material_system.message}</span>
            )}
          </div>
        </TaskFieldGroup>

        <TaskFieldGroup title="Dataset Information">
          <div style={styles.fieldContainer}>
            <label style={styles.label}>Dataset Description *</label>
            <Controller
              name="dataset_description"
              control={control}
              render={({ field }) => (
                <textarea
                  {...field}
                  style={styles.textarea}
                  placeholder="Describe the dataset in detail, including its source, structure, and relevant characteristics."
                  rows={3}
                />
              )}
            />
            {errors.dataset_description && (
              <span style={styles.error}>{errors.dataset_description.message}</span>
            )}
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Input Type *</label>
            <Controller
              name="input_type"
              control={control}
              render={({ field }) => (
                <select {...field} style={styles.select} defaultValue="">
                  <option value="" disabled>
                    Select input type
                  </option>
                  {INPUT_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            />
            {errors.input_type && <span style={styles.error}>{errors.input_type.message}</span>}
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Target Column *</label>
            <Controller
              name="target_column"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  style={styles.input}
                  placeholder="e.g., band_gap"
                />
              )}
            />
            {errors.target_column && (
              <span style={styles.error}>{errors.target_column.message}</span>
            )}
          </div>
        </TaskFieldGroup>

        <TaskFieldGroup title="Machine Learning Task Information">
          <div style={styles.fieldContainer}>
            <label style={styles.label}>Prediction Target *</label>
            <Controller
              name="prediction_target"
              control={control}
              render={({ field }) => (
                <input
                  {...field}
                  style={styles.input}
                  placeholder="e.g., experimental band gap"
                />
              )}
            />
            {errors.prediction_target && (
              <span style={styles.error}>{errors.prediction_target.message}</span>
            )}
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Task Type *</label>
            <Controller
              name="task_type"
              control={control}
              render={({ field }) => (
                <select {...field} style={styles.select} defaultValue="">
                  <option value="" disabled>
                    Select task type
                  </option>
                  {TASK_TYPE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            />
            {errors.task_type && <span style={styles.error}>{errors.task_type.message}</span>}
          </div>
        </TaskFieldGroup>

        <TaskFieldGroup title="Evaluation Metric Information">
          <div style={styles.fieldContainer}>
            <label style={styles.label}>Evaluation Metric</label>
            <Controller
              name="evaluation_metric"
              control={control}
              render={({ field }) => (
                <select {...field} style={styles.select} defaultValue="">
                  <option value="" disabled>
                    Select evaluation metric
                  </option>
                  {EVALUATION_METRIC_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              )}
            />
            {errors.evaluation_metric && (
              <span style={styles.error}>{errors.evaluation_metric.message}</span>
            )}
          </div>
        </TaskFieldGroup>

        <TaskFieldGroup title="User Preferences and Constraints">
          <div style={styles.fieldContainer}>
            <label style={styles.label}>User Priority</label>
            <div style={styles.checkboxGroup}>
              {USER_PRIORITY_OPTIONS.map((option) => (
                <label key={option.value} style={styles.checkboxLabel}>
                  <Controller
                    name="user_priority"
                    control={control}
                    render={({ field }) => (
                      <input
                        type="checkbox"
                        checked={field.value?.includes(option.value) || false}
                        onChange={(e) => {
                          const currentValue = field.value || [];
                          if (e.target.checked) {
                            field.onChange([...currentValue, option.value]);
                          } else {
                            field.onChange(
                              currentValue.filter((v) => v !== option.value)
                            );
                          }
                        }}
                      />
                    )}
                  />
                  <span style={styles.checkboxText}>{option.label}</span>
                </label>
              ))}
            </div>
          </div>

          <div style={styles.fieldContainer}>
            <label style={styles.label}>Constraints</label>
            <Controller
              name="constraints"
              control={control}
              render={({ field }) => (
                <textarea
                  {...field}
                  style={styles.textarea}
                  placeholder="e.g., Use interpretable models only (one per line)"
                  rows={3}
                />
              )}
            />
            {errors.constraints && (
              <span style={styles.error}>{errors.constraints.message}</span>
            )}
          </div>
        </TaskFieldGroup>

        <button type="submit" style={styles.submitButton} disabled={loading}>
          {loading ? 'Submitting...' : 'Submit Task Specification'}
        </button>
      </form>

      {error && (
        <div style={styles.errorBox}>
          <strong>Error:</strong>{' '}
          <span style={{ whiteSpace: 'pre-wrap' }}>{error}</span>
        </div>
      )}

      {result && (
        <div style={styles.resultBox}>
          <h3 style={styles.resultTitle}>Task Specification Result</h3>
          <div style={styles.resultField}>
            <strong>Task ID:</strong> {result.task_id}
          </div>
          <div style={styles.resultField}>
            <strong>Status:</strong>{' '}
            <span style={{ color: getStatusColor(result.status) }}>
              {result.status}
            </span>
          </div>
          {result.missing_fields && result.missing_fields.length > 0 && (
            <div style={styles.resultField}>
              <strong>Missing Fields:</strong>{' '}
              {result.missing_fields.join(', ')}
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
      )}

      {activeTaskId && (
        <TaskInterpretationPanel
          taskId={activeTaskId}
          initialResult={panelResults.interpretation}
          key={`interp-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <DatasetProfilePanel
          taskId={activeTaskId}
          initialResult={panelResults.datasetProfile}
          key={`dsprofile-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <WorkflowPlanPanel
          taskId={activeTaskId}
          initialResult={panelResults.workflowPlan}
          key={`wfplan-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <FeatureEngineeringPanel
          taskId={activeTaskId}
          initialResult={panelResults.featureEngineering}
          key={`fe-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <FeaturePreprocessingPanel
          taskId={activeTaskId}
          initialResult={panelResults.featurePreprocessing}
          key={`fp-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <ModelSearchContextPanel
          taskId={activeTaskId}
          initialResult={panelResults.modelSearchContext}
          key={`msctx-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <ModelSearchPlanPanel
          taskId={activeTaskId}
          initialResult={panelResults.modelSearchPlan}
          key={`msplan-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <PipelineGenerationPanel
          taskId={activeTaskId}
          initialResult={panelResults.pipelineGeneration}
          key={`pg-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <PipelineExecutionPanel
          taskId={activeTaskId}
          initialResult={panelResults.pipelineExecution}
          key={`pe-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <MetricEvaluationPanel
          taskId={activeTaskId}
          initialResult={panelResults.metricEvaluation}
          key={`me-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <ResultDiagnosisPanel
          taskId={activeTaskId}
          initialResult={panelResults.resultDiagnosis}
          key={`rd-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <WorkflowRefinementPanel
          taskId={activeTaskId}
          initialResult={panelResults.workflowRefinement}
          key={`wr-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <FinalPipelineSelectionPanel
          taskId={activeTaskId}
          initialResult={panelResults.finalPipelineSelection}
          key={`fps-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <InterpretabilityAnalysisPanel
          taskId={activeTaskId}
          initialResult={panelResults.interpretabilityAnalysis}
          key={`ia-${activeTaskId}`}
        />
      )}

      {activeTaskId && (
        <FinalOutputPanel
          taskId={activeTaskId}
          initialResult={panelResults.finalOutput}
          key={`fo-${activeTaskId}`}
        />
      )}
    </div>
  );
};

const styles = {
  fieldContainer: {
    marginBottom: '16px',
  },
  label: {
    display: 'block',
    marginBottom: '4px',
    fontWeight: 500,
    color: '#555',
  },
  input: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
  },
  textarea: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
    resize: 'vertical' as const,
  },
  select: {
    width: '100%',
    padding: '8px 12px',
    border: '1px solid #ccc',
    borderRadius: '4px',
    fontSize: '14px',
    boxSizing: 'border-box' as const,
    backgroundColor: '#fff',
  },
  checkboxGroup: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '8px',
  },
  checkboxLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    cursor: 'pointer',
  },
  checkboxText: {
    fontSize: '14px',
  },
  error: {
    color: '#f44336',
    fontSize: '12px',
    marginTop: '4px',
    display: 'block',
  },
  submitButton: {
    padding: '12px 24px',
    backgroundColor: '#1976d2',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    fontSize: '16px',
    fontWeight: 600,
    cursor: 'pointer',
    width: '100%',
    marginTop: '16px',
  },
  errorBox: {
    marginTop: '16px',
    padding: '12px',
    backgroundColor: '#ffebee',
    border: '1px solid #f44336',
    borderRadius: '4px',
    color: '#c62828',
  },
  resultBox: {
    marginTop: '24px',
    padding: '16px',
    backgroundColor: '#e8f5e9',
    border: '1px solid #4caf50',
    borderRadius: '4px',
  },
  resultTitle: {
    margin: '0 0 12px 0',
    fontSize: '18px',
    fontWeight: 600,
  },
  resultField: {
    marginBottom: '8px',
    fontSize: '14px',
  },
  messageList: {
    margin: '4px 0',
    paddingLeft: '20px',
  },
  resultJson: {
    marginTop: '16px',
  },
  pre: {
    backgroundColor: '#fff',
    padding: '12px',
    borderRadius: '4px',
    overflow: 'auto',
    fontSize: '12px',
    marginTop: '8px',
  },
};

export default TaskSpecificationForm;
