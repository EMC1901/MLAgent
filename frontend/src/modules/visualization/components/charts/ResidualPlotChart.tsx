import React from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Cell } from 'recharts';
import { ResidualPlotData } from '../../types';
import { CHART_COLORS } from '../../constants';

// ---- Number formatting helpers (shared pattern with PredictedVsActualChart) ----
function niceNumber(x: number, round: boolean): number {
  if (x === 0) return 0;
  const exp = Math.floor(Math.log10(Math.abs(x)));
  const frac = Math.abs(x) / Math.pow(10, exp);
  let nice: number;
  if (round) {
    if (frac < 1.5) nice = 1;
    else if (frac < 3) nice = 2;
    else if (frac < 7) nice = 5;
    else nice = 10;
  } else {
    if (frac <= 1) nice = 1;
    else if (frac <= 2) nice = 2;
    else if (frac <= 5) nice = 5;
    else nice = 10;
  }
  return nice * Math.pow(10, exp) * (x >= 0 ? 1 : -1);
}

function niceDomain(minVal: number, maxVal: number, tickCount: number = 6): [number, number] {
  if (minVal === maxVal) return [minVal - 1, maxVal + 1];
  const range = niceNumber(maxVal - minVal, false);
  const interval = niceNumber(range / (tickCount - 1), true);
  const niceMin = Math.floor(minVal / interval) * interval;
  const niceMax = Math.ceil(maxVal / interval) * interval;
  return [niceMin, niceMax];
}

function generateTicks(minVal: number, maxVal: number, tickCount: number = 6): number[] {
  const [dMin, dMax] = niceDomain(minVal, maxVal, tickCount);
  const step = (dMax - dMin) / (tickCount - 1);
  const ticks: number[] = [];
  for (let i = 0; i < tickCount; i++) {
    ticks.push(parseFloat((dMin + i * step).toFixed(8)));
  }
  return ticks;
}

function formatTick(value: number): string {
  if (value === 0) return '0';
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 0.1) {
    const s = value.toFixed(3);
    return parseFloat(s).toString();
  }
  if (absVal >= 0.001) return parseFloat(value.toFixed(5)).toString();
  return parseFloat(value.toFixed(6)).toString();
}

function formatMetric(value: number): string {
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 1) return value.toFixed(2);
  if (absVal >= 0.01) return value.toFixed(4);
  if (absVal >= 0.0001) return value.toFixed(5);
  return value.toExponential(3);
}

interface Props {
  data: ResidualPlotData | null;
}

const ResidualPlotChart: React.FC<Props> = ({ data }) => {
  if (!data || !data.points || data.points.length === 0) {
    return <p style={{ color: '#999' }}>No residual data available.</p>;
  }

  const predicted = data.points.map(p => p.predicted);
  const residuals = data.points.map(p => p.residual);
  const minPred = Math.min(...predicted);
  const maxPred = Math.max(...predicted);
  const maxAbsResidual = Math.max(...residuals.map(Math.abs));

  const xDomain = niceDomain(minPred, maxPred);
  const yDomain = niceDomain(-maxAbsResidual, maxAbsResidual);
  const xTicks = generateTicks(minPred, maxPred);
  const yTicks = generateTicks(-maxAbsResidual, maxAbsResidual);

  return (
    <div>
      <div style={{ display: 'flex', gap: 16, marginBottom: 8, fontSize: 13, color: '#555' }}>
        <span>R&sup2;: <strong>{formatMetric(data.r_squared)}</strong></span>
        <span>RMSE: <strong>{formatMetric(data.rmse)}</strong></span>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <ScatterChart margin={{ top: 16, right: 20, left: 16, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            type="number" dataKey="predicted" name="Predicted" tick={{ fontSize: 12 }}
            tickFormatter={formatTick} ticks={xTicks}
            domain={xDomain}
            label={{ value: 'Predicted', position: 'insideBottomRight', offset: -8, fontSize: 12 }}
          />
          <YAxis
            type="number" dataKey="residual" name="Residual" tick={{ fontSize: 12 }}
            tickFormatter={formatTick} ticks={yTicks}
            domain={yDomain}
            label={{ value: 'Residual', angle: -90, position: 'insideLeft', offset: -4, fontSize: 12 }}
          />
          <Tooltip cursor={{ strokeDasharray: '3 3' }} />
          <ReferenceLine y={0} stroke={CHART_COLORS.negative} strokeDasharray="5 5" />
          <Scatter name="Residuals" data={data.points} fill={CHART_COLORS.secondary} opacity={0.5}>
            {data.points.map((_, i) => (
              <Cell key={i} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
};

export default ResidualPlotChart;
