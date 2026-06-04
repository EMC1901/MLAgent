export const CHART_COLORS = {
  primary: '#1976d2',
  secondary: '#7b1fa2',
  positive: '#4caf50',
  negative: '#f44336',
  warning: '#ff9800',
  neutral: '#9e9e9e',
  series: ['#1976d2', '#7b1fa2', '#4caf50', '#ff9800', '#f44336', '#00bcd4', '#795548', '#607d8b'],
};

export const HEATMAP_COLORS = ['#d73027', '#f46d43', '#fdae61', '#fee090', '#ffffbf', '#e0f3f8', '#abd9e9', '#74add1', '#4575b4'];

export const FEATURE_GROUP_COLORS: Record<string, string> = {
  composition_descriptor: '#1976d2',
  structure_descriptor: '#7b1fa2',
  statistical_descriptor: '#4caf50',
  elemental_descriptor: '#ff9800',
  derived_feature: '#00bcd4',
  other: '#9e9e9e',
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  regression: 'Regression',
  classification: 'Classification',
};
