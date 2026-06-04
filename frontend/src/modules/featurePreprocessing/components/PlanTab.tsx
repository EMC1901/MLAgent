import React from 'react';
import { FeaturePreprocessingResponse, OperationSequenceItem, PPRationale } from '../types';
import { STATUS_COLORS } from '../constants';
import { PlanTabStyles as s } from './styles';

const Badge: React.FC<{ label: string; color?: string }> = ({ label, color = '#1976d2' }) => (
  <span style={{ ...s.badge, backgroundColor: color }}>{label}</span>
);

const renderRationale = (r: PPRationale | null) => {
  if (!r) return null;
  return (
    <div style={s.rationaleBox}>
      {r.reason && <div><strong>Reason:</strong> {r.reason}</div>}
      {r.evidence && r.evidence.length > 0 && <div><strong>Evidence:</strong> {r.evidence.join('; ')}</div>}
      {r.expected_benefit && <div><strong>Benefit:</strong> {r.expected_benefit}</div>}
      {r.risk && <div><strong>Risk:</strong> {r.risk}</div>}
      {r.fallback && <div><strong>Fallback:</strong> {r.fallback}</div>}
    </div>
  );
};

const getStatusColor = (status: string): string => {
  const colorMap: Record<string, string> = {
    preprocessed: '#4caf50',
    preprocessed_with_warning: '#ff9800',
    failed: '#f44336',
    blocked: '#9e9e9e',
    pending: '#9e9e9e',
  };
  return colorMap[status] || '#9e9e9e';
};

interface PlanTabProps {
  result: FeaturePreprocessingResponse;
}

const PlanTab: React.FC<PlanTabProps> = ({ result }) => {
  const plan = result.preprocessing_plan;
  if (!plan) return null;

  const globalOps = plan.operation_sequence.filter((o: OperationSequenceItem) => o.execution_scope === 'dataset_profile_only');
  const foldOps = plan.operation_sequence.filter((o: OperationSequenceItem) => o.execution_scope === 'fold_only');

  return (
    <div>
      <div style={s.card}>
        <h4 style={s.cardTitle}>Status</h4>
        <div style={s.grid}>
          <div style={s.field}><strong>Preprocessing ID:</strong> {result.preprocessing_id}</div>
          <div style={s.field}>
            <strong>Status: </strong>
            <Badge label={result.status} color={getStatusColor(result.status)} />
          </div>
          <div style={s.field}><strong>FE ID:</strong> {result.feature_engineering_id || '—'}</div>
          <div style={s.field}><strong>WP ID:</strong> {result.workflow_plan_id || '—'}</div>
          {result.preprocessing_registry_snapshot_version && (
            <div style={s.field}><strong>Registry:</strong> {result.preprocessing_registry_snapshot_version}</div>
          )}
        </div>
      </div>

      <div style={s.card}>
        <h4 style={s.cardTitle}>Preprocessing Plan (AI-Generated)</h4>
        <div style={s.field}>
          <strong>Plan Version:</strong> {plan.plan_version}
          {plan.plan_id && <span style={{ marginLeft: '16px' }}><strong>Plan ID:</strong> {plan.plan_id}</span>}
        </div>
      </div>

      {plan.global_policy && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Global Policy</h4>
          <div style={s.subCard}>
            <strong>Leakage Prevention:</strong>
            <div style={{ marginLeft: '12px', fontSize: '12px' }}>
              scope={plan.global_policy.leakage_prevention.fit_transform_scope}
              , target_excluded={plan.global_policy.leakage_prevention.target_column_excluded ? 'Yes' : 'No'}
              , id_excluded={plan.global_policy.leakage_prevention.id_columns_excluded ? 'Yes' : 'No'}
              , target_aware={plan.global_policy.leakage_prevention.target_aware_selection_allowed ? 'Yes' : 'No'}
            </div>
          </div>
          {plan.global_policy.variant_strategy && (
            <div style={s.subCard}>
              <strong>Variant Strategy:</strong>{' '}
              mode={plan.global_policy.variant_strategy.mode}
            </div>
          )}
        </div>
      )}

      {plan.capability_groups_used && plan.capability_groups_used.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Capability Groups Used</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {plan.capability_groups_used.map((g: string, i: number) => (
              <Badge key={i} label={g} color="#1565c0" />
            ))}
          </div>
        </div>
      )}

      {plan.operation_sequence.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>
            Operation Sequence ({plan.operation_sequence.length} ops)
            {' — '}
            <span style={{ color: '#1565c0', fontSize: '13px' }}>
              Global: {globalOps.length}
            </span>
            {' | '}
            <span style={{ color: '#e65100', fontSize: '13px' }}>
              Fold: {foldOps.length}
            </span>
          </h4>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ ...s.table, minWidth: '700px' }}>
              <thead>
                <tr>
                  <th style={s.th}>#</th>
                  <th style={s.th}>Capability</th>
                  <th style={s.th}>Scope</th>
                  <th style={s.th}>Rationale</th>
                </tr>
              </thead>
              <tbody>
                {plan.operation_sequence.map((op: OperationSequenceItem, i: number) => {
                  const isFold = op.execution_scope === 'fold_only';
                  const isGlobal = op.execution_scope === 'dataset_profile_only';
                  return (
                    <tr key={i} style={{
                      ...s.tableRow,
                      backgroundColor: isFold ? '#fff3e0' : isGlobal ? '#e3f2fd' : 'transparent',
                    }}>
                      <td style={s.td}>{op.step_order}</td>
                      <td style={s.td}>
                        <Badge label={op.capability_id} color={isFold ? '#e65100' : '#2e7d32'} />
                        {op.operation_id && <div style={{ fontSize: '10px', color: '#999' }}>{op.operation_id}</div>}
                      </td>
                      <td style={s.td}>
                        <span style={{
                          color: isFold ? '#e65100' : isGlobal ? '#1565c0' : '#666',
                          fontWeight: 600, fontSize: '12px',
                        }}>
                          {op.execution_scope}
                        </span>
                      </td>
                      <td style={s.td}>{renderRationale(op.decision_rationale)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {plan.column_policies && plan.column_policies.length > 0 && (
        <div style={s.card}>
          <h4 style={s.cardTitle}>Column Policies</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
            {plan.column_policies.map((cp, i: number) => (
              <Badge
                key={i}
                label={`${cp.column_name}: ${cp.action}`}
                color={cp.action === 'drop' ? '#c62828' : cp.action === 'transform' ? '#ff9800' : '#2e7d32'}
              />
            ))}
          </div>
        </div>
      )}

      {plan.rejected_operations && plan.rejected_operations.length > 0 && (
        <div style={s.card}>
          <h4 style={{ ...s.cardTitle, color: '#c62828' }}>Rejected Operations</h4>
          {plan.rejected_operations.map((ro, i: number) => (
            <div key={i} style={{ fontSize: '12px', marginLeft: '8px', color: '#888' }}>
              {ro.capability_id}: {ro.reason}
            </div>
          ))}
        </div>
      )}

      {plan.warnings_for_downstream && plan.warnings_for_downstream.length > 0 && (
        <div style={s.warningBox}>
          <strong>Downstream Warnings:</strong>
          {plan.warnings_for_downstream.map((w: string, i: number) => (
            <div key={i} style={{ marginTop: '2px' }}>{w}</div>
          ))}
        </div>
      )}
    </div>
  );
};

export default PlanTab;
