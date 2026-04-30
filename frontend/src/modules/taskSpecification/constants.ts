import { z } from 'zod';

export const taskSpecificationSchema = z.object({
  task_name: z.string().optional(),
  task_description: z.string().optional(),
  material_system: z.string().optional(),
  prediction_target: z.string().min(1, 'Prediction target is required'),
  task_type: z.string().min(1, 'Task type is required'),
  dataset_description: z.string().min(1, 'Dataset description is required'),
  input_type: z.string().min(1, 'Input type is required'),
  target_column: z.string().min(1, 'Target column is required'),
  evaluation_metric: z.string().optional(),
  user_priority: z.array(z.string()).optional(),
  constraints: z.string().optional(),
});

export type TaskSpecificationFormData = z.infer<typeof taskSpecificationSchema>;

export const TASK_TYPE_OPTIONS = [
  { label: 'Regression', value: 'regression' },
  { label: 'Classification', value: 'classification' },
  { label: 'Ranking', value: 'ranking' },
];

export const INPUT_TYPE_OPTIONS = [
  { label: 'Chemical composition', value: 'composition' },
  { label: 'Crystal structure', value: 'structure' },
  { label: 'Descriptor table', value: 'descriptor_table' },
  { label: 'Text-derived features', value: 'text_features' },
];

export const MATERIAL_SYSTEM_OPTIONS = [
  { label: 'Inorganic crystals', value: 'inorganic crystals' },
  { label: 'Organic molecules', value: 'organic molecules' },
  { label: 'Metal alloys', value: 'metal alloys' },
  { label: 'Polymers', value: 'polymers' },
  { label: 'Ceramics', value: 'ceramics' },
  { label: 'Semiconductors', value: 'semiconductors' },
];

export const EVALUATION_METRIC_OPTIONS = [
  { label: 'Mean Absolute Error (MAE)', value: 'MAE' },
  { label: 'Root Mean Squared Error (RMSE)', value: 'RMSE' },
  { label: 'R-squared (R2)', value: 'R2' },
  { label: 'Accuracy', value: 'Accuracy' },
  { label: 'F1 score', value: 'F1' },
  { label: 'ROC-AUC', value: 'ROC-AUC' },
  { label: 'Spearman', value: 'Spearman' },
  { label: 'NDCG', value: 'NDCG' },
  { label: 'Top-k recall', value: 'Top-k recall' },
];

export const USER_PRIORITY_OPTIONS = [
  { label: 'Accuracy', value: 'accuracy' },
  { label: 'Interpretability', value: 'interpretability' },
  { label: 'Speed', value: 'speed' },
  { label: 'Robustness', value: 'robustness' },
];
