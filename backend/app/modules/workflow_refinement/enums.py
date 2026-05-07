class WorkflowRefinementStatus:
    DECIDING = "deciding"
    DECIDED = "decided"
    DECIDED_WITH_WARNING = "decided_with_warning"
    ADOPTED = "adopted"
    FAILED = "failed"


class WorkflowRefinementDecision:
    PROCEED_NEXT_STAGE = "proceed_next_stage"
    ITERATE_REFINEMENT = "iterate_refinement"


class DecisionConfidenceLevel:
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RerunStage:
    WORKFLOW_PLANNING = "workflow_planning"
    FEATURE_ENGINEERING = "feature_engineering"
    FEATURE_PREPROCESSING = "feature_preprocessing"
    MODEL_SEARCH_CONTEXT = "model_search_context"
    MODEL_SEARCH = "model_search"
    PIPELINE_GENERATION = "pipeline_generation"
    PIPELINE_EXECUTION = "pipeline_execution"
    METRIC_EVALUATION = "metric_evaluation"
    FINAL_PIPELINE_SELECTION = "final_pipeline_selection"


VALID_RERUN_STAGES = {
    RerunStage.WORKFLOW_PLANNING,
    RerunStage.FEATURE_ENGINEERING,
    RerunStage.FEATURE_PREPROCESSING,
    RerunStage.MODEL_SEARCH_CONTEXT,
    RerunStage.MODEL_SEARCH,
    RerunStage.PIPELINE_GENERATION,
    RerunStage.PIPELINE_EXECUTION,
    RerunStage.METRIC_EVALUATION,
    RerunStage.FINAL_PIPELINE_SELECTION,
}

VALID_DECISIONS = {
    WorkflowRefinementDecision.PROCEED_NEXT_STAGE,
    WorkflowRefinementDecision.ITERATE_REFINEMENT,
}

VALID_CONFIDENCE_LEVELS = {
    DecisionConfidenceLevel.LOW,
    DecisionConfidenceLevel.MEDIUM,
    DecisionConfidenceLevel.HIGH,
}

VALID_STATUSES = {
    WorkflowRefinementStatus.DECIDING,
    WorkflowRefinementStatus.DECIDED,
    WorkflowRefinementStatus.DECIDED_WITH_WARNING,
    WorkflowRefinementStatus.ADOPTED,
    WorkflowRefinementStatus.FAILED,
}


RERUN_STAGE_RECOMMENDATIONS = {
    "feature_insufficiency": RerunStage.WORKFLOW_PLANNING,
    "feature_noise": RerunStage.WORKFLOW_PLANNING,
    "underfitting": RerunStage.WORKFLOW_PLANNING,
    "model_mismatch": RerunStage.MODEL_SEARCH_CONTEXT,
    "hpo_insufficient": RerunStage.MODEL_SEARCH,
    "validation_instability": RerunStage.WORKFLOW_PLANNING,
    "weak_baseline_improvement": RerunStage.WORKFLOW_PLANNING,
    "limited_pipeline_gain": RerunStage.WORKFLOW_PLANNING,
    "pipeline_execution_failure": RerunStage.PIPELINE_GENERATION,
    "metric_calculation_issue": RerunStage.METRIC_EVALUATION,
    "result_good_enough": RerunStage.FINAL_PIPELINE_SELECTION,
}
