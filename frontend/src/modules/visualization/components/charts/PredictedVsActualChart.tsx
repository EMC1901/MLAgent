import React, { useMemo } from 'react';
import {
  Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, Cell, ComposedChart,
  Label,
} from 'recharts';
import { PredictedVsActualData } from '../../types';

// ---- Number formatting helpers ----
/** Snap a value to a nice round number for axis domain edges. */
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

/** Compute a nice domain [min, max] with a suggested tick count. */
function niceDomain(minVal: number, maxVal: number, tickCount: number = 6): [number, number] {
  if (minVal === maxVal) return [minVal - 1, maxVal + 1];
  const range = niceNumber(maxVal - minVal, false);
  const interval = niceNumber(range / (tickCount - 1), true);
  const niceMin = Math.floor(minVal / interval) * interval;
  const niceMax = Math.ceil(maxVal / interval) * interval;
  return [niceMin, niceMax];
}

/** Generate explicit tick values at nice round positions. */
function generateTicks(minVal: number, maxVal: number, tickCount: number = 6): number[] {
  const [dMin, dMax] = niceDomain(minVal, maxVal, tickCount);
  const step = (dMax - dMin) / (tickCount - 1);
  const ticks: number[] = [];
  for (let i = 0; i < tickCount; i++) {
    ticks.push(parseFloat((dMin + i * step).toFixed(8)));
  }
  return ticks;
}

/** Format a tick value: strip trailing zeros and floating-point noise. */
function formatTick(value: number): string {
  if (value === 0) return '0';
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 0.1) {
    // 1-3 meaningful decimal places, stripping trailing zeros
    const s = value.toFixed(3);
    return parseFloat(s).toString();
  }
  if (absVal >= 0.001) return parseFloat(value.toFixed(5)).toString();
  return parseFloat(value.toFixed(6)).toString();
}

/** Format metric value with appropriate precision. */
function formatMetric(value: number): string {
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 1) return value.toFixed(2);
  if (absVal >= 0.01) return value.toFixed(4);
  if (absVal >= 0.0001) return value.toFixed(5);
  return value.toExponential(3);
}

interface Props {
  data: PredictedVsActualData | null;
  modelId?: string | null;
  modelFamily?: string | null;
  modelTrialId?: string | null;
}

// Color gradient stops: green (small error) → yellow → orange → red (large error)
const ERROR_COLORS = [
  { threshold: 0.0, color: '#2e7d32' },   // dark green
  { threshold: 0.25, color: '#66bb6a' },   // light green
  { threshold: 0.5, color: '#fdd835' },    // yellow
  { threshold: 0.75, color: '#ff9800' },   // orange
  { threshold: 1.0, color: '#c62828' },    // dark red
];

function residualColor(absError: number, maxError: number): string {
  if (maxError === 0) return ERROR_COLORS[0].color;
  const ratio = Math.min(absError / maxError, 1.0);
  for (let i = ERROR_COLORS.length - 1; i >= 0; i--) {
    if (ratio >= ERROR_COLORS[i].threshold) return ERROR_COLORS[i].color;
  }
  return ERROR_COLORS[0].color;
}

