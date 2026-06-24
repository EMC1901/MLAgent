import React, { useMemo } from 'react';
import { FeatureImportanceItem } from '../../types';
import { CHART_COLORS, FEATURE_GROUP_COLORS, PUBLICATION_CHART_STYLE } from '../../constants';

interface Props {
  data: FeatureImportanceItem[];
}

interface ChartItem {
  name: string;
  value: number;
  group: string;
  method: string;
  displayName: string;
}

const WIDTH = 1160;
const HEIGHT = 520;
const MARGIN = { top: 26, right: 24, bottom: 76, left: 118 };
const PLOT_WIDTH = WIDTH - MARGIN.left - MARGIN.right;
const PLOT_HEIGHT = HEIGHT - MARGIN.top - MARGIN.bottom;
const DEFAULT_BAR = '#E97770';
const DEFAULT_BAR_STROKE = '#4a4a4a';
const HIGHLIGHT_BAR = '#1F5A72';

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

function yMaxFor(values: number[]): number {
  const max = Math.max(...values, 0.01);
  const padded = max * 1.12;
  const interval = niceNumber(padded / 7, true);
  return Math.ceil(padded / interval) * interval;
}

function generateTicks(maxValue: number, count = 8): number[] {
  const step = maxValue / (count - 1);
  return Array.from({ length: count }, (_, i) => Number((i * step).toFixed(10)));
}

function formatTick(value: number): string {
  if (value === 0) return '0';
  if (value >= 1) return Number(value.toFixed(2)).toString();
  return value.toFixed(2);
}

function cleanFeatureName(name: string): string {
  let cleaned = name || 'Feature';
  cleaned = cleaned.replace(/^matminer_[a-z0-9_]+__+/i, '');
  cleaned = cleaned.replace(/^[a-z0-9_]+__+/i, '');
  cleaned = cleaned.replace(/\bstd_dev\b/gi, 'std');
  cleaned = cleaned.replace(/\bstandard deviation\b/gi, 'std');
  cleaned = cleaned.replace(/\bweighted average\b/gi, 'weighted avg');
  cleaned = cleaned.replace(/\bminimum\b/gi, 'min');
  cleaned = cleaned.replace(/\bmaximum\b/gi, 'max');
  cleaned = cleaned.replace(/\baverage\b/gi, 'avg');
  cleaned = cleaned.replace(/[=_]/g, ' ');
  cleaned = cleaned.replace(/\bAGNI\s+dir\s+([xyz])\b/gi, 'AGNI $1');
  cleaned = cleaned.replace(/\beta\s+[-+]?\d*\.?\d+(?:e[-+]?\d+)?\b/gi, 'eta');
  cleaned = cleaned.replace(/\bAGNI\s+eta\b/gi, 'AGNI eta');
  cleaned = cleaned.replace(/\s+/g, ' ').trim();
  cleaned = cleaned.replace(/[.;:,]+$/g, '');

  const statMatch = cleaned.match(/^(std|mean|avg|min|max|range|median|mode)\s+(.+)$/i);
  if (statMatch) {
    cleaned = `${statMatch[2]} ${statMatch[1].toLowerCase()}`;
  }
  cleaned = cleaned.replace(/\bAGNI\s+([xyz])\s+eta\b/gi, 'AGNI $1');

  const parts = cleaned.split(' ');
  const deduped: string[] = [];
  for (const part of parts) {
    if (deduped[deduped.length - 1]?.toLowerCase() !== part.toLowerCase()) {
      deduped.push(part);
    }
  }
  return deduped.join(' ');
}

function truncateFeatureName(name: string, max = 18): string {
  if (name.length <= max) return name;
  return `${name.slice(0, max - 3)}...`;
}

function colorForItem(item: ChartItem, index: number): string {
  const groupColor = FEATURE_GROUP_COLORS[item.group];
  if (groupColor && item.group && item.group !== 'other') {
    if (index >= 16) return groupColor;
  }
  if (item.group && /composition|structure|elemental/i.test(item.group) && index >= 16) {
    return HIGHLIGHT_BAR;
  }
  return DEFAULT_BAR;
}

