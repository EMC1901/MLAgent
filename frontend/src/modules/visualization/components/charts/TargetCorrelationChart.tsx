import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { TargetCorrelationItem } from '../../types';
import { CHART_COLORS } from '../../constants';

interface Props {
  data: TargetCorrelationItem[];
}

const TargetCorrelationChart: React.FC<Props> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p style={{ color: '#999' }}>No target correlation data available.</p>;
  }

  const chartData = data
    .map(d => ({
      name: d.feature_name.length > 25 ? d.feature_name.slice(0, 25) + '...' : d.feature_name,
      fullName: d.feature_name,
      pearson: +d.pearson_r.toFixed(4),
      spearman: +d.spearman_rho.toFixed(4),
    }))
    .sort((a, b) => Math.abs(b.pearson) - Math.abs(a.pearson));

  return (
    <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 28)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 20, left: 120, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
        <XAxis type="number" domain={[-1, 1]} tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={110} />
        <Tooltip
          formatter={(value: any) => (typeof value === 'number' ? value.toFixed(4) : value)}
          labelFormatter={(label: any, payload: any) => payload?.[0]?.payload?.fullName || label}
        />
        <Legend />
        <Bar dataKey="pearson" name="Pearson r" fill={CHART_COLORS.primary} />
        <Bar dataKey="spearman" name="Spearman ρ" fill={CHART_COLORS.secondary} />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default TargetCorrelationChart;
