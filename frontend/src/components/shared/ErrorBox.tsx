import React from 'react';
import { Alert } from 'antd';

interface ErrorBoxProps {
  message: string;
  style?: React.CSSProperties;
}

const ErrorBox: React.FC<ErrorBoxProps> = ({ message, style }) => (
  <Alert
    type="error"
    message="Error"
    description={message}
    showIcon
    style={{ marginBottom: 16, ...style }}
  />
);

export default ErrorBox;
