import React from 'react';
import { CorrelationMatrixData } from '../../types';
import { HEATMAP_COLORS, PUBLICATION_CHART_STYLE } from '../../constants';

interface Props {
  data: CorrelationMatrixData | null;
}

const truncate = (value: string, max = 18): string =>
  value.length > max ? `${value.slice(0, max - 3)}...` : value;

const FeatureCorrelationHeatmap: React.FC<Props> = ({ data }) => {
  if (!data || !data.feature_names.length || !data.matrix.length) {
    return <p style={{ color: '#999' }}>No correlation matrix data available.</p>;
  }

  const { feature_names, matrix } = data;
  const n = feature_names.length;
  const cellSize = Math.max(16, Math.min(34, 720 / n));
  const left = 152;
  const top = 120;
  const right = 36;
  const bottom = 54;
  const legendHeight = 28;
  const width = left + n * cellSize + right;
  const height = top + n * cellSize + bottom + legendHeight;

  const colorFor = (v: number): string => {
    const t = (v + 1) / 2;
    const idx = Math.round(t * (HEATMAP_COLORS.length - 1));
    return HEATMAP_COLORS[Math.max(0, Math.min(HEATMAP_COLORS.length - 1, idx))];
  };

  const legendX = left;
  const legendY = top + n * cellSize + 26;
  const legendWidth = Math.min(260, n * cellSize);
  const legendStep = legendWidth / HEATMAP_COLORS.length;

  return (
    <div style={{ overflowX: 'auto', background: '#fff' }}>
      <svg
        className="publication-svg"
        width="100%"
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Feature correlation heatmap with ${n} features`}
        style={{ fontFamily: PUBLICATION_CHART_STYLE.fontFamily, background: '#fff' }}
      >
        <rect x={0} y={0} width={width} height={height} fill="#fff" />
        <text x={left + (n * cellSize) / 2} y={24} textAnchor="middle" fontSize={14} fontWeight={700} fill="#111">
          Feature correlation matrix
        </text>
        {feature_names.map((name, i) => {
          const x = left + i * cellSize + cellSize / 2;
          return (
            <text
              key={`x-${name}-${i}`}
              x={x}
              y={top - 10}
              transform={`rotate(-45 ${x} ${top - 10})`}
              textAnchor="start"
              fontSize={10}
              fill="#222"
            >
              <title>{name}</title>
              {truncate(name, 22)}
            </text>
          );
        })}
        {feature_names.map((name, i) => (
          <text
            key={`y-${name}-${i}`}
            x={left - 8}
            y={top + i * cellSize + cellSize * 0.66}
            textAnchor="end"
            fontSize={10}
            fill="#222"
          >
            <title>{name}</title>
            {truncate(name, 23)}
          </text>
        ))}
        {matrix.map((row, ri) =>
          row.map((val, ci) => {
            const x = left + ci * cellSize;
            const y = top + ri * cellSize;
            return (
              <g key={`${ri}-${ci}`}>
                <rect
                  x={x}
                  y={y}
                  width={cellSize}
                  height={cellSize}
                  fill={colorFor(val)}
                  stroke="#fff"
                  strokeWidth={0.75}
                >
                  <title>{`${feature_names[ri]} x ${feature_names[ci]}: ${val.toFixed(3)}`}</title>
                </rect>
                {cellSize >= 24 && (
                  <text
                    x={x + cellSize / 2}
                    y={y + cellSize * 0.64}
                    textAnchor="middle"
                    fontSize={8.5}
                    fontWeight={Math.abs(val) > 0.5 ? 700 : 400}
                    fill={Math.abs(val) > 0.72 ? '#fff' : '#222'}
                  >
                    {val.toFixed(1)}
                  </text>
                )}
              </g>
            );
          })
        )}
        <text x={legendX} y={legendY - 7} fontSize={10} fill="#222">Correlation coefficient</text>
        {HEATMAP_COLORS.map((color, i) => (
          <rect key={color} x={legendX + i * legendStep} y={legendY} width={legendStep + 0.5} height={10} fill={color} />
        ))}
        <text x={legendX} y={legendY + 24} fontSize={10} textAnchor="middle" fill="#222">-1</text>
        <text x={legendX + legendWidth / 2} y={legendY + 24} fontSize={10} textAnchor="middle" fill="#222">0</text>
        <text x={legendX + legendWidth} y={legendY + 24} fontSize={10} textAnchor="middle" fill="#222">+1</text>
      </svg>
    </div>
  );
};

export default FeatureCorrelationHeatmap;
