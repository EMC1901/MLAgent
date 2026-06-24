import React from 'react';
import { Tag } from 'antd';

interface StatusBadgeProps {
  label: string;
  color?: string;
}

const colorMap: Record<string, string> = {
  // Status colors — maps common statuses to Ant Design Tag colors
  valid: 'success',
  analyzed: 'success',
  diagnosed: 'success',
  completed: 'success',
  preprocessed: 'success',
  interpreted: 'success',
  profiled: 'success',

  valid_with_warning: 'warning',
  analyzed_with_warning: 'warning',
  diagnosed_with_warning: 'warning',
  completed_with_warning: 'warning',
  preprocessed_with_warning: 'warning',
  interpreted_with_warning: 'warning',
  profiled_with_warning: 'warning',

  failed: 'error',
  invalid: 'error',
  incomplete: 'warning',
  blocked: 'default',
  pending: 'default',
  received: 'default',
  cancelled: 'default',
  skipped: 'default',

  analyzing: 'processing',
  diagnosing: 'processing',
  running: 'processing',
  diagnosing_in_progress: 'processing',
};

const StatusBadge: React.FC<StatusBadgeProps> = ({ label, color }) => {
  const antdColor = color
    ? undefined // custom color passed directly
    : colorMap[label.toLowerCase()] || undefined;

  return (
    <Tag color={color || antdColor} style={{ margin: 0 }}>
      {label}
    </Tag>
  );
};

export default StatusBadge;
