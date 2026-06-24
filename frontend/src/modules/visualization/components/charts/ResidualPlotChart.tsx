import React, { useMemo } from 'react';
import { ResidualPlotData } from '../../types';
import { CHART_COLORS, PUBLICATION_CHART_STYLE } from '../../constants';

interface Props {
  data: ResidualPlotData | null;
  variant?: 'scatter' | 'distribution';
}

interface ResidualPoint {
  predicted: number;
  residual: number;
  split: string;
}

interface HistogramBin {
  x0: number;
  x1: number;
  trainDensity: number;
  testDensity: number;
}

const WIDTH = 760;
const HEIGHT = 640;
const MARGIN = { top: 54, right: 42, bottom: 74, left: 78 };
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

function niceDomain(minVal: number, maxVal: number, tickCount = 7): [number, number] {
  if (!Number.isFinite(minVal) || !Number.isFinite(maxVal)) return [0, 1];
  if (minVal === maxVal) return [minVal - 1, maxVal + 1];
  const range = niceNumber(maxVal - minVal, false);
  const interval = niceNumber(range / (tickCount - 1), true);
  return [Math.floor(minVal / interval) * interval, Math.ceil(maxVal / interval) * interval];
}

function generateTicks(minVal: number, maxVal: number, tickCount = 7): number[] {
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

function formatDensity(value: number): string {
  if (value >= 0.01) return value.toFixed(3);
  return value.toFixed(4);
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

function cleanPoints(data: ResidualPlotData | null): ResidualPoint[] {
  return (data?.points || [])
    .filter(p => Number.isFinite(p.predicted) && Number.isFinite(p.residual))
    .map(p => ({ predicted: p.predicted, residual: p.residual, split: p.split || 'test' }));
}

function buildHistogram(points: ResidualPoint[], binCount = 24): HistogramBin[] {
  if (points.length === 0) return [];
  const residuals = points.map(p => p.residual);
  const [minResidual, maxResidual] = niceDomain(Math.min(...residuals), Math.max(...residuals), 8);
  const width = (maxResidual - minResidual) / binCount || 1;
  const trainPoints = points.filter(p => canonicalSplit(p.split) === 'train');
  const testPoints = points.filter(p => canonicalSplit(p.split) === 'test');
  const bins: HistogramBin[] = [];

  for (let i = 0; i < binCount; i++) {
    const x0 = minResidual + i * width;
    const x1 = i === binCount - 1 ? maxResidual : x0 + width;
    const inBin = (p: ResidualPoint) => p.residual >= x0 && (i === binCount - 1 ? p.residual <= x1 : p.residual < x1);
    const trainCount = trainPoints.filter(inBin).length;
    const testCount = testPoints.filter(inBin).length;
    bins.push({
      x0,
      x1,
      trainDensity: trainPoints.length > 0 ? trainCount / (trainPoints.length * width) : 0,
      testDensity: testPoints.length > 0 ? testCount / (testPoints.length * width) : 0,
    });
  }
  return bins;
}

function Legend({ hasTrain, hasTest, x, y, line = false }: { hasTrain: boolean; hasTest: boolean; x: number; y: number; line?: boolean }) {
  const items = [
    ...(hasTrain ? [{ color: TRAIN_COLOR, label: 'Training Set' }] : []),
    ...(hasTest ? [{ color: TEST_COLOR, label: 'External Test Set' }] : []),
  ];
  const width = 176;
  const height = 22 + items.length * 26;
  return (
    <g transform={`translate(${x} ${y})`}>
      <rect width={width} height={height} rx={3} fill="#fff" stroke="#d0d0d0" strokeWidth={1.2} />
      {items.map((item, index) => (
        <g key={item.label}>
          {line ? (
            <rect x={17} y={19 + index * 26} width={28} height={11} fill={item.color} fillOpacity={0.72} />
          ) : (
            <circle cx={31} cy={24 + index * 26} r={5.2} fill="none" stroke={item.color} strokeWidth={1.8} />
          )}
          <text x={58} y={29 + index * 26} fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={15} fill="#333">
            {item.label}
          </text>
        </g>
      ))}
    </g>
  );
}

function Axes({
  xTicks,
  yTicks,
  xScale,
  yScale,
  yFormatter = formatTick,
}: {
  xTicks: number[];
  yTicks: number[];
  xScale: (value: number) => number;
  yScale: (value: number) => number;
  yFormatter?: (value: number) => string;
}) {
  return (
    <>
      <rect x={MARGIN.left} y={MARGIN.top} width={PLOT_WIDTH} height={PLOT_HEIGHT} fill="#fff" stroke="#555" strokeWidth={1.5} />
      {xTicks.map(tick => {
        const x = xScale(tick);
        return (
          <g key={`x-${tick}`}>
            <line x1={x} y1={MARGIN.top} x2={x} y2={MARGIN.top + PLOT_HEIGHT} stroke={CHART_COLORS.grid} strokeWidth={1} opacity={0.68} />
            <line x1={x} y1={MARGIN.top + PLOT_HEIGHT} x2={x} y2={MARGIN.top + PLOT_HEIGHT + 6} stroke="#333" strokeWidth={1.2} />
            <text x={x} y={MARGIN.top + PLOT_HEIGHT + 28} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={14} fill="#333">
              {formatTick(tick)}
            </text>
          </g>
        );
      })}
      {yTicks.map(tick => {
        const y = yScale(tick);
        return (
          <g key={`y-${tick}`}>
            <line x1={MARGIN.left} y1={y} x2={MARGIN.left + PLOT_WIDTH} y2={y} stroke={CHART_COLORS.grid} strokeWidth={1} opacity={0.68} />
            <line x1={MARGIN.left - 6} y1={y} x2={MARGIN.left} y2={y} stroke="#333" strokeWidth={1.2} />
            <text x={MARGIN.left - 14} y={y + 5} textAnchor="end" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={14} fill="#333">
              {yFormatter(tick)}
            </text>
          </g>
        );
      })}
    </>
  );
}

function ResidualScatterSvg({ points }: { points: ResidualPoint[] }) {
  const predicted = points.map(p => p.predicted);
  const residuals = points.map(p => p.residual);
  const [xMin, xMax] = niceDomain(Math.min(...predicted), Math.max(...predicted), 8);
  const maxAbsResidual = Math.max(...residuals.map(Math.abs), 1);
  const [yMin, yMax] = niceDomain(-maxAbsResidual, maxAbsResidual, 8);
  const xTicks = generateTicks(xMin, xMax, 8);
  const yTicks = generateTicks(yMin, yMax, 8);
  const xScale = (value: number) => MARGIN.left + ((value - xMin) / (xMax - xMin)) * PLOT_WIDTH;
  const yScale = (value: number) => MARGIN.top + PLOT_HEIGHT - ((value - yMin) / (yMax - yMin)) * PLOT_HEIGHT;
  const hasTrain = points.some(p => canonicalSplit(p.split) === 'train');
  const hasTest = points.some(p => canonicalSplit(p.split) === 'test');

  return (
    <svg className="publication-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Residuals plot" style={{ width: '100%', height: 'auto', background: '#fff', display: 'block' }}>
      <rect x={0} y={0} width={WIDTH} height={HEIGHT} fill="#fff" />
      <text x={WIDTH / 2} y={30} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={21} fontWeight={600} fill={CHART_COLORS.axis}>
        Residuals Plot
      </text>
      <Axes xTicks={xTicks} yTicks={yTicks} xScale={xScale} yScale={yScale} />
      <line x1={MARGIN.left} y1={yScale(0)} x2={MARGIN.left + PLOT_WIDTH} y2={yScale(0)} stroke={CHART_COLORS.axis} strokeWidth={2.2} strokeDasharray="9 7" />
      {points.map((point, index) => (
        <circle key={`${point.predicted}-${point.residual}-${index}`} cx={xScale(point.predicted)} cy={yScale(point.residual)} r={5.1} fill="none" stroke={splitColor(point.split)} strokeWidth={1.8}>
          <title>{`Predicted: ${formatTick(point.predicted)}, Residual: ${formatTick(point.residual)}`}</title>
        </circle>
      ))}
      <Legend hasTrain={hasTrain} hasTest={hasTest} x={MARGIN.left + PLOT_WIDTH - 188} y={MARGIN.top + 10} />
      <text x={MARGIN.left + PLOT_WIDTH / 2} y={HEIGHT - 24} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={17} fill={CHART_COLORS.axis}>
        Predicted Values
      </text>

    </svg>
  );
}

function ResidualDistributionSvg({ points }: { points: ResidualPoint[] }) {
  const bins = buildHistogram(points);
  const residualMin = bins[0]?.x0 ?? -1;
  const residualMax = bins[bins.length - 1]?.x1 ?? 1;
  const maxDensity = Math.max(...bins.flatMap(b => [b.trainDensity, b.testDensity]), 0.001);
  const [yMin, yMax] = niceDomain(0, maxDensity, 7);
  const xTicks = generateTicks(residualMin, residualMax, 7);
  const yTicks = generateTicks(yMin, yMax, 7);
  const xScale = (value: number) => MARGIN.left + ((value - residualMin) / (residualMax - residualMin)) * PLOT_WIDTH;
  const yScale = (value: number) => MARGIN.top + PLOT_HEIGHT - ((value - yMin) / (yMax - yMin)) * PLOT_HEIGHT;
  const hasTrain = points.some(p => canonicalSplit(p.split) === 'train');
  const hasTest = points.some(p => canonicalSplit(p.split) === 'test');

  return (
    <svg className="publication-svg" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Residuals distribution" style={{ width: '100%', height: 'auto', background: '#fff', display: 'block' }}>
      <rect x={0} y={0} width={WIDTH} height={HEIGHT} fill="#fff" />
      <text x={WIDTH / 2} y={30} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={21} fontWeight={600} fill={CHART_COLORS.axis}>
        Residuals Distribution
      </text>
      <Axes xTicks={xTicks} yTicks={yTicks} xScale={xScale} yScale={yScale} yFormatter={formatDensity} />
      {bins.map((bin, index) => {
        const x = xScale(bin.x0) + 1;
        const width = Math.max(1, xScale(bin.x1) - xScale(bin.x0) - 2);
        const trainHeight = yScale(0) - yScale(bin.trainDensity);
        const testHeight = yScale(0) - yScale(bin.testDensity);
        return (
          <g key={`${bin.x0}-${index}`}>
            {hasTrain && trainHeight > 0 && (
              <rect x={x} y={yScale(bin.trainDensity)} width={width} height={trainHeight} fill={TRAIN_COLOR} fillOpacity={0.72} />
            )}
            {hasTest && testHeight > 0 && (
              <rect x={x} y={yScale(bin.testDensity)} width={width} height={testHeight} fill={TEST_COLOR} fillOpacity={0.72} />
            )}
          </g>
        );
      })}
      <Legend hasTrain={hasTrain} hasTest={hasTest} x={MARGIN.left + PLOT_WIDTH - 188} y={MARGIN.top + 10} line />
      <text x={MARGIN.left + PLOT_WIDTH / 2} y={HEIGHT - 24} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={17} fill={CHART_COLORS.axis}>
        Residuals
      </text>
      <text transform={`translate(26 ${MARGIN.top + PLOT_HEIGHT / 2}) rotate(-90)`} textAnchor="middle" fontFamily={PUBLICATION_CHART_STYLE.fontFamily} fontSize={17} fill={CHART_COLORS.axis}>
        Density
      </text>
    </svg>
  );
}

const ResidualPlotChart: React.FC<Props> = ({ data, variant = 'scatter' }) => {
  const points = useMemo(() => cleanPoints(data), [data]);

  if (!data || points.length === 0) {
    return <p style={{ color: '#999' }}>No residual data available.</p>;
  }

  return variant === 'distribution'
    ? <ResidualDistributionSvg points={points} />
    : <ResidualScatterSvg points={points} />;
};

export default ResidualPlotChart;
