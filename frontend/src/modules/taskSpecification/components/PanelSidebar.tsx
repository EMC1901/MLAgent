import React, { useState } from 'react';
import { Layout, Menu, Button } from 'antd';
import {
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  EditOutlined,
  ReadOutlined,
  DatabaseOutlined,
  ApartmentOutlined,
  ExperimentOutlined,
  ControlOutlined,
  SearchOutlined,
  BuildOutlined,
  ThunderboltOutlined,
  DashboardOutlined,
  NodeIndexOutlined,
  EyeOutlined,
  BarChartOutlined,
  FileProtectOutlined,
} from '@ant-design/icons';
import type { MenuProps } from 'antd';
import TaskPanelOrchestrator, { PANEL_DEFS } from './TaskPanelOrchestrator';

const { Sider, Content } = Layout;

interface PanelSidebarProps {
  activeTaskId: string;
  panelResults: Record<string, any>;
  onRerunComplete: () => Promise<void>;
  onNewTaskCreated?: (taskId: string) => void;
}

const menuIconMap: Record<string, React.ReactNode> = {
  taskSpecification: <EditOutlined />,
  interpretation: <ReadOutlined />,
  datasetProfile: <DatabaseOutlined />,
  workflowPlan: <ApartmentOutlined />,
  featureEngineering: <ExperimentOutlined />,
  featurePreprocessing: <ControlOutlined />,
  modelSearchContext: <SearchOutlined />,
  pipelineGeneration: <BuildOutlined />,
  pipelineExecution: <ThunderboltOutlined />,
  metricEvaluation: <DashboardOutlined />,
  iterationDecision: <NodeIndexOutlined />,
  interpretabilityAnalysis: <EyeOutlined />,
  visualization: <BarChartOutlined />,
  finalOutput: <FileProtectOutlined />,
};

const PanelSidebar: React.FC<PanelSidebarProps> = ({
  activeTaskId, panelResults, onRerunComplete, onNewTaskCreated,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKey, setSelectedKey] = useState('taskSpecification');

  const menuItems: MenuProps['items'] = PANEL_DEFS.map((p) => ({
    key: p.key,
    icon: menuIconMap[p.key],
    label: p.label,
  }));

  return (
    <Layout style={{ minHeight: 400, background: 'transparent' }}>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={null}
        width={220}
        style={{
          background: '#fafafa',
          borderRight: '1px solid #d9d9d9',
        }}
      >
        <div style={{ padding: '8px 16px', borderBottom: '1px solid #d9d9d9' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ width: '100%', textAlign: 'center' }}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          />
        </div>
        <Menu
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => setSelectedKey(key)}
          style={{
            background: 'transparent',
            borderRight: 'none',
          }}
        />
      </Sider>
      <Content style={{ padding: '0 0 0 16px', overflow: 'auto' }}>
        <TaskPanelOrchestrator
          activeTaskId={activeTaskId}
          panelResults={panelResults}
          onRerunComplete={onRerunComplete}
          onNewTaskCreated={onNewTaskCreated}
          selectedPanelKey={selectedKey}
        />
      </Content>
    </Layout>
  );
};

export default PanelSidebar;
