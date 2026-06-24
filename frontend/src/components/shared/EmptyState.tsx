import React from 'react';
import { Empty } from 'antd';

interface EmptyStateProps {
  description?: string;
  children?: React.ReactNode;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  description = 'No data available',
  children,
}) => <Empty description={description}>{children}</Empty>;

export default EmptyState;
