import React from 'react';
import { CorrelationMatrixData } from '../../types';
import { HEATMAP_COLORS } from '../../constants';

interface Props {
  data: CorrelationMatrixData | null;
}

const FeatureCorrelationHeatmap: React.FC<Props> = ({ data }) => {
  if (!data || !data.feature_names.length || !data.matrix.length) {
    return <p style={{ color: '#999' }}>No correlation matrix data available.</p>;
  }

  const { feature_names, matrix } = data;
  const n = feature_names.length;
  const cellSize = Math.max(14, Math.min(40, 600 / n));

  const colorFor = (v: number): string => {
    // map [-1, 1] -> [0, 8]
    const t = (v + 1) / 2;
    const idx = Math.round(t * (HEATMAP_COLORS.length - 1));
    return HEATMAP_COLORS[Math.max(0, Math.min(HEATMAP_COLORS.length - 1, idx))];
  };

  const labelStyle: React.CSSProperties = {
    fontSize: Math.max(8, cellSize * 0.35),
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    maxWidth: 120,
  };

  return (
    <div style={{ overflowX: 'auto', fontSize: '12px' }}>
      <div style={{ display: 'flex' }}>
        {/* Y-axis labels */}
        <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-around', paddingRight: 4, minWidth: 100 }}>
          <div style={{ height: cellSize }} />
          {feature_names.map((name, i) => (
            <div key={i} style={{ height: cellSize, display: 'flex', alignItems: 'center' }} title={name}>
              <span style={labelStyle}>{name}</span>
            </div>
          ))}
        </div>
        {/* Heatmap grid */}
        <div>
          {/* X-axis labels */}
          <div style={{ display: 'flex', paddingLeft: 0 }}>
            {feature_names.map((name, i) => (
              <div
                key={i}
                style={{
                  width: cellSize,
                  height: cellSize,
                  display: 'flex',
                  alignItems: 'flex-end',
                  justifyContent: 'center',
                  transform: 'rotate(-45deg)',
                  transformOrigin: 'bottom left',
                  marginLeft: i === 0 ? 0 : 0,
                }}
                title={name}
              >
                <span style={{ ...labelStyle, marginBottom: 2 }}>{name}</span>
              </div>
            ))}
          </div>
          {/* Cells */}
          {matrix.map((row, ri) => (
            <div key={ri} style={{ display: 'flex' }}>
              {row.map((val, ci) => (
                <div
                  key={ci}
                  title={`${feature_names[ri]} × ${feature_names[ci]}: ${val.toFixed(3)}`}
                  style={{
                    width: cellSize,
                    height: cellSize,
                    backgroundColor: colorFor(val),
                    border: '1px solid #fff',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: Math.max(7, cellSize * 0.25),
                    color: Math.abs(val) > 0.7 ? '#fff' : '#333',
                    fontWeight: Math.abs(val) > 0.5 ? 600 : 400,
                  }}
                >
                  {cellSize > 20 ? val.toFixed(1) : ''}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 12, fontSize: 11, color: '#666' }}>
        <span>-1</span>
        <div style={{ display: 'flex', height: 12, width: 200 }}>
          {HEATMAP_COLORS.map((c, i) => (
            <div key={i} style={{ flex: 1, backgroundColor: c }} />
          ))}
        </div>
        <span>+1</span>
      </div>
    </div>
  );
};

export default FeatureCorrelationHeatmap;
