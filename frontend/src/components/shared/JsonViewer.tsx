import React from 'react';
import { Typography } from 'antd';

const { Paragraph } = Typography;

interface JsonViewerProps {
  data: unknown;
  maxHeight?: number;
}

const JsonViewer: React.FC<JsonViewerProps> = ({ data, maxHeight = 500 }) => (
  <Paragraph style={{ margin: 0 }}>
    <pre
      tabIndex={0}
      role="region"
      aria-label="JSON output"
      style={{
        backgroundColor: '#263238',
        color: '#aed581',
        padding: 12,
        borderRadius: 4,
        overflow: 'auto',
        fontSize: 12,
        maxHeight,
        margin: 0,
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  </Paragraph>
);

export default JsonViewer;