// ---- Chart ----
const PredictedVsActualChart: React.FC<Props> = ({ data, modelId, modelFamily, modelTrialId }) => {
  const {
    enrichedPoints, maxAbsError,
    metrics, domain, ticks, modelLabel,
  } = useMemo(() => {
    if (!data || !data.points || data.points.length === 0) {
      return {
        enrichedPoints: [] as any[],
        maxAbsError: 0,
        metrics: null,
        domain: [0, 1] as [number, number],
        ticks: [0, 1],
        modelLabel: null as string | null,
      };
    }

    const allActual = data.points.map(p => p.actual);
    const minVal = Math.min(...allActual);
    const maxVal = Math.max(...allActual);

    const absErrors = data.points.map(p => Math.abs(p.residual));
    const maxAbs = Math.max(...absErrors, 1e-10);

    // Scatter in ComposedChart reads x/y from data items.
    // Map actual→x, predicted→y for correct positioning.
    const enriched = data.points.map((p, i) => ({
      x: p.actual,
      y: p.predicted,
      ...p,
      absError: absErrors[i],
    }));

    // Model label
    const parts: string[] = [];
    if (modelFamily) parts.push(modelFamily);
    if (modelId) parts.push(modelId);
    if (modelTrialId) parts.push(`trial: ${modelTrialId}`);
    const label = parts.length > 0 ? parts.join('  ·  ') : null;

    return {
      enrichedPoints: enriched,
      maxAbsError: maxAbs,
      metrics: {
        rSquared: data.r_squared,
        rmse: data.rmse,
        mae: data.mae,
        resMean: data.residual_mean,
        resStd: data.residual_std,
      },
      domain: niceDomain(minVal, maxVal) as [number, number],
      ticks: generateTicks(minVal, maxVal),
      modelLabel: label,
    };
  }, [data, modelId, modelFamily, modelTrialId]);

  if (!data || !data.points || data.points.length === 0) {
    return <p style={{ color: '#999' }}>No prediction vs actual data available.</p>;
  }

  const [dMin, dMax] = domain;

  return (
    <div>
      {/* Model label */}
      {modelLabel && (
        <div style={{
          fontSize: 12, color: '#555', marginBottom: 6,
          padding: '4px 10px', backgroundColor: '#f5f5f5',
          borderRadius: 4, display: 'inline-block',
        }}>
          <strong>Model:</strong> {modelLabel}
        </div>
      )}

      {/* Metrics */}
      {metrics && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14, marginBottom: 12, fontSize: 13 }}>
          <span style={{ color: '#2e7d32', fontWeight: 600 }}>
            R&sup2;: {formatMetric(metrics.rSquared)}
          </span>
          <span style={{ color: '#e65100', fontWeight: 600 }}>
            RMSE: {formatMetric(metrics.rmse)}
          </span>
          <span style={{ color: '#6a1b9a', fontWeight: 600 }}>
            MAE: {formatMetric(metrics.mae)}
          </span>
          <span style={{ color: '#555' }}>
            Residual Mean: <strong>{formatMetric(metrics.resMean)}</strong>
          </span>
          <span style={{ color: '#555' }}>
            1&sigma;: <strong>±{formatMetric(metrics.resStd)}</strong>
          </span>
        </div>
      )}

      {/* Legend above chart */}
      <div style={{
        display: 'flex', justifyContent: 'flex-end', marginBottom: -8,
        fontSize: 11, color: '#666',
      }}>
        <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <span style={{
            display: 'inline-block', width: 20, height: 2,
            backgroundColor: '#555', verticalAlign: 'middle',
          }} />
          Identity (y=x)
        </span>
      </div>

      {/* Scatter chart */}
      <ResponsiveContainer width="100%" height={420}>
        <ComposedChart margin={{ top: 8, right: 12, left: 0, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis
            type="number"
            dataKey="actual"
            name="Actual"
            tick={{ fontSize: 11 }}
            tickFormatter={formatTick}
            ticks={ticks}
            domain={domain}
          >
            <Label value="Actual" offset={-4} position="insideBottomRight" fontSize={12} />
          </XAxis>
          <YAxis
            type="number"
            dataKey="predicted"
            name="Predicted"
            tick={{ fontSize: 11 }}
            tickFormatter={formatTick}
            ticks={ticks}
            domain={domain}
          >
            <Label value="Predicted" angle={-90} offset={6} position="insideLeft" fontSize={12} />
          </YAxis>
          <Tooltip content={<CustomTooltip />} />

          {/* Identity line */}
          <ReferenceLine
            segment={[{ x: dMin, y: dMin }, { x: dMax, y: dMax }]}
            stroke="#555"
            strokeWidth={1.5}
          />

          {/* Scatter with error-coloring */}
          <Scatter name="Samples" data={enrichedPoints} opacity={0.6}>
            {enrichedPoints.map((p: any, i: number) => (
              <Cell key={i} fill={residualColor(p.absError, maxAbsError)} />
            ))}
          </Scatter>
        </ComposedChart>
      </ResponsiveContainer>

      {/* Color legend for residual magnitude */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 6,
        justifyContent: 'center', marginTop: 6, fontSize: 11, color: '#666',
      }}>
        <span>|Residual|</span>
        <svg width={180} height={14}>
          <defs>
            <linearGradient id="errorGrad" x1="0" y1="0" x2="1" y2="0">
              {ERROR_COLORS.map((s, i) => (
                <stop key={i} offset={s.threshold} stopColor={s.color} />
              ))}
            </linearGradient>
          </defs>
          <rect x={0} y={2} width={180} height={10} rx={2} fill="url(#errorGrad)" />
        </svg>
      </div>
    </div>
  );
};

// ---- Custom Tooltip ----
interface TooltipPayloadItem {
  name: string;
  value: number;
  dataKey: string;
  payload?: {
    actual: number;
    predicted: number;
    residual: number;
    absError: number;
  };
}

const CustomTooltip: React.FC<{ active?: boolean; payload?: TooltipPayloadItem[] }> = ({ active, payload }) => {
  if (!active || !payload || payload.length === 0) return null;

  // Find the scatter payload with actual/predicted/residual data
  const sample = payload.find(p => p.payload?.actual !== undefined)?.payload;
  if (!sample) return null;

  const errPct = sample.actual !== 0
    ? (Math.abs(sample.residual) / Math.abs(sample.actual) * 100).toFixed(1)
    : 'N/A';

  return (
    <div style={{
      backgroundColor: '#fff', border: '1px solid #ccc',
      borderRadius: 4, padding: '8px 12px', fontSize: 12,
      boxShadow: '0 2px 8px rgba(0,0,0,0.12)',
    }}>
      <div style={{ fontWeight: 600, marginBottom: 4 }}>Sample</div>
      <div>Actual: <strong>{sample.actual.toFixed(4)}</strong></div>
      <div>Predicted: <strong>{sample.predicted.toFixed(4)}</strong></div>
      <div>Residual: <strong style={{ color: sample.residual > 0 ? '#c62828' : '#2e7d32' }}>
        {sample.residual > 0 ? '+' : ''}{sample.residual.toFixed(4)}
      </strong></div>
      <div>|Error|: <strong>{errPct}%</strong></div>
    </div>
  );
};

export default PredictedVsActualChart;
