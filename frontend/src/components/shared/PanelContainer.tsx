import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

interface PanelContainerProps {
  title: string;
  description?: string;
  /** Left accent border color. Defaults to #1976d2. */
  accentColor?: string;
  children: React.ReactNode;
  /** Render the title as this heading level. Defaults to 3 (h3). */
  headingLevel?: 1 | 2 | 3 | 4 | 5;
}

const PanelContainer: React.FC<PanelContainerProps> = ({
  title,
  description,
  accentColor = '#1976d2',
  children,
  headingLevel = 3,
}) => (
  <Card
    style={{
      marginTop: 24,
      borderLeft: `4px solid ${accentColor}`,
    }}
    styles={{ body: { padding: 16 } }}
    title={
      <Title
        level={headingLevel}
        id={`panel-${title.replace(/\s+/g, '-').toLowerCase()}`}
        style={{ margin: 0, fontSize: 17, fontWeight: 600 }}
      >
        {title}
      </Title>
    }
  >
    <div aria-live="polite" aria-atomic="true">
      {description && (
        <Paragraph
          type="secondary"
          style={{ margin: '0 0 16px 0', fontSize: 13, lineHeight: 1.5 }}
        >
          {description}
        </Paragraph>
      )}
      {children}
    </div>
  </Card>
);

export default PanelContainer;
