import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { DescriptorDistributionItem } from '../../types';
import { CHART_COLORS } from '../../constants';

interface Props {
  data: DescriptorDistributionItem[];
}

type ScaleMode = 'raw' | 'normalized';

const DescriptorDistributionChart: React.FC<Props> = ({ data }) => {
  const [scaleMode, setScaleMode] = React.useState<ScaleMode>('normalized');

  if (!data || data.length === 0) {
    return <p style={{ color: '#999' }}>No descriptor distribution data available.</p>;
  }

  const top = data.slice(0, 30);

  // normalize each stat independently across features for comparability
  const maxVariance = Math.max(...top.map(d => d.variance), 1e-9);
  const maxAbsSkew = Math.max(...top.map(d => Math.abs(d.skewness)), 1e-9);
  const maxRange = Math.max(...top.map(d => d.max_val - d.min_val), 1e-9);
  const maxStd = Math.max(...top.map(d => d.std), 1e-9);

  const chartData = top.map(d => ({
    name: d.feature_name.length > 20 ? d.feature_name.slice(0, 20) + '...' : d.feature_name,
    fullName: d.feature_name,
    variance: scaleMode === 'normalized' ? d.variance / maxVariance : d.variance,
    absSkewness: scaleMode === 'normalized' ? Math.abs(d.skewness) / maxAbsSkew : Math.abs(d.skewness),
    range: scaleMode === 'normalized' ? (d.max_val - d.min_val) / maxRange : (d.max_val - d.min_val),
    std: scaleMode === 'normalized' ? d.std / maxStd : d.std,
  }));

  return (
    <div>
      <div style={{ marginBottom: 8, display: 'flex', gap: 8, alignItems: 'center' }}>
        <button
          onClick={() => setScaleMode('normalized')}
          style={{
            padding: '4px 12px', border: 'none', borderRadius: '12px', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
            backgroundColor: scaleMode === 'normalized' ? CHART_COLORS.primary : '#e8e8e8',
            color: scaleMode === 'normalized' ? '#fff' : '#333',
          }}
        >
          Normalized
        </button>
        <button
          onClick={() => setScaleMode('raw')}
          style={{
            padding: '4px 12px', border: 'none', borderRadius: '12px', fontSize: '12px', fontWeight: 600, cursor: 'pointer',
            backgroundColor: scaleMode === 'raw' ? CHART_COLORS.primary : '#e8e8e8',
            color: scaleMode === 'raw' ? '#fff' : '#333',
          }}
        >
          Raw
        </button>
      </div>
      <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 28)}>
        <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 20, left: 120, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis type="number" tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
          <Tooltip labelFormatter={(label: any, payload: any) => payload?.[0]?.payload?.fullName || label} />
          <Legend />
          <Bar dataKey="variance" name={scaleMode === 'normalized' ? 'Var (norm)' : 'Variance'} fill={CHART_COLORS.primary} />
          <Bar dataKey="absSkewness" name={scaleMode === 'normalized' ? '|Skew| (norm)' : '|Skewness|'} fill={CHART_COLORS.secondary} />
          <Bar dataKey="std" name={scaleMode === 'normalized' ? 'Std (norm)' : 'Std Dev'} fill={CHART_COLORS.positive} />
          <Bar dataKey="range" name={scaleMode === 'normalized' ? 'Range (norm)' : 'Range'} fill={CHART_COLORS.warning} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DescriptorDistributionChart;
