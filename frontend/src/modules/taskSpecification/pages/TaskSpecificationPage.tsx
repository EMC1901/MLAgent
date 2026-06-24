import React from 'react';
import { Layout, Typography } from 'antd';
import TaskSpecificationForm from '../components/TaskSpecificationForm';

const { Header: AntHeader } = Layout;
const { Title, Paragraph } = Typography;

const TaskSpecificationPage: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh', backgroundColor: '#f5f5f5' }}>
      <AntHeader
        style={{
          backgroundColor: '#1976d2',
          height: 'auto',
          padding: '24px',
          textAlign: 'center',
        }}
      >
        <Title level={1} style={{ color: '#fff', margin: '0 0 8px 0', fontSize: 28, fontWeight: 600 }}>
          Mat-AIDE
        </Title>
        <Paragraph
          style={{ color: 'rgba(255,255,255,0.9)', margin: 0, fontSize: 16 }}
        >
          An AI-driven platform for autonomous and interpretable data-driven modeling in materials science
        </Paragraph>
      </AntHeader>
      <Layout.Content
        style={{ maxWidth: 1100, margin: '32px auto', padding: '0 16px', width: '100%' }}
      >
        <TaskSpecificationForm />
      </Layout.Content>
    </Layout>
  );
};

export default TaskSpecificationPage;
