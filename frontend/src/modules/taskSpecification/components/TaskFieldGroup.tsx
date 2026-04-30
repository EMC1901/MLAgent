import React from 'react';

interface TaskFieldGroupProps {
  title: string;
  children: React.ReactNode;
}

const TaskFieldGroup: React.FC<TaskFieldGroupProps> = ({ title, children }) => {
  return (
    <div style={styles.container}>
      <h3 style={styles.title}>{title}</h3>
      {children}
    </div>
  );
};

const styles = {
  container: {
    marginBottom: '24px',
    padding: '16px',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    backgroundColor: '#fafafa',
  },
  title: {
    margin: '0 0 16px 0',
    fontSize: '18px',
    fontWeight: 600,
    color: '#333',
    borderBottom: '2px solid #1976d2',
    paddingBottom: '8px',
  },
};

export default TaskFieldGroup;
