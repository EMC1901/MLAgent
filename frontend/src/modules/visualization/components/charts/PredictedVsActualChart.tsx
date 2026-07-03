import React, { useMemo } from 'react';
import { PredictedVsActualData } from '../../types';
import { CHART_COLORS, PUBLICATION_CHART_STYLE } from '../../constants';

interface Props {
  data: PredictedVsActualData | null;
  modelId?: string | null;
  modelFamily?: string | null;
  modelTrialId?: string | null;
}

interface PlotPoint {
  actual: number;
  predicted: number;
  residual: number;
  split: string;
}

const WIDTH = 860;
const HEIGHT = 720;
const MARGIN = { top: 72, right: 60, bottom: 82, left: 92 };
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom;
const TRAIN_COLOR = '#315BE8';
const TEST_COLOR = '#E41A1C';
const UNKNOWN_COLOR = '#6f6f6f';

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

function niceDomain(minVal: number, maxVal: number, tickCount = 8): [number, number] {
  if (!Number.isFinite(minVal) || !Number.isFinite(maxVal)) return [0, 1];
  if (minVal === maxVal) return [minVal - 1, maxVal + 1];
  const range = niceNumber(maxVal - minVal, false);
  const interval = niceNumber(range / (tickCount - 1), true);
  return [Math.floor(minVal / interval) * interval, Math.ceil(maxVal / interval) * interval];
}

function generateTicks(minVal: number, maxVal: number, tickCount = 8): number[] {
  const [dMin, dMax] = niceDomain(minVal, maxVal, tickCount);
  const step = (dMax - dMin) / (tickCount - 1);
  return Array.from({ length: tickCount }, (_, i) => Number((dMin + i * step).toFixed(10)));
}

function formatTick(value: number): string {
  if (value === 0) return '0';
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 1) return Number(value.toFixed(2)).toString();
  if (absVal >= 0.001) return Number(value.toFixed(4)).toString();
  return value.toExponential(2);
}

function formatMetric(value: number): string {
  const absVal = Math.abs(value);
  if (absVal >= 100) return value.toFixed(0);
  if (absVal >= 10) return value.toFixed(1);
  if (absVal >= 1) return value.toFixed(3);
  if (absVal >= 0.01) return value.toFixed(3);
  if (absVal >= 0.0001) return value.toFixed(4);
  return value.toExponential(2);
}

function metricKey(metric?: string | null): string {
  const normalised = (metric || '').toLowerCase().replace(/[\s.-]/g, '_');
  if (normalised === 'r2' || normalised === 'r_2' || normalised === 'r_squared' || normalised === 'rsquared') return 'r2';
  if (normalised === 'mean_absolute_error') return 'mae';
  if (normalised === 'root_mean_squared_error') return 'rmse';
  return normalised;
}

function metricLabel(metric?: string | null): string {
  const raw = (metric || 'R2').trim();
  if (metricKey(raw) === 'r2') return 'R\u00b2';
  return raw.toUpperCase();
}
function canonicalSplit(split?: string): 'train' | 'test' | 'unknown' {
  const value = (split || 'test').toLowerCase();
  if (['train', 'training'].includes(value)) return 'train';
  if (['test', 'testing', 'validation', 'valid', 'val', 'holdout'].includes(value)) return 'test';
  return 'unknown';
}

function splitColor(split?: string): string {
  const kind = canonicalSplit(split);
  if (kind === 'train') return TRAIN_COLOR;
  if (kind === 'test') return TEST_COLOR;
  return UNKNOWN_COLOR;
}

function modelTitle(modelFamily?: string | null, modelId?: string | null): string {
  const label = modelFamily || modelId || 'Model';
  return `Prediction vs Actual - ${label}`;
}

