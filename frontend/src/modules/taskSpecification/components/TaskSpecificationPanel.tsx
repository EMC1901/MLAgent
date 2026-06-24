import React, { useState, useEffect } from 'react';
import { Button } from 'antd';
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
import TaskResultDisplay from './TaskResultDisplay';
import { createTask, getTask } from '../../../api/taskApi';
import { PanelContainer, ErrorBox } from '../../../components/shared';

interface TaskSpecificationPanelProps {
  taskId: string;
}

const defaultValues: TaskSpecificationFormData = {
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

const TaskSpecificationPanel: React.FC<TaskSpecificationPanelProps> = ({ taskId }) => {
  const [loading, setLoading] = useState(false);
  const [loadingTask, setLoadingTask] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<TaskSpecificationFormData>({
    resolver: zodResolver(taskSpecificationSchema),
    defaultValues,
  });

  useEffect(() => {
    if (taskId) {
      setLoadingTask(true);
      getTask(taskId)
        .then((res) => {
          if (res.success && res.data) {
            const d = res.data;
            reset({
              task_name: d.task_name || '',
              task_description: d.task_description || '',
              material_system: d.material_system || '',
              prediction_target: d.prediction_target || '',
              task_type: d.task_type || '',
              dataset_description: d.dataset_description || '',
              input_type: d.input_type || '',
              target_column: d.target_column || '',
              evaluation_metric: d.evaluation_metric || '',
              user_priority: d.user_priority || [],
              constraints: (d.constraints || []).join('\n'),
            });
            setResult(d);
          }
        })
        .catch(() => {})
        .finally(() => setLoadingTask(false));
    }
  }, [taskId, reset]);

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
      } else {
        setError(response.message);
      }
    } catch (err: any) {
      if (err.code === 'ERR_NETWORK' || err.message?.includes('Network Error')) {
        setError('Network Error: Cannot reach backend. Make sure the backend server is running.');
      } else if (err.response) {
        const detail = err.response.data?.detail;
        const detailMsg = typeof detail === 'object' ? (detail?.message ?? JSON.stringify(detail)) : detail;
        setError(`HTTP ${err.response.status}: ${detailMsg || err.response.data?.message || 'Unknown error'}`);
      } else {
        setError(`Request failed: ${err.message || 'Unknown error'}`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <PanelContainer
      title="Task Specification"
      description="Define your materials science modeling task. Specify the prediction target, dataset characteristics, task type, and evaluation preferences."
    >
      <form onSubmit={handleSubmit(onSubmit)}>
        <TaskFieldGroup title="Basic Task Information">
          <FormField name="task_name" control={control} label="Task Name" placeholder="e.g., Band gap prediction" error={errors.task_name?.message} />
          <FormField name="task_description" control={control} label="Task Description" type="textarea" placeholder="e.g., Predict experimental band gaps from chemical compositions." error={errors.task_description?.message} />
          <FormField name="material_system" control={control} label="Material System" type="select" placeholder="Select material system" options={MATERIAL_SYSTEM_OPTIONS} error={errors.material_system?.message} />
        </TaskFieldGroup>

        <TaskFieldGroup title="Dataset Information">
          <FormField name="dataset_description" control={control} label="Dataset Description" type="textarea" required placeholder="Describe the dataset in detail." error={errors.dataset_description?.message} />
          <FormField name="input_type" control={control} label="Input Type" type="select" required placeholder="Select input type" options={INPUT_TYPE_OPTIONS} error={errors.input_type?.message} />
          <FormField name="target_column" control={control} label="Target Column" required placeholder="e.g., band_gap" error={errors.target_column?.message} />
        </TaskFieldGroup>

        <TaskFieldGroup title="Machine Learning Task Information">
          <FormField name="prediction_target" control={control} label="Prediction Target" required placeholder="e.g., experimental band gap" error={errors.prediction_target?.message} />
          <FormField name="task_type" control={control} label="Task Type" type="select" required placeholder="Select task type" options={TASK_TYPE_OPTIONS} error={errors.task_type?.message} />
        </TaskFieldGroup>

        <TaskFieldGroup title="Evaluation Metric Information">
          <FormField name="evaluation_metric" control={control} label="Evaluation Metric" type="select" placeholder="Select evaluation metric" options={EVALUATION_METRIC_OPTIONS} error={errors.evaluation_metric?.message} />
        </TaskFieldGroup>

        <TaskFieldGroup title="User Preferences and Constraints">
          <FormField name="user_priority" control={control} label="User Priority" type="checkbox-group" options={USER_PRIORITY_OPTIONS} />
          <FormField name="constraints" control={control} label="Constraints" type="textarea" placeholder="e.g., Use interpretable models only (one per line)" />
        </TaskFieldGroup>

        <Button type="primary" htmlType="submit" loading={loading} disabled={loading || loadingTask} block size="large">
          {loading ? 'Submitting...' : 'Submit Task Specification'}
        </Button>
      </form>

      {error && <ErrorBox message={error} style={{ marginTop: 16 }} />}
      {result && <TaskResultDisplay result={result} />}
    </PanelContainer>
  );
};

export default TaskSpecificationPanel;
