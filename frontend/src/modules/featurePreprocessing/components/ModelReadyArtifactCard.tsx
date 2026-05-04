import React, { useState } from 'react';
import { Card, Descriptions, Button, Table, Spin } from 'antd';
import { EyeOutlined } from '@ant-design/icons';
import { ModelReadyArtifact, PreprocessingPipelineArtifact, PreviewResponse } from '../types';
import { getModelReadyPreview } from '../../../api/featurePreprocessingApi';

interface Props {
  artifact: ModelReadyArtifact;
  pipelineArtifact?: PreprocessingPipelineArtifact | null;
  preprocessingId: string;
}

const ModelReadyArtifactCard: React.FC<Props> = ({
  artifact,
  pipelineArtifact,
  preprocessingId,
}) => {
  const [preview, setPreview] = useState<PreviewResponse | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  const handlePreview = async () => {
    setPreviewLoading(true);
    try {
      const resp = await getModelReadyPreview(preprocessingId);
      if (resp.success) {
        setPreview(resp.data);
      }
    } catch {
      // ignore
    } finally {
      setPreviewLoading(false);
    }
  };

  const previewColumns =
    preview?.columns.map((col: string) => ({
      title: col,
      dataIndex: col,
      key: col,
      ellipsis: true,
      width: 150,
    })) || [];

  return (
    <Card
      title="Model-Ready Artifact"
      size="small"
      style={{ marginBottom: 16 }}
      extra={
        <Button
          icon={<EyeOutlined />}
          onClick={handlePreview}
          loading={previewLoading}
          size="small"
        >
          Preview
        </Button>
      }
    >
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Artifact ID">{artifact.artifact_id}</Descriptions.Item>
        <Descriptions.Item label="Storage Type">{artifact.storage_type}</Descriptions.Item>
        <Descriptions.Item label="Samples">{artifact.n_samples}</Descriptions.Item>
        <Descriptions.Item label="Features">{artifact.n_features}</Descriptions.Item>
        <Descriptions.Item label="Target Column">{artifact.target_column}</Descriptions.Item>
        <Descriptions.Item label="File Path" span={2}>
          {artifact.file_path}
        </Descriptions.Item>
        {pipelineArtifact && (
          <>
            <Descriptions.Item label="Pipeline Artifact ID">
              {pipelineArtifact.artifact_id}
            </Descriptions.Item>
            <Descriptions.Item label="Pipeline Storage">
              {pipelineArtifact.storage_type}
            </Descriptions.Item>
            <Descriptions.Item label="Pipeline Path" span={2}>
              {pipelineArtifact.file_path}
            </Descriptions.Item>
          </>
        )}
      </Descriptions>

      {previewLoading && <Spin style={{ marginTop: 16 }} />}
      {preview && (
        <div style={{ marginTop: 16 }}>
          <Table
            dataSource={preview.rows.map((row, i) => ({ ...row, key: i }))}
            columns={previewColumns}
            size="small"
            scroll={{ x: 'max-content', y: 300 }}
            pagination={false}
          />
          <div style={{ marginTop: 8, fontSize: 12, color: '#888' }}>
            Showing {preview.preview_rows} of {preview.total_rows} rows
          </div>
        </div>
      )}
    </Card>
  );
};

export default ModelReadyArtifactCard;
