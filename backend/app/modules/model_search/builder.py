from datetime import datetime
from typing import List
from app.modules.model_search.schemas import (
    ModelSearchPlanResponse,
    DatasetContext,
    CandidateModelPlanGroup,
    HPOPlan,
    SearchSpacePlan,
    ValidationPlan,
    EvaluationPlan,
    LLMModelSearchAdvice,
    SystemValidationResult,
    PipelineGenerationInput,
    BaselineModelPlan,
    CandidateModelPlan,
    ExcludedModelPlan,
    TrialAllocationItem,
    SearchSpaceItem,
)
from app.modules.model_search.enums import ModelSearchPlanStatus, PlanningMode


def build_model_search_plan_response(
    plan_id: str,
    context: dict,
    candidate_model_plan_data: dict,
    hpo_plan: HPOPlan,
    search_space_plan: SearchSpacePlan,
    validation_plan: ValidationPlan,
    evaluation_plan: EvaluationPlan,
    validation_result: dict,
    llm_advice: dict,
    llm_confidence_score: float,
    llm_used: bool,
    warnings: List[str],
    errors: List[str],
    status: str,
    error_message: str = None,
) -> ModelSearchPlanResponse:
    """Build the full ModelSearchPlanResponse object."""
    # Build dataset context
    dataset_ctx = DatasetContext(
        model_ready_matrix_path=context.get("model_ready_matrix_path"),
        preprocessing_pipeline_artifact_id=context.get("preprocessing_pipeline_artifact_id"),
        n_samples=context.get("n_samples", 0),
        n_features=context.get("n_features", 0),
        target_column=context.get("target_column"),
        task_type=context.get("task_type"),
        primary_metric=context.get("primary_metric"),
    )

    # Build candidate model plan group
    cand_data = candidate_model_plan_data or {}
    candidate_model_plan = CandidateModelPlanGroup(
        baseline_models=[
            BaselineModelPlan(**b) if isinstance(b, dict) else b
            for b in cand_data.get("baseline_models", [])
        ],
        candidate_models=[
            CandidateModelPlan(**c) if isinstance(c, dict) else c
            for c in cand_data.get("candidate_models", [])
        ],
        excluded_models=[
            ExcludedModelPlan(**e) if isinstance(e, dict) else e
            for e in cand_data.get("excluded_models", [])
        ],
    )

    # Build LLM advice summary
    llm_summary = _build_llm_summary(llm_advice) if llm_used else "LLM advisor not used."
    llm_advice_dto = LLMModelSearchAdvice(
        used=llm_used,
        confidence_score=llm_confidence_score,
        summary=llm_summary,
    )

    # Build system validation result
    validation_result_dto = SystemValidationResult(
        is_valid=validation_result.get("is_valid", True),
        rejected_models=validation_result.get("rejected_models", []),
        rejected_hpo_methods=validation_result.get("rejected_hpo_methods", []),
        fallback_applied=validation_result.get("fallback_applied", False),
        warnings=validation_result.get("warnings", []),
    )

    # Build pipeline generation input
    pipeline_input = PipelineGenerationInput(
        model_ready_matrix_path=context.get("model_ready_matrix_path"),
        preprocessing_pipeline_artifact_id=context.get("preprocessing_pipeline_artifact_id"),
        target_column=context.get("target_column"),
        feature_columns=context.get("feature_columns", []),
        candidate_model_plan=cand_data,
        hpo_plan=hpo_plan.model_dump() if hpo_plan else {},
        search_space_plan=search_space_plan.model_dump() if search_space_plan else {},
        validation_plan=validation_plan.model_dump() if validation_plan else {},
        evaluation_plan=evaluation_plan.model_dump() if evaluation_plan else {},
        ready_for_pipeline_generation=status
        in (ModelSearchPlanStatus.PLANNED, ModelSearchPlanStatus.PLANNED_WITH_WARNING),
    )

    return ModelSearchPlanResponse(
        model_search_plan_id=plan_id,
        task_id=context["task_id"],
        model_search_context_id=context.get("model_search_context_id"),
        feature_preprocessing_id=context.get("feature_preprocessing_id"),
        workflow_plan_id=context.get("workflow_plan_id"),
        status=status,
        planning_mode=PlanningMode.LLM_GUIDED_WITH_REGISTRY_VALIDATION if llm_used else PlanningMode.SYSTEM_ONLY,
        dataset_context=dataset_ctx,
        candidate_model_plan=candidate_model_plan,
        hpo_plan=hpo_plan,
        search_space_plan=search_space_plan,
        validation_plan=validation_plan,
        evaluation_plan=evaluation_plan,
        llm_model_search_advice=llm_advice_dto,
        system_validation_result=validation_result_dto,
        pipeline_generation_input=pipeline_input,
        warnings=warnings,
        errors=errors,
        error_message=error_message,
    )


def _build_llm_summary(llm_advice: dict) -> str:
    parts = []
    recs = llm_advice.get("recommended_model_ids", [])
    if recs:
        parts.append(f"Recommended models: {', '.join(recs)}.")
    hpo = llm_advice.get("hpo_recommendation", {})
    if hpo:
        parts.append(
            f"HPO: {hpo.get('search_method', 'unknown')}, "
            f"budget={hpo.get('budget_level', 'unknown')}, "
            f"trials={hpo.get('max_total_trials', 'unknown')}."
        )
    return " ".join(parts) if parts else "No advice available."


def build_plan_json(response: ModelSearchPlanResponse) -> dict:
    return response.model_dump(mode="json")
