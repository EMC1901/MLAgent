import React from 'react';
import TaskSpecificationForm from '../components/TaskSpecificationForm';

const TaskSpecificationPage: React.FC = () => {
  return (
    <div style={styles.page}>
      <header style={styles.header}>
        <h1 style={styles.title}>MLAgent - Task Specification</h1>
        <p style={styles.subtitle}>
          Submit your materials machine learning task requirements
        </p>
      </header>
      <main style={styles.main}>
        <TaskSpecificationForm />
      </main>
    </div>
  );
};

const styles = {
  page: {
    minHeight: '100vh',
    backgroundColor: '#f5f5f5',
  },
  header: {
    backgroundColor: '#1976d2',
    color: '#fff',
    padding: '24px',
    textAlign: 'center' as const,
  },
  title: {
    margin: '0 0 8px 0',
    fontSize: '28px',
    fontWeight: 600,
  },
  subtitle: {
    margin: 0,
    fontSize: '16px',
    opacity: 0.9,
  },
  main: {
    maxWidth: '800px',
    margin: '32px auto',
    padding: '0 16px',
  },
};

export default TaskSpecificationPage;
