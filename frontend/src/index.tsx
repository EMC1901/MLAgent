import React from 'react';
import ReactDOM from 'react-dom/client';
import { ConfigProvider, App } from 'antd';
import TaskSpecificationPage from './modules/taskSpecification/pages/TaskSpecificationPage';

const theme = {
  token: {
    colorPrimary: '#1976d2',
    colorSuccess: '#43a047',
    colorWarning: '#fb8c00',
    colorError: '#e53935',
    colorInfo: '#1976d2',
    borderRadius: 6,
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    fontSize: 14,
    lineHeight: 1.5,
    colorBgContainer: '#ffffff',
    colorBorder: '#d9d9d9',
    colorBorderSecondary: '#d9d9d9',
  },
  components: {
    Card: {
      paddingLG: 16,
      headerBg: '#fafafa',
    },
    Table: {
      fontSize: 13,
      headerBg: '#f5f5f5',
      headerColor: '#333',
      borderColor: '#d9d9d9',
      cellPaddingBlock: 8,
      cellPaddingInline: 12,
    },
    Descriptions: {
      itemPaddingBottom: 8,
    },
    Tag: {
      borderRadiusSM: 12,
    },
    Button: {
      fontWeight: 600,
    },
  },
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <ConfigProvider theme={theme}>
      <App>
        <TaskSpecificationPage />
      </App>
    </ConfigProvider>
  </React.StrictMode>
);
