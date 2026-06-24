export const CHART_COLORS = {
  primary: '#0072B2',
  secondary: '#CC79A7',
  positive: '#009E73',
  negative: '#D55E00',
  warning: '#E69F00',
  neutral: '#6f6f6f',
  grid: '#d8d8d8',
  axis: '#222222',
  series: ['#0072B2', '#D55E00', '#009E73', '#CC79A7', '#E69F00', '#56B4E9', '#F0E442', '#000000'],
};

export const HEATMAP_COLORS = ['#3B4CC0', '#688AE2', '#9EBEFF', '#D5E5FF', '#F7F7F7', '#F6C6A8', '#E6865A', '#C94741', '#8B1A1A'];

export const FEATURE_GROUP_COLORS: Record<string, string> = {
  composition_descriptor: '#0072B2',
  structure_descriptor: '#CC79A7',
  statistical_descriptor: '#009E73',
  elemental_descriptor: '#E69F00',
  derived_feature: '#56B4E9',
  other: '#6f6f6f',
};

export const TASK_TYPE_LABELS: Record<string, string> = {
  regression: 'Regression',
  classification: 'Classification',
};

export const PUBLICATION_EXPORT_SIZES = {
  single: { label: 'Single column', widthMm: 85 },
  double: { label: 'Double column', widthMm: 178 },
};

export const PUBLICATION_CHART_STYLE = {
  fontFamily: 'Arial, Helvetica, sans-serif',
  axisColor: '#222222',
  gridColor: '#d8d8d8',
  background: '#ffffff',
  axisFontSize: 11,
  labelFontSize: 12,
  legendFontSize: 11,
};
