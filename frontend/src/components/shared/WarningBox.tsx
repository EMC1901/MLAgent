import React from 'react';
import { Alert } from 'antd';

interface WarningBoxProps {
  warnings: string[];
  style?: React.CSSProperties;
}

const WarningBox: React.FC<WarningBoxProps> = ({ warnings, style }) => {
  if (!warnings || warnings.length === 0) return null;
  return (
    <Alert
      type="warning"
      message={`Warning${warnings.length > 1 ? 's' : ''}`}
      description={
        <ul style={{ margin: '4px 0', paddingLeft: 20 }}>
          {warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      }
      showIcon
      style={{ marginBottom: 16, ...style }}
    />
  );
};

export default WarningBox;
