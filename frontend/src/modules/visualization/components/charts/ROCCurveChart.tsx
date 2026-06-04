import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, Legend } from 'recharts';
import { ROCCurveData, PRCurveData } from '../../types';
import { CHART_COLORS } from '../../constants';

interface Props {
  rocData: ROCCurveData | null;
  prData: PRCurveData | null;
  taskType: string;
}

const ROCCurveChart: React.FC<Props> = ({ rocData, prData, taskType }) => {
  const [mode, setMode] = useState<'roc' | 'pr'>('roc');

  if (taskType !== 'classification') {
    return <p style={{ color: '#999' }}>ROC and PR curves are only available for classification tasks.</p>;
  }

  const renderROC = () => {
    if (!rocData || !rocData.curves.length) {
      return <p style={{ color: '#999' }}>No ROC curve data available.</p>;
    }
    // merge all curves into one long dataset (each curve has fpr/tpr pairs)
    const allCurves = rocData.curves;
    const combined: { fpr: number; tpr: number; classId: string }[] = [];
    allCurves.forEach(c => {
      c.fpr.forEach((fpr, i) => {
        combined.push({ fpr: +fpr.toFixed(4), tpr: +c.tpr[i].toFixed(4), classId: c.class_id });
      });
    });

    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart margin={{ top: 16, right: 20, left: 16, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis type="number" dataKey="fpr" name="FPR" tick={{ fontSize: 12 }} domain={[0, 1]}
            label={{ value: 'False Positive Rate', position: 'insideBottomRight', offset: -8, fontSize: 12 }} />
          <YAxis type="number" dataKey="tpr" name="TPR" tick={{ fontSize: 12 }} domain={[0, 1]}
            label={{ value: 'True Positive Rate', angle: -90, position: 'insideLeft', offset: -4, fontSize: 12 }} />
          <Tooltip />
          <ReferenceLine segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} stroke="#9e9e9e" strokeDasharray="3 3" />
          <Legend />
          {allCurves.map((c, i) => {
            const curveData = combined.filter(d => d.classId === c.class_id);
            return (
              <Line
                key={c.class_id}
                data={curveData}
                type="stepAfter"
                dataKey="tpr"
                name={`${c.class_id} (AUC=${c.auc.toFixed(3)})`}
                stroke={CHART_COLORS.series[i % CHART_COLORS.series.length]}
                strokeWidth={2}
                dot={false}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const renderPR = () => {
    if (!prData || !prData.curves.length) {
      return <p style={{ color: '#999' }}>No PR curve data available.</p>;
    }
    const allCurves = prData.curves;
    const combined: { recall: number; precision: number; classId: string }[] = [];
    allCurves.forEach(c => {
      c.recall.forEach((rec, i) => {
        combined.push({ recall: +rec.toFixed(4), precision: +c.precision[i].toFixed(4), classId: c.class_id });
      });
    });

    return (
      <ResponsiveContainer width="100%" height={400}>
        <LineChart margin={{ top: 16, right: 20, left: 16, bottom: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
          <XAxis type="number" dataKey="recall" name="Recall" tick={{ fontSize: 12 }} domain={[0, 1]}
            label={{ value: 'Recall', position: 'insideBottomRight', offset: -8, fontSize: 12 }} />
          <YAxis type="number" dataKey="precision" name="Precision" tick={{ fontSize: 12 }} domain={[0, 1]}
            label={{ value: 'Precision', angle: -90, position: 'insideLeft', offset: -4, fontSize: 12 }} />
          <Tooltip />
          <Legend />
          {allCurves.map((c, i) => {
            const curveData = combined.filter(d => d.classId === c.class_id);
            return (
              <Line
                key={c.class_id}
                data={curveData}
                type="monotone"
                dataKey="precision"
                name={`${c.class_id} (AP=${c.average_precision.toFixed(3)})`}
                stroke={CHART_COLORS.series[i % CHART_COLORS.series.length]}
                strokeWidth={2}
                dot={false}
              />
            );
          })}
        </LineChart>
      </ResponsiveContainer>
    );
  };

  const hasROC = rocData && rocData.curves.length > 0;
  const hasPR = prData && prData.curves.length > 0;

  return (
    <div>
      <div style={{ marginBottom: 8, display: 'flex', gap: 8 }}>
        <button
          onClick={() => setMode('roc')}
          disabled={!hasROC}
          style={{
            padding: '4px 12px', border: 'none', borderRadius: '12px', fontSize: '12px', fontWeight: 600, cursor: hasROC ? 'pointer' : 'not-allowed',
            backgroundColor: mode === 'roc' ? '#1976d2' : '#e0e0e0',
            color: mode === 'roc' ? '#fff' : '#333',
            opacity: hasROC ? 1 : 0.5,
          }}
        >
          ROC Curve
        </button>
        <button
          onClick={() => setMode('pr')}
          disabled={!hasPR}
          style={{
            padding: '4px 12px', border: 'none', borderRadius: '12px', fontSize: '12px', fontWeight: 600, cursor: hasPR ? 'pointer' : 'not-allowed',
            backgroundColor: mode === 'pr' ? '#1976d2' : '#e0e0e0',
            color: mode === 'pr' ? '#fff' : '#333',
            opacity: hasPR ? 1 : 0.5,
          }}
        >
          PR Curve
        </button>
      </div>
      {mode === 'roc' ? renderROC() : renderPR()}
    </div>
  );
};

export default ROCCurveChart;
