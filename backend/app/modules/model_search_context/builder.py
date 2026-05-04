import uuid
from datetime import datetime
from typing import List
from app.modules.model_search_context.schemas import (
    LLMStrategyAdvice,
    ModelSearchContextInput,
    ModelSearchContextResponse,
)
from app.modules.model_search_context.enums import ModelSearchContextStatus, UpdateMode


def build_model_search_context_response(
    context_id: str,
    context: dict,
    dataset_result: dict,
    feature_group_result: dict,
    preprocessing_result: dict,
    merge_result: dict,
    validation_result: dict,
    llm_advice: dict,
    llm_confidence_score: float,
    warnings: List[str],
    errors: List[str],
    status: str,
    error_message: str = None,
) -> ModelSearchContextResponse:

    llm_strategy_advice = LLMStrategyAdvice(
        candidate_model_families=llm_advice.get("model_strategy_suggestion", {}).get("candidate_model_families", []),
        baseline_models=llm_advice.get("model_strategy_suggestion", {}).get("baseline_models", []),
        preferred_model_bias=llm_advice.get("model_strategy_suggestion", {}).get("preferred_model_bias"),
        hpo_search_method=llm_advice.get("hpo_strategy_suggestion", {}).get("search_method"),
        hpo_budget_level=llm_advice.get("hpo_strategy_suggestion", {}).get("budget_level", "moderate"),
        max_trials=llm_advice.get("hpo_strategy_suggestion", {}).get("max_trials", 30),
        validation_split_strategy=llm_advice.get("validation_strategy_suggestion", {}).get("split_strategy"),
        n_splits=llm_advice.get("validation_strategy_suggestion", {}).get("n_splits", 5),
        adjustment_reasons=llm_advice.get("adjustment_reasons", []),
        risk_notes=llm_advice.get("risk_notes", []),
        confidence_score=llm_confidence_score,
    )

    fmp_ctx = context.get("feature_preprocessing_context", {})
    task_ctx = context.get("task_context", {})

    feature_columns = []
    fmp_json = fmp_ctx.get("preprocessing_json", {}) or {}
    preprocessing_execution = fmp_json.get("preprocessing_execution", {}) or {}
    feature_selection = preprocessing_execution.get("feature_selection", {}) or {}
    if feature_selection.get("retained_features"):
        feature_columns = feature_selection["retained_features"]
    elif fmp_json.get("column_validation"):
        cv = fmp_json["column_validation"]
        if isinstance(cv, dict):
            feature_columns = cv.get("retained_features", [])

    updated_model = merge_result.get("updated_model_strategy", {})
    updated_hpo = merge_result.get("updated_hpo_strategy", {})
    updated_val = merge_result.get("updated_validation_strategy", {})
    updated_eval = merge_result.get("updated_evaluation_strategy", {})

    model_search_input = ModelSearchContextInput(
        model_ready_matrix_path=fmp_ctx.get("model_ready_artifact_path"),
        preprocessing_pipeline_artifact_id=fmp_ctx.get("preprocessor_artifact_id"),
        target_column=task_ctx.get("target_column"),
        feature_columns=feature_columns,
        task_type=task_ctx.get("task_type"),
        primary_metric=task_ctx.get("primary_metric"),
        model_strategy=updated_model,
        validation_strategy=updated_val,
        evaluation_strategy=updated_eval,
        hpo_strategy=updated_hpo,
        ready_for_model_search_plan=True,
    )

    return ModelSearchContextResponse(
        context_id=context_id,
        task_id=context["task_id"],
        workflow_plan_id=context.get("workflow_plan_id"),
        feature_engineering_id=context.get("feature_engineering_id"),
        feature_preprocessing_id=context.get("feature_preprocessing_id"),
        status=status,
        update_mode=UpdateMode.LLM_GUIDED_WITH_SYSTEM_VALIDATION,
        dataset_effective_profile=dataset_result["profile"],
        feature_group_summary=feature_group_result["summary"],
        preprocessing_summary=preprocessing_result["summary"],
        llm_strategy_advice=llm_strategy_advice,
        system_validation_result=validation_result.get("validation_result"),
        strategy_adjustment=merge_result.get("strategy_adjustment"),
        updated_model_strategy=updated_model,
        updated_hpo_strategy=updated_hpo,
        updated_validation_strategy=updated_val,
        updated_evaluation_strategy=updated_eval,
        model_search_context_input=model_search_input,
        warnings=warnings,
        errors=errors,
        error_message=error_message,
        confidence_score=llm_confidence_score,
    )


def build_context_json(response: ModelSearchContextResponse) -> dict:
    return response.model_dump(mode="json")
