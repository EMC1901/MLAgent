import React, { useRef, useState } from 'react';
import { Button, Card, Space, Tooltip, message } from 'antd';
import { DownloadOutlined, FileImageOutlined, FullscreenOutlined } from '@ant-design/icons';
import { exportChart } from '../utils/exportChart';

interface ExportSettings {
  dpi: number;
  widthMm: number;
}

interface PublicationChartFrameProps {
  title: string;
  filenameBase: string;
  exportSettings: ExportSettings;
  children: React.ReactNode;
  onFullscreen: (payload: { title: string; children: React.ReactNode }) => void;
}

const PublicationChartFrame: React.FC<PublicationChartFrameProps> = ({
  title,
  filenameBase,
  exportSettings,
  children,
  onFullscreen,
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState<'svg' | 'png' | null>(null);

  const handleExport = async (format: 'svg' | 'png') => {
    if (!chartRef.current) return;
    try {
      setExporting(format);
      await exportChart(chartRef.current, {
        filenameBase,
        format,
        dpi: exportSettings.dpi,
        widthMm: exportSettings.widthMm,
      });
    } catch (err: any) {
      message.error(err?.message || 'Chart export failed.');
    } finally {
      setExporting(null);
    }
  };

  return (
    <Card
      size="small"
      title={title}
      extra={
        <Space size={4}>
          <Tooltip title="Download publication SVG">
            <Button
              size="small"
              icon={<DownloadOutlined />}
              loading={exporting === 'svg'}
              onClick={() => handleExport('svg')}
              aria-label={`Download ${title} as SVG`}
            />
          </Tooltip>
          <Tooltip title={`Download ${exportSettings.dpi} dpi PNG`}>
            <Button
              size="small"
              icon={<FileImageOutlined />}
              loading={exporting === 'png'}
              onClick={() => handleExport('png')}
              aria-label={`Download ${title} as PNG`}
            />
          </Tooltip>
          <Tooltip title="View fullscreen">
            <Button
              size="small"
              icon={<FullscreenOutlined />}
              onClick={() => onFullscreen({ title, children })}
              aria-label={`View ${title} fullscreen`}
            />
          </Tooltip>
        </Space>
      }
    >
      <div
        ref={chartRef}
        style={{
          background: '#fff',
          color: '#111',
          fontFamily: 'Arial, Helvetica, sans-serif',
          letterSpacing: 0,
        }}
      >
        {children}
      </div>
    </Card>
  );
};

export default PublicationChartFrame;