const FeatureImportanceChart: React.FC<Props> = ({ data }) => {
  const chart = useMemo(() => {
    const items: ChartItem[] = (data || [])
      .filter(d => Number.isFinite(d.importance_value))
      .sort((a, b) => b.importance_value - a.importance_value)
      .slice(0, 30)
      .map(d => ({
        name: d.feature_name || 'Feature',
        value: Math.max(0, d.importance_value),
        group: d.feature_group || 'other',
        method: d.importance_method || '',
        displayName: cleanFeatureName(d.feature_name || 'Feature'),
      }));

    if (items.length === 0) return null;
    const yMax = yMaxFor(items.map(item => item.value));
    const yTicks = generateTicks(yMax);
    const xStep = PLOT_WIDTH / items.length;
    const barWidth = Math.max(10, Math.min(32, xStep * 0.78));
    const yScale = (value: number) => MARGIN.top + PLOT_HEIGHT - (value / yMax) * PLOT_HEIGHT;

    return { items, yMax, yTicks, xStep, barWidth, yScale };
  }, [data]);

  if (!chart) {
    return <p style={{ color: '#999' }}>No feature importance data available.</p>;
  }

  return (
    <svg
      className="publication-svg"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label="Feature importance bar chart"
      style={{ width: '100%', height: 'auto', background: '#fff', display: 'block' }}
    >
      <rect x={0} y={0} width={WIDTH} height={HEIGHT} fill="#fff" />
      <rect
        x={MARGIN.left}
        y={MARGIN.top}
        width={PLOT_WIDTH}
        height={PLOT_HEIGHT}
        fill="#fff"
        stroke="#111"
        strokeWidth={3}
      />

      {chart.yTicks.map(tick => {
        const y = chart.yScale(tick);
        return (
          <g key={`y-${tick}`}>
            <line x1={MARGIN.left} y1={y} x2={MARGIN.left + PLOT_WIDTH} y2={y} stroke={CHART_COLORS.grid} strokeWidth={1} opacity={0.42} />
            <line x1={MARGIN.left} y1={y} x2={MARGIN.left + 8} y2={y} stroke="#111" strokeWidth={2} />
            <text
              x={MARGIN.left - 12}
              y={y + 6}
              textAnchor="end"
              fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
              fontSize={22}
              fill="#111"
            >
              {formatTick(tick)}
            </text>
          </g>
        );
      })}

      {chart.items.map((item, index) => {
        const xCenter = MARGIN.left + chart.xStep * index + chart.xStep / 2;
        const x = xCenter - chart.barWidth / 2;
        const y = chart.yScale(item.value);
        const barHeight = MARGIN.top + PLOT_HEIGHT - y;
        const labelY = MARGIN.top + PLOT_HEIGHT - 10;
        return (
          <g key={`${item.name}-${index}`}>
            <rect
              x={x}
              y={y}
              width={chart.barWidth}
              height={barHeight}
              fill={colorForItem(item, index)}
              fillOpacity={0.94}
              stroke={DEFAULT_BAR_STROKE}
              strokeWidth={1.6}
            >
              <title>{`${item.name}: ${item.value.toFixed(6)}${item.method ? ` (${item.method})` : ''}`}</title>
            </rect>
            <text
              transform={`translate(${xCenter + 4} ${labelY}) rotate(-90)`}
              textAnchor="start"
              fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
              fontSize={16}
              fill="#111"
            >
              {truncateFeatureName(item.displayName)}
            </text>
          </g>
        );
      })}

      <text
        transform={`translate(26 ${MARGIN.top + PLOT_HEIGHT / 2}) rotate(-90)`}
        textAnchor="middle"
        fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
        fontSize={24}
        fontWeight={700}
        fill="#111"
      >
        Importance
      </text>
      <text
        x={MARGIN.left + PLOT_WIDTH / 2}
        y={HEIGHT - 18}
        textAnchor="middle"
        fontFamily={PUBLICATION_CHART_STYLE.fontFamily}
        fontSize={24}
        fontWeight={700}
        fill="#111"
      >
        Features
      </text>
    </svg>
  );
};

export default FeatureImportanceChart;
