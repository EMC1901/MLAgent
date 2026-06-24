import React from 'react';
import TaskSpecificationPanel from './TaskSpecificationPanel';
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

export interface PanelDef {
  key: string;
  label: string;
  component: PanelComponent;
  dependsOnResult?: boolean;
}

interface TaskPanelOrchestratorProps {
  activeTaskId: string;
  panelResults: Record<string, any>;
  onRerunComplete: () => Promise<void>;
  /** Callback when a new task is created from the Task Specification panel */
  onNewTaskCreated?: (taskId: string) => void;
  /** If set, only render this specific panel. Otherwise render all. */
  selectedPanelKey?: string;
}

export const PANEL_DEFS: PanelDef[] = [
  { key: 'taskSpecification', label: 'Task Specification', component: TaskSpecificationPanel },
  { key: 'interpretation', label: 'Task Interpretation', component: TaskInterpretationPanel, dependsOnResult: true },
  { key: 'datasetProfile', label: 'Dataset Profile', component: DatasetProfilePanel, dependsOnResult: true },
  { key: 'workflowPlan', label: 'Workflow Plan', component: WorkflowPlanPanel, dependsOnResult: true },
  { key: 'featureEngineering', label: 'Feature Engineering', component: FeatureEngineeringPanel, dependsOnResult: true },
  { key: 'featurePreprocessing', label: 'Data Preprocessing', component: FeaturePreprocessingPanel, dependsOnResult: true },
  { key: 'modelSearchContext', label: 'Model Search Plan', component: ModelSearchContextPanel, dependsOnResult: true },
  { key: 'pipelineGeneration', label: 'Pipeline Generation', component: PipelineGenerationPanel, dependsOnResult: true },
  { key: 'pipelineExecution', label: 'Pipeline Execution', component: PipelineExecutionPanel, dependsOnResult: true },
  { key: 'metricEvaluation', label: 'Metric Evaluation', component: MetricEvaluationPanel, dependsOnResult: true },
  { key: 'iterationDecision', label: 'Iteration Decision', component: IterationDecisionPanel, dependsOnResult: true },
  { key: 'interpretabilityAnalysis', label: 'Interpretability', component: InterpretabilityAnalysisPanel, dependsOnResult: true },
  { key: 'visualization', label: 'Visualization', component: VisualizationPanel },
  { key: 'finalOutput', label: 'Final Output', component: FinalOutputPanel, dependsOnResult: true },
];

const TaskPanelOrchestrator: React.FC<TaskPanelOrchestratorProps> = ({
  activeTaskId, panelResults, onRerunComplete, onNewTaskCreated, selectedPanelKey,
}) => {
  const panelsToRender = selectedPanelKey
    ? PANEL_DEFS.filter(p => p.key === selectedPanelKey)
    : PANEL_DEFS;

  return (
    <>
      {panelsToRender.map(({ key, component: Component, dependsOnResult }) => {
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
        if (key === 'taskSpecification' && onNewTaskCreated) {
          props.onTaskSubmitted = (newTaskId: string) => {
            onNewTaskCreated(newTaskId);
            onRerunComplete();
          };
        }
        return <Component {...props} />;
      })}
    </>
  );
};

export default TaskPanelOrchestrator;
