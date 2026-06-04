import React from 'react';
import { ConfusionMatrixData } from '../../types';

interface Props {
  data: ConfusionMatrixData | null;
  taskType: string;
}

const ConfusionMatrixChart: React.FC<Props> = ({ data, taskType }) => {
  if (taskType !== 'classification') {
    return <p style={{ color: '#999' }}>Confusion matrix is only available for classification tasks.</p>;
  }
  if (!data || !data.labels.length || !data.matrix.length) {
    return <p style={{ color: '#999' }}>No confusion matrix data available.</p>;
  }

  const { labels, matrix } = data;
  const maxCount = Math.max(...matrix.flat());
  const cellSize = Math.max(32, Math.min(80, 500 / labels.length));

  const colorIntensity = (count: number): string => {
    const t = maxCount > 0 ? count / maxCount : 0;
    const r = Math.round(255 * (1 - t * 0.8));
    const g = Math.round(255 * (1 - t * 0.7));
    const b = Math.round(255 * (1 - t * 0.9));
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div style={{ overflowX: 'auto', fontSize: 12 }}>
      <div style={{ display: 'inline-block' }}>
        {/* Header row */}
        <div style={{ display: 'flex', marginLeft: 60 }}>
          <div style={{ width: cellSize, textAlign: 'center', fontWeight: 600, fontSize: 11, color: '#666', padding: '4px 0' }}>
            Predicted
          </div>
        </div>
        {/* Matrix */}
        <div style={{ display: 'flex' }}>
          {/* Y-axis */}
          <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', width: 55 }}>
            <div style={{ transform: 'rotate(-90deg)', whiteSpace: 'nowrap', textAlign: 'center', fontSize: 11, color: '#666', fontWeight: 600 }}>
              Actual
            </div>
          </div>
          {/* Cells */}
          <div>
            {/* X labels */}
            <div style={{ display: 'flex' }}>
              {labels.map((l, i) => (
                <div key={i} style={{
                  width: cellSize, textAlign: 'center', fontSize: 10, fontWeight: 600,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  padding: '2px 0',
                }} title={l}>
                  {l.length > 8 ? l.slice(0, 8) + '..' : l}
                </div>
              ))}
            </div>
            {/* Matrix rows */}
            {matrix.map((row, ri) => (
              <div key={ri} style={{ display: 'flex', alignItems: 'stretch' }}>
                <div style={{
                  width: 48, display: 'flex', alignItems: 'center', justifyContent: 'flex-end',
                  fontSize: 10, fontWeight: 600, paddingRight: 4,
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }} title={labels[ri]}>
                  {labels[ri].length > 6 ? labels[ri].slice(0, 6) + '.' : labels[ri]}
                </div>
                {row.map((val, ci) => (
                  <div
                    key={ci}
                    title={`Actual: ${labels[ri]}  Predicted: ${labels[ci]}  Count: ${val}`}
                    style={{
                      width: cellSize,
                      height: cellSize,
                      backgroundColor: colorIntensity(val),
                      border: '1px solid #fff',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: cellSize > 40 ? 13 : 10,
                      fontWeight: ri === ci ? 700 : 400,
                      color: val > maxCount * 0.4 ? '#fff' : '#333',
                    }}
                  >
                    {val}
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfusionMatrixChart;