function buildMetricLines(data: PredictedVsActualData): string[] {
  const splitMetrics = data.split_metrics || [];
  const primaryMetric = data.primary_metric || 'R2';
  const primaryKey = metricKey(primaryMetric);
  const displayMetric = metricLabel(primaryMetric);
  const findMetric = (kind: 'train' | 'test') => splitMetrics.find(
    m => canonicalSplit(m.split) === kind && metricKey(m.metric_name) === primaryKey
  );
  const trainMetric = findMetric('train');
  const testMetric = findMetric('test');
  const lines: string[] = [];

  if (trainMetric) {
    lines.push(`${displayMetric} Train: ${formatMetric(trainMetric.metric_value)}`);
  }
  if (testMetric) {
    lines.push(`${displayMetric} Test: ${formatMetric(testMetric.metric_value)}`);
  } else if (typeof data.primary_metric_value === 'number') {
    lines.push(`${displayMetric} Test: ${formatMetric(data.primary_metric_value)}`);
  } else if (primaryKey === 'r2' && typeof data.r_squared === 'number') {
    lines.push(`${displayMetric} Test: ${formatMetric(data.r_squared)}`);
  }

  return lines;
}
const PredictedVsActualChart: React.FC<Props> = ({ data, modelId, modelFamily, modelTrialId }) => {
  const chart = useMemo(() => {
    const points: PlotPoint[] = (data?.points || [])
      .filter(p => Number.isFinite(p.actual) && Number.isFinite(p.predicted))
      .map(p => ({ ...p, split: p.split || 'test' }));

    if (!data || points.length === 0) {
      return null;
    }

    const allValues = points.flatMap(p => [p.actual, p.predicted]);
    const [domainMin, domainMax] = niceDomain(Math.min(...allValues), Math.max(...allValues));
    const ticks = generateTicks(domainMin, domainMax);
    const xScale = (value: number) => MARGIN.left + ((value - domainMin) / (domainMax - domainMin)) * PLOT_WIDTH;
    const yScale = (value: number) => MARGIN.top + PLOT_HEIGHT - ((value - domainMin) / (domainMax - domainMin)) * PLOT_HEIGHT;
    const hasTrain = points.some(p => canonicalSplit(p.split) === 'train');
    const hasTest = points.some(p => canonicalSplit(p.split) === 'test');

    return {
      points,
      ticks,
      domainMin,
      domainMax,
      xScale,
      yScale,
      hasTrain,
      hasTest,
      metricLines: buildMetricLines(data),
    };
  }, [data]);

  if (!data || !chart) {
    return <p style={{ color: '#999' }}>No final train/test prediction data available. Re-run Pipeline Execution with external test enabled and saved predictions.</p>;
  }

  const metricBoxHeight = 46 + Math.max(0, chart.metricLines.length - 1) * 22;
  const legendItems = [
    ...(chart.hasTrain ? [{ type: 'point', color: TRAIN_COLOR, label: 'Training Set' }] : []),
    ...(chart.hasTest ? [{ type: 'point', color: TEST_COLOR, label: 'Test Set' }] : []),
    { type: 'line', color: CHART_COLORS.axis, label: 'Perfect Prediction' },
  ];
  const legendWidth = 250;
  const legendHeight = 34 + legendItems.length * 28;
  const legendX = MARGIN.left + PLOT_WIDTH - legendWidth - 12;
  const legendY = MARGIN.top + PLOT_HEIGHT - legendHeight - 12;

  return (
    <svg
      className="publication-svg"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Predicted versus actual regression chart"
      style={{ width: '100%', height: 'auto', background: '#fff', display: 'block' }}
    >
      <rect x={0} y={0} width={WIDTH} height={HEIGHT} fill="#fff" />
      <text
        x={WIDTH / 2}
        y={34}
        textAnchor="middle"
        fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
        fontSize={24}
        fontWeight={600}
        fill={CHART_COLORS.axis}
      >
        {modelTitle(modelFamily, modelId)}
      </text>
      {modelTrialId && (
        <text
          x={WIDTH / 2}
          y={58}
          textAnchor="middle"
          fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
          fontSize={12}
          fill="#666"
        >
          Trial: {modelTrialId}
        </text>
      )}

      <rect
        x={MARGIN.left}
        y={MARGIN.top}
        width={PLOT_WIDTH}
        height={PLOT_HEIGHT}
        fill="#fff"
        stroke="#444"
        strokeWidth={1.8}
      />

      {chart.ticks.map(tick => {
        const x = chart.xScale(tick);
        const y = chart.yScale(tick);
        return (
          <g key={`grid-${tick}`}>
            <line x1={x} y1={MARGIN.top} x2={x} y2={MARGIN.top + PLOT_HEIGHT} stroke={CHART_COLORS.grid} strokeWidth={1} opacity={0.7} />
            <line x1={MARGIN.left} y1={y} x2={MARGIN.left + PLOT_WIDTH} y2={y} stroke={CHART_COLORS.grid} strokeWidth={1} opacity={0.7} />
            <line x1={x} y1={MARGIN.top + PLOT_HEIGHT} x2={x} y2={MARGIN.top + PLOT_HEIGHT + 6} stroke="#333" strokeWidth={1.3} />
            <line x1={MARGIN.left - 6} y1={y} x2={MARGIN.left} y2={y} stroke="#333" strokeWidth={1.3} />
            <text x={x} y={MARGIN.top + PLOT_HEIGHT + 28} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={14} fill="#333">
              {formatTick(tick)}
            </text>
            <text x={MARGIN.left - 14} y={y + 5} textAnchor="end" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={14} fill="#333">
              {formatTick(tick)}
            </text>
          </g>
        );
      })}

      <line
        x1={chart.xScale(chart.domainMin)}
        y1={chart.yScale(chart.domainMin)}
        x2={chart.xScale(chart.domainMax)}
        y2={chart.yScale(chart.domainMax)}
        stroke={CHART_COLORS.axis}
        strokeWidth={3}
        strokeDasharray="11 8"
        strokeLinecap="round"
      />

      {chart.points.map((point, index) => (
        <circle
          key={`${point.actual}-${point.predicted}-${index}`}
          cx={chart.xScale(point.actual)}
          cy={chart.yScale(point.predicted)}
          r={5.2}
          fill={splitColor(point.split)}
          fillOpacity={0.78}
          stroke="#fff"
          strokeWidth={0.7}
        >
          <title>{`Actual: ${formatMetric(point.actual)}, Predicted: ${formatMetric(point.predicted)}, Residual: ${formatMetric(point.residual)}`}</title>
        </circle>
      ))}

      <text
        x={MARGIN.left + PLOT_WIDTH / 2}
        y={HEIGHT - 24}
        textAnchor="middle"
        fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
        fontSize={18}
        fill={CHART_COLORS.axis}
      >
        Actual Values
      </text>
      <text
        transform={`translate(28 ${MARGIN.top + PLOT_HEIGHT / 2}) rotate(-90)`}
        textAnchor="middle"
        fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
        fontSize={18}
        fill={CHART_COLORS.axis}
      >
        Predicted Values
      </text>

      <g transform={`translate(${MARGIN.left + 22} ${MARGIN.top + 22})`}>
        <rect width={196} height={metricBoxHeight} rx={6} fill="#FFF4D9" stroke="#777" strokeWidth={1.6} />
        {chart.metricLines.map((line, index) => (
          <text
            key={line}
            x={14}
            y={index === 0 ? 27 : 49 + (index - 1) * 22}
            fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
            fontSize={17}
            fontWeight={700}
            fill="#333"
          >
            {line}
          </text>
        ))}
      </g>

      <g transform={`translate(${legendX} ${legendY})`}>
        <rect width={legendWidth} height={legendHeight} rx={3} fill="#fff" stroke="#d0d0d0" strokeWidth={1.4} />
        {legendItems.map((item, index) => {
          const y = 28 + index * 28;
          return (
            <g key={item.label}>
              {item.type === 'point' ? (
                <circle cx={28} cy={y - 5} r={5.5} fill={item.color} fillOpacity={0.78} stroke="#fff" strokeWidth={0.7} />
              ) : (
                <line x1={16} y1={y - 5} x2={42} y2={y - 5} stroke={item.color} strokeWidth={3} strokeDasharray="9 6" strokeLinecap="round" />
              )}
              <text x={58} y={y} fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={17} fill="#333">
                {item.label}
              </text>
            </g>
          );
        })}
      </g>
    </svg>
  );
};

export default PredictedVsActualChart;
