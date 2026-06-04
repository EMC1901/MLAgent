import React from 'react';
import { BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrainTestComparisonData } from '../../types';
import { CHART_COLORS } from '../../constants';

interface Props {
  data: TrainTestComparisonData | null;
}

const TrainTestComparisonChart: React.FC<Props> = ({ data }) => {
  if (!data || !data.comparisons || data.comparisons.length === 0) {
    return <p style={{ color: '#999' }}>No train/test comparison data available.</p>;
  }

  const chartData = data.comparisons.map(c => ({
    name: `Fold ${c.fold_index}`,
    testValue: +c.test_value.toFixed(4),
    n_samples: c.n_samples,
  }));

  return (
    <ResponsiveContainer width="100%" height={Math.max(250, chartData.length * 50)}>
      <BarChart data={chartData} margin={{ top: 8, right: 20, left: 16, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
        <XAxis dataKey="name" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip formatter={(value: any) => (typeof value === 'number' ? value.toFixed(4) : value)} />
        <Bar dataKey="testValue" name="Test Metric" fill={CHART_COLORS.primary}>
          {chartData.map((entry, i) => (
            <Cell key={i} fill={CHART_COLORS.series[i % CHART_COLORS.series.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
};

export default TrainTestComparisonChart;
