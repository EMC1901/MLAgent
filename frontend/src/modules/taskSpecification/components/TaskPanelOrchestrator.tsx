import React from 'react';
import TaskInterpretationPanel from '../../taskInterpretation/components/TaskInterpretationPanel';
import DatasetProfilePanel from '../../datasetProfile/components/DatasetProfilePanel';
import WorkflowPlanPanel from '../../workflowPlanning/components/WorkflowPlanPanel';
import FeatureEngineeringPanel from '../../featureEngineering/components/FeatureEngineeringPanel';
import FeaturePreprocessingPanel from '../../featurePreprocessing/components/FeaturePreprocessingPanel';
import ModelSearchContextPanel from '../../modelSearchContext/components/ModelSearchContextPanel';
import PipelineGenerationPanel from '../../pipelineGeneration/components/PipelineGenerationPanel';
import PipelineExecutionPanel from '../../pipelineExecution/components/PipelineExecutionPanel';
import MetricEvaluationPanel from '../../metricEvaluation/components/MetricEvaluationPanel';
import IterationDecisionPanel from '../../iterationDecision/components/IterationDecisionPanel';
import InterpretabilityAnalysisPanel from '../../interpretabilityAnalysis/components/InterpretabilityAnalysisPanel';
import VisualizationPanel from '../../visualization/components/VisualizationPanel';
import FinalOutputPanel from '../../finalOutput/components/FinalOutputPanel';

type PanelComponent = React.ComponentType<any>;

interface PanelDef {
  key: string;
  component: PanelComponent;
  dependsOnResult?: boolean;
}

interface TaskPanelOrchestratorProps {
  activeTaskId: string;
  panelResults: Record<string, any>;
  onRerunComplete: () => Promise<void>;
}

const PANEL_DEFS: PanelDef[] = [
  { key: 'interpretation', component: TaskInterpretationPanel, dependsOnResult: true },
  { key: 'datasetProfile', component: DatasetProfilePanel, dependsOnResult: true },
  { key: 'workflowPlan', component: WorkflowPlanPanel, dependsOnResult: true },
  { key: 'featureEngineering', component: FeatureEngineeringPanel, dependsOnResult: true },
  { key: 'featurePreprocessing', component: FeaturePreprocessingPanel, dependsOnResult: true },
  { key: 'modelSearchContext', component: ModelSearchContextPanel, dependsOnResult: true },
  { key: 'pipelineGeneration', component: PipelineGenerationPanel, dependsOnResult: true },
  { key: 'pipelineExecution', component: PipelineExecutionPanel, dependsOnResult: true },
  { key: 'metricEvaluation', component: MetricEvaluationPanel, dependsOnResult: true },
  { key: 'iterationDecision', component: IterationDecisionPanel, dependsOnResult: true },
  { key: 'interpretabilityAnalysis', component: InterpretabilityAnalysisPanel, dependsOnResult: true },
  { key: 'visualization', component: VisualizationPanel },
  { key: 'finalOutput', component: FinalOutputPanel, dependsOnResult: true },
];

const TaskPanelOrchestrator: React.FC<TaskPanelOrchestratorProps> = ({
  activeTaskId, panelResults, onRerunComplete,
}) => {
  return (
    <>
      {PANEL_DEFS.map(({ key, component: Component, dependsOnResult }) => {
        const props: Record<string, any> = {
          taskId: activeTaskId,
          key: `${key}-${activeTaskId}`,
        };
        if (dependsOnResult) {
          props.initialResult = panelResults[key];
        }
        if (key === 'iterationDecision') {
          props.onRerunComplete = onRerunComplete;
        }
        return <Component {...props} />;
      })}
    </>
  );
};

export default TaskPanelOrchestrator;
