import React from 'react';
import { ConfusionMatrixData } from '../../types';
import { PUBLICATION_CHART_STYLE } from '../../constants';

interface Props {
  data: ConfusionMatrixData | null;
  taskType: string;
}

const truncate = (value: string, max = 12): string =>
  value.length > max ? `${value.slice(0, max - 3)}...` : value;

const ConfusionMatrixChart: React.FC<Props> = ({ data, taskType }) => {
  if (taskType !== 'classification') {
    return <p style={{ color: '#999' }}>Confusion matrix is only available for classification tasks.</p>;
  }
  if (!data || !data.labels.length || !data.matrix.length) {
    return <p style={{ color: '#999' }}>No confusion matrix data available.</p>;
  }

  const { labels, matrix } = data;
  const n = labels.length;
  const maxCount = Math.max(...matrix.flat(), 1);
  const cellSize = Math.max(42, Math.min(72, 560 / n));
  const left = 128;
  const top = 82;
  const right = 60;
  const bottom = 78;
  const width = left + n * cellSize + right;
  const height = top + n * cellSize + bottom;

  const colorIntensity = (count: number): string => {
    const t = maxCount > 0 ? count / maxCount : 0;
    const r = Math.round(247 - t * 185);
    const g = Math.round(247 - t * 122);
    const b = Math.round(247 - t * 47);
    return `rgb(${r},${g},${b})`;
  };

  return (
    <div style={{ overflowX: 'auto', background: '#fff' }}>
      <svg
        className="publication-svg"
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Confusion matrix with ${n} classes`}
        style={{ fontFamily: PUBLICATION_CHART_STYLE.fontFamily, background: '#fff' }}
      >
        <rect x={0} y={0} width={width} height={height} fill="#fff" />
        <text x={left + (n * cellSize) / 2} y={24} textAnchor="middle" fontSize={14} fontWeight={700} fill="#111">
          Confusion matrix
        </text>
        <text x={left + (n * cellSize) / 2} y={54} textAnchor="middle" fontSize={12} fontWeight={700} fill="#222">
          Predicted label
        </text>
        <text
          x={24}
          y={top + (n * cellSize) / 2}
          textAnchor="middle"
          fontSize={12}
          fontWeight={700}
          fill="#222"
          transform={`rotate(-90 24 ${top + (n * cellSize) / 2})`}
        >
          Actual label
        </text>
        {labels.map((label, i) => (
          <text
            key={`x-${label}-${i}`}
            x={left + i * cellSize + cellSize / 2}
            y={top - 10}
            textAnchor="middle"
            fontSize={10}
            fontWeight={700}
            fill="#222"
          >
            <title>{label}</title>
            {truncate(label)}
          </text>
        ))}
        {labels.map((label, i) => (
          <text
            key={`y-${label}-${i}`}
            x={left - 10}
            y={top + i * cellSize + cellSize * 0.62}
            textAnchor="end"
            fontSize={10}
            fontWeight={700}
            fill="#222"
          >
            <title>{label}</title>
            {truncate(label, 15)}
          </text>
        ))}
        {matrix.map((row, ri) =>
          row.map((val, ci) => {
            const x = left + ci * cellSize;
            const y = top + ri * cellSize;
            const normalized = row.reduce((sum, item) => sum + item, 0) > 0
              ? val / row.reduce((sum, item) => sum + item, 0)
              : 0;
            return (
              <g key={`${ri}-${ci}`}>
                <rect
                  x={x}
                  y={y}
                  width={cellSize}
                  height={cellSize}
                  fill={colorIntensity(val)}
                  stroke="#fff"
                  strokeWidth={1}
                >
                  <title>{`Actual: ${labels[ri]}, Predicted: ${labels[ci]}, Count: ${val}, Row fraction: ${(normalized * 100).toFixed(1)}%`}</title>
                </rect>
                <text
                  x={x + cellSize / 2}
                  y={y + cellSize * 0.48}
                  textAnchor="middle"
                  fontSize={12}
                  fontWeight={ri === ci ? 700 : 500}
                  fill={val > maxCount * 0.48 ? '#fff' : '#111'}
                >
                  {val}
                </text>
                <text
                  x={x + cellSize / 2}
                  y={y + cellSize * 0.72}
                  textAnchor="middle"
                  fontSize={9}
                  fill={val > maxCount * 0.48 ? '#fff' : '#333'}
                >
                  {(normalized * 100).toFixed(0)}%
                </text>
              </g>
            );
          })
        )}
        <text x={left} y={height - 20} fontSize={10} fill="#333">
          Cell text shows count and row-normalized percentage.
        </text>
      </svg>
    </div>
  );
};

export default ConfusionMatrixChart;
