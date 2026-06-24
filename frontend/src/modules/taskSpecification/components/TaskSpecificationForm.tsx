import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
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
import FormField from './FormField';
import TaskFieldGroup from './TaskFieldGroup';
import TaskHistoryList from './TaskHistoryList';
import TaskResultDisplay from './TaskResultDisplay';
import PanelSidebar from './PanelSidebar';
import { createTask, getTask, TaskSpecificationResponse } from '../../../api/taskApi';
import { getLatestInterpretation } from '../../../api/taskInterpretationApi';
import { getLatestDatasetProfileByTaskId } from '../../../api/datasetProfileApi';
import { getLatestWorkflowPlanByTaskId } from '../../../api/workflowPlanningApi';
import { getLatestFeatureEngineeringByTaskId } from '../../../api/featureEngineeringApi';
import { getLatestFeaturePreprocessingByTaskId } from '../../../api/featurePreprocessingApi';
import { getLatestModelSearchContextByTaskId } from '../../../api/modelSearchContextApi';
import { getLatestPipelineGenerationByTaskId } from '../../../api/pipelineGenerationApi';
import { getLatestPipelineExecutionByTaskId } from '../../../api/pipelineExecutionApi';
import { getLatestMetricEvaluationByTaskId } from '../../../api/metricEvaluationApi';
import { getLatestIterationDecisionByTaskId } from '../../../api/iterationDecisionApi';
import { getLatestInterpretabilityAnalysis } from '../../../api/interpretabilityAnalysisApi';
import { getLatestFinalOutput } from '../../../api/finalOutputApi';

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
  user_priority: [] as string[],
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
    formState: { errors },
  } = useForm<TaskSpecificationFormData>({
    resolver: zodResolver(taskSpecificationSchema),
    defaultValues,
  });

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
        setError('Request timeout (>10min): Backend took too long to respond. Check if the database is running.');
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

  const fetchAllPanels = async (taskId: string): Promise<Record<string, any>> => {
    const results: Record<string, any> = {};

    const fetchers: [string, () => Promise<any>][] = [
      ['interpretation', () => getLatestInterpretation(taskId)],
      ['datasetProfile', () => getLatestDatasetProfileByTaskId(taskId)],
      ['workflowPlan', () => getLatestWorkflowPlanByTaskId(taskId)],
      ['featureEngineering', () => getLatestFeatureEngineeringByTaskId(taskId)],
      ['featurePreprocessing', () => getLatestFeaturePreprocessingByTaskId(taskId)],
      ['modelSearchContext', () => getLatestModelSearchContextByTaskId(taskId)],
      ['pipelineGeneration', () => getLatestPipelineGenerationByTaskId(taskId)],
      ['pipelineExecution', () => getLatestPipelineExecutionByTaskId(taskId)],
      ['metricEvaluation', () => getLatestMetricEvaluationByTaskId(taskId)],
      ['iterationDecision', () => getLatestIterationDecisionByTaskId(taskId)],
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

    return results;
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

      const results = await fetchAllPanels(taskId);
      setPanelResults(results);
      setActiveTaskId(taskId);
      setResult(taskData);
    } catch (err: any) {
      setError(err.message || 'Failed to load task.');
    } finally {
      setLoadingTask(false);
    }
  };

  const handleRerunComplete = async () => {
    if (!activeTaskId) return;
    const results = await fetchAllPanels(activeTaskId);
    setPanelResults(results);
  };

  const handleNewTaskCreated = async (newTaskId: string) => {
    setActiveTaskId(newTaskId);
    const results = await fetchAllPanels(newTaskId);
    setPanelResults(results);
  };

  const handleNewTask = () => {
    reset(defaultValues);
    setResult(null);
    setActiveTaskId(null);
    setPanelResults({});
    setError(null);
  };

  return (
    <div>
      <TaskHistoryList
        onLoadTask={loadTask}
        onNewTask={handleNewTask}
        isLoading={loadingTask}
        currentTaskId={activeTaskId || undefined}
      />

      {!activeTaskId && <>
      <form onSubmit={handleSubmit(onSubmit)}>
        <TaskFieldGroup title="Basic Task Information">
          <FormField
            name="task_name" control={control} label="Task Name"
            placeholder="e.g., Band gap prediction"
            error={errors.task_name?.message}
          />
          <FormField
            name="task_description" control={control} label="Task Description"
            type="textarea" placeholder="e.g., Predict experimental band gaps from chemical compositions."
            error={errors.task_description?.message}
          />
          <FormField
            name="material_system" control={control} label="Material System"
            type="select" placeholder="Select material system"
            options={MATERIAL_SYSTEM_OPTIONS}
            error={errors.material_system?.message}
          />
        </TaskFieldGroup>

        <TaskFieldGroup title="Dataset Information">
          <FormField
            name="dataset_description" control={control} label="Dataset Description"
            type="textarea" required
            placeholder="Describe the dataset in detail, including its source, structure, and relevant characteristics."
            error={errors.dataset_description?.message}
          />
          <FormField
            name="input_type" control={control} label="Input Type"
            type="select" required
            placeholder="Select input type"
            options={INPUT_TYPE_OPTIONS}
            error={errors.input_type?.message}
          />
          <FormField
            name="target_column" control={control} label="Target Column"
            required placeholder="e.g., band_gap"
            error={errors.target_column?.message}
          />
        </TaskFieldGroup>

        <TaskFieldGroup title="Machine Learning Task Information">
          <FormField
            name="prediction_target" control={control} label="Prediction Target"
            required placeholder="e.g., experimental band gap"
            error={errors.prediction_target?.message}
          />
          <FormField
            name="task_type" control={control} label="Task Type"
            type="select" required
            placeholder="Select task type"
            options={TASK_TYPE_OPTIONS}
            error={errors.task_type?.message}
          />
        </TaskFieldGroup>

        <TaskFieldGroup title="Evaluation Metric Information">
          <FormField
            name="evaluation_metric" control={control} label="Evaluation Metric"
            type="select" placeholder="Select evaluation metric"
            options={EVALUATION_METRIC_OPTIONS}
            error={errors.evaluation_metric?.message}
          />
        </TaskFieldGroup>

        <TaskFieldGroup title="User Preferences and Constraints">
          <FormField
            name="user_priority" control={control} label="User Priority"
            type="checkbox-group"
            options={USER_PRIORITY_OPTIONS}
          />
          <FormField
            name="constraints" control={control} label="Constraints"
            type="textarea"
            placeholder="e.g., Use interpretable models only (one per line)"
          />
        </TaskFieldGroup>

        <button
          type="submit"
          style={{
            ...submitButtonStyle,
            opacity: loading || loadingTask ? 0.6 : 1,
            cursor: loading || loadingTask ? 'not-allowed' : 'pointer',
          }}
          disabled={loading || loadingTask}
        >
          {loading ? 'Submitting...' : 'Submit Task Specification'}
        </button>
      </form>

      {error && (
        <div style={errorBoxStyle} role="alert">
          <strong>Error:</strong>{' '}
          <span style={{ whiteSpace: 'pre-wrap' }}>{error}</span>
        </div>
      )}

      {result && <TaskResultDisplay result={result} />}
      </>}

      {activeTaskId && (
        <PanelSidebar
          activeTaskId={activeTaskId}
          panelResults={panelResults}
          onRerunComplete={handleRerunComplete}
          onNewTaskCreated={handleNewTaskCreated}
        />
      )}
    </div>
  );
};

const submitButtonStyle: React.CSSProperties = {
  padding: '12px 24px',
  backgroundColor: '#1976d2',
  color: '#fff',
  border: 'none',
  borderRadius: '4px',
  fontSize: '16px',
  fontWeight: 600,
  width: '100%',
  marginTop: '16px',
};

const errorBoxStyle: React.CSSProperties = {
  marginTop: '16px',
  padding: '12px',
  backgroundColor: '#ffebee',
  border: '1px solid #f44336',
  borderRadius: '4px',
  color: '#c62828',
};

export default TaskSpecificationForm;
