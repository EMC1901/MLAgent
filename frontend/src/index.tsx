import React from 'react';
import ReactDOM from 'react-dom/client';
import TaskSpecificationPage from './modules/taskSpecification/pages/TaskSpecificationPage';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <TaskSpecificationPage />
  </React.StrictMode>
);
