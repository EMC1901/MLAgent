import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { CrossValidationBoxPlotData } from '../../types';
import { CHART_COLORS } from '../../constants';

interface Props {
  data: CrossValidationBoxPlotData | null;
}

const CrossValidationBoxPlotChart: React.FC<Props> = ({ data }) => {
  if (!data || !data.folds || data.folds.length === 0) {
    return <p style={{ color: '#999' }}>No cross-validation data available.</p>;
  }

  // group by model_family and fold_index
  const families = Array.from(new Set(data.folds.map(f => f.model_family || 'Unknown')));
  const chartData = data.folds.map(f => ({
    family: f.model_family || 'Unknown',
    fold: f.fold_index,
    value: +f.metric_value.toFixed(4),
  }));

  const allValues = chartData.map(d => d.value);
  const meanVal = allValues.reduce((a, b) => a + b, 0) / allValues.length;

  return (
    <div>
      <p style={{ fontSize: 13, color: '#555', margin: '0 0 8px 0' }}>
        Metric: <strong>{data.metric_name}</strong> | Mean: <strong>{meanVal.toFixed(4)}</strong>
      </p>
      <ResponsiveContainer width="100%" height={350}>
        <ScatterChart margin={{ top: 16, right: 20, left: 16, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} />
          <XAxis
            type="number" dataKey="fold" name="Fold" tick={{ fontSize: 12 }}
            domain={['dataMin - 0.5', 'dataMax + 0.5']}
            label={{ value: 'Fold Index', position: 'insideBottomRight', offset: -8, fontSize: 12 }}
            allowDecimals={false}
          />
          <YAxis
            type="number" dataKey="value" name={data.metric_name} tick={{ fontSize: 12 }}
            label={{ value: data.metric_name, angle: -90, position: 'insideLeft', offset: -4, fontSize: 12 }}
          />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <ReferenceLine y={meanVal} stroke={CHART_COLORS.negative} strokeDasharray="5 5" />
          {families.map((family, fi) => {
            const familyData = chartData.filter(d => d.family === family);
            return (
              <Scatter
                key={family}
                name={family}
                data={familyData}
                fill={CHART_COLORS.series[fi % CHART_COLORS.series.length]}
              >
                {familyData.map((_, i) => <Cell key={i} />)}
              </Scatter>
            );
          })}
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default CrossValidationBoxPlotChart;
