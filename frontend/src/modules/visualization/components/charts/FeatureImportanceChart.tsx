import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { FeatureImportanceItem } from '../../types';
import { FEATURE_GROUP_COLORS, CHART_COLORS } from '../../constants';

interface Props {
  data: FeatureImportanceItem[];
}

const FeatureImportanceChart: React.FC<Props> = ({ data }) => {
  if (!data || data.length === 0) {
    return <p style={{ color: '#999' }}>No feature importance data available.</p>;
  }

  const top = data.slice(0, 30);
  const chartData = top.map(d => ({
    name: d.feature_name.length > 30 ? d.feature_name.slice(0, 30) + '...' : d.feature_name,
    fullName: d.feature_name,
    value: +d.importance_value.toFixed(6),
    group: d.feature_group,
    method: d.importance_method,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(300, chartData.length * 30)}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 20, left: 140, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
        <XAxis type="number" tick={{ fontSize: 12 }} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={130} />
        <Tooltip
          formatter={(value: any) => (typeof value === 'number' ? value.toFixed(6) : value)}
          labelFormatter={(label: any, payload: any) => payload?.[0]?.payload?.fullName || label}
        />
        <Bar dataKey="value" name="Importance">
          {chartData.map((entry, i) => (
            <Cell key={i} fill={FEATURE_GROUP_COLORS[entry.group] || CHART_COLORS.neutral} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default FeatureImportanceChart;
