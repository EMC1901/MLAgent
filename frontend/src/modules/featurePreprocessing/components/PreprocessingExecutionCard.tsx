import React from 'react';
import { Card, Descriptions, Tag } from 'antd';
import { PreprocessingExecution } from '../types';

interface Props {
  execution: PreprocessingExecution;
}

const PreprocessingExecutionCard: React.FC<Props> = ({ execution }) => {
  return (
    <Card title="Preprocessing Execution" size="small" style={{ marginBottom: 16 }}>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Imputation">
          {execution.imputation.executed ? (
            <Tag color="blue">
              Executed ({execution.imputation.strategy})
            </Tag>
          ) : (
            <Tag>Not Executed</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Scaling">
          {execution.scaling.executed ? (
            <Tag color="blue">
              Executed ({execution.scaling.strategy})
            </Tag>
          ) : (
            <Tag>Not Executed</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Categorical Encoding">
          {execution.categorical_encoding.executed ? (
            <Tag color="blue">Executed</Tag>
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
        <Descriptions.Item label="Feature Selection">
          {execution.feature_selection.executed ? (
            <Tag color="blue">
              Executed ({execution.feature_selection.strategy})
              {execution.feature_selection.columns_dropped.length > 0 &&
                ` - ${execution.feature_selection.columns_dropped.length} dropped`}
            </Tag>
          ) : (
            <Tag>None</Tag>
          )}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
};

export default PreprocessingExecutionCard;
