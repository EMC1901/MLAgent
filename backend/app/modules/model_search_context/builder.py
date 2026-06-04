import logging
import uuid
from datetime import datetime
from typing import List, Optional
from app.shared.config.settings import settings
from app.shared.registry.hpo_registry import get_hpo_method_spec

logger = logging.getLogger(__name__)
from app.modules.model_search_context.schemas import (
    LLMStrategyAdvice,
    ModelSearchContextInput,
    ModelSearchContextResponse,
    StrategyChange,
    StrategyChangeRationale,
    BaselineModelPlan,
    CandidateModelPlan,
    CandidateModelPlanGroup,
    ExcludedModelPlan,
    TrialAllocationItem,
    HPOPlan,
    SearchSpacePlan,
    ValidationPlan,
    EvaluationPlan,
    PipelineGenerationInput,
)
from app.modules.model_search_context.enums import (
    ModelSearchContextStatus,
    UpdateMode,
    HPOBudgetLevel,
    TaskType,
    MetricDirection,
)


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
    execution_plans: dict = None,
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
        ready_for_pipeline_generation=True,
    )

    # Build execution plans
    candidate_model_plan = None
    hpo_plan = None
    search_space_plan = None
    validation_plan = None
    evaluation_plan = None
    pipeline_gen_input = None

    if execution_plans:
        candidate_model_plan = _build_candidate_model_plan_group(execution_plans.get("candidate_model_data", {}))
        hpo_plan = execution_plans.get("hpo_plan")
        search_space_plan = execution_plans.get("search_space_plan")
        validation_plan = execution_plans.get("validation_plan")
        evaluation_plan = execution_plans.get("evaluation_plan")

        ss_dump = search_space_plan.model_dump() if search_space_plan else {}
        cm_dump = candidate_model_plan.model_dump() if candidate_model_plan else {}
        spaces_model_ids = [s.get("model_id") for s in ss_dump.get("spaces", [])]
        cand_model_ids = [c.get("model_id") for c in cm_dump.get("candidate_models", [])]
        logger.info(
            "PG input: search_space_plan model_ids=%s | candidate_model_plan model_ids=%s",
            spaces_model_ids, cand_model_ids,
        )
        if set(spaces_model_ids) != set(cand_model_ids):
            logger.warning(
                "PG input MISMATCH: search_space has model_ids=%s but candidates have model_ids=%s",
                spaces_model_ids, cand_model_ids,
            )

        pipeline_gen_input = PipelineGenerationInput(
            model_ready_matrix_path=fmp_ctx.get("model_ready_artifact_path"),
            preprocessing_pipeline_artifact_id=fmp_ctx.get("preprocessor_artifact_id"),
            target_column=task_ctx.get("target_column"),
            feature_columns=feature_columns,
            candidate_model_plan=cm_dump,
            hpo_plan=hpo_plan.model_dump() if hpo_plan else {},
            search_space_plan=ss_dump,
            validation_plan=validation_plan.model_dump() if validation_plan else {},
            evaluation_plan=evaluation_plan.model_dump() if evaluation_plan else {},
            ready_for_pipeline_generation=True,
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
        candidate_model_plan=candidate_model_plan,
        hpo_plan=hpo_plan,
        search_space_plan=search_space_plan,
        validation_plan=validation_plan,
        evaluation_plan=evaluation_plan,
        pipeline_generation_input=pipeline_gen_input,
        strategy_changes=_convert_strategy_changes(merge_result.get("strategy_changes", [])),
        strategy_change_summary=merge_result.get("strategy_change_summary", ""),
        warnings=warnings,
        errors=errors,
        error_message=error_message,
        confidence_score=llm_confidence_score,
    )


def _build_candidate_model_plan_group(data: dict) -> CandidateModelPlanGroup:
    """Convert raw dicts or Pydantic model lists to CandidateModelPlanGroup."""
    def _coerce(items, model_cls):
        result = []
        for item in items:
            if isinstance(item, model_cls):
                result.append(item)
            elif isinstance(item, dict):
                result.append(model_cls(**item))
            else:
                result.append(model_cls(**item.model_dump()))
        return result

    return CandidateModelPlanGroup(
        baseline_models=_coerce(data.get("baseline_models", []), BaselineModelPlan),
        candidate_models=_coerce(data.get("candidate_models", []), CandidateModelPlan),
        excluded_models=_coerce(data.get("excluded_models", []), ExcludedModelPlan),
    )


def _convert_strategy_changes(changes_data: List[dict]) -> List[StrategyChange]:
    """Convert dict-based strategy changes to StrategyChange models."""
    result = []
    for cd in changes_data:
        if isinstance(cd, StrategyChange):
            result.append(cd)
            continue
        try:
            result.append(StrategyChange(**cd))
        except Exception:
            pass
    return result


def build_context_json(response: ModelSearchContextResponse) -> dict:
    return response.model_dump(mode="json")


# ---- Inlined execution plan builders (from model_search) ----

_METRIC_DIRECTIONS = {
    "MAE": MetricDirection.MINIMIZE,
    "MSE": MetricDirection.MINIMIZE,
    "RMSE": MetricDirection.MINIMIZE,
    "R2": MetricDirection.MAXIMIZE,
    "MAPE": MetricDirection.MINIMIZE,
    "Accuracy": MetricDirection.MAXIMIZE,
    "Precision": MetricDirection.MAXIMIZE,
    "Recall": MetricDirection.MAXIMIZE,
    "F1": MetricDirection.MAXIMIZE,
    "ROC_AUC": MetricDirection.MAXIMIZE,
}

_DEFAULT_SECONDARY = {
    TaskType.REGRESSION: ["RMSE", "R2"],
    TaskType.CLASSIFICATION: ["Accuracy", "F1"],
}


def build_hpo_plan(
    updated_hpo_strategy: dict,
    candidate_models: List[dict],
    baseline_models: List[dict],
    preferred_search_method: str = None,
    max_total_trials_override: int = None,
    llm_trial_allocation: List[dict] = None,
) -> HPOPlan:
    """Build HPO plan from the context's updated_hpo_strategy."""
    enabled = updated_hpo_strategy.get("enabled", True)

    search_method = preferred_search_method or updated_hpo_strategy.get("search_method") or "random_search"
    method_spec = get_hpo_method_spec(search_method)
    if not method_spec:
        search_method = "random_search"

    budget_level = updated_hpo_strategy.get("budget_level", "moderate")

    if max_total_trials_override:
        max_total_trials = max_total_trials_override
    else:
        max_total_trials = int(updated_hpo_strategy.get("max_trials", 30))

    max_allowed = getattr(settings, "MODEL_SEARCH_MAX_TOTAL_TRIALS", 50)
    max_total_trials = min(max_total_trials, max_allowed)

    max_parallel = getattr(settings, "MODEL_SEARCH_DEFAULT_MAX_PARALLEL_TRIALS", 1)

    if llm_trial_allocation:
        trial_allocation = _apply_llm_trial_allocation(
            llm_trial_allocation, candidate_models, baseline_models, max_total_trials,
        )
    else:
        trial_allocation = _allocate_trials(candidate_models, baseline_models, max_total_trials)

    fallback = "random_search" if search_method != "random_search" else None

    return HPOPlan(
        enabled=enabled,
        search_method=search_method,
        budget_level=budget_level,
        max_total_trials=max_total_trials,
        max_parallel_trials=max_parallel,
        trial_allocation=trial_allocation,
        early_stopping=budget_level == HPOBudgetLevel.LOW,
        fallback_method=fallback,
    )


def _apply_llm_trial_allocation(
    llm_allocations: List[dict],
    candidate_models: List[dict],
    baseline_models: List[dict],
    max_total_trials: int,
) -> List[TrialAllocationItem]:
    """Use LLM-provided trial allocation, mapped from model_family to model_id."""
    # Build family → rationale lookup from LLM
    llm_map: dict = {}
    for alloc in llm_allocations:
        family = alloc.get("model_family", "")
        llm_map[family] = {
            "max_trials": int(alloc.get("max_trials", 0)),
            "allocation_rationale": alloc.get("allocation_rationale", ""),
        }

    allocations = []
    # Handle non-HPO baselines (always 0 trials)
    non_hpo_baselines = [b for b in baseline_models if not b.get("hpo_enabled")]
    for b in non_hpo_baselines:
        allocations.append(TrialAllocationItem(
            model_id=b["model_id"],
            max_trials=0,
            allocation_rationale="Baseline model — fixed defaults, no HPO needed.",
        ))

    # Handle HPO baselines + candidates with LLM allocation
    hpo_baselines = [b for b in baseline_models if b.get("hpo_enabled")]
    all_hpo_models = hpo_baselines + candidate_models

    # Sum of LLM-allocated trials (keyed by model_family, not model_id)
    llm_total = sum(llm_map.get(m.get("model_family", ""), {}).get("max_trials", 0)
                    for m in all_hpo_models)

    # If LLM total differs from system max, scale proportionally
    scale = (max_total_trials / llm_total) if llm_total > 0 else 1.0

    allocated = 0
    items: list = []
    for m in all_hpo_models:
        mid = m["model_id"]
        family = m.get("model_family", mid)
        llm_entry = llm_map.get(mid) or llm_map.get(family, {})
        raw = llm_entry.get("max_trials", 0) if llm_entry else 0
        trials = int(raw * scale) if llm_entry else 0
        trials = max(1, min(trials, max_total_trials))  # at least 1 trial for HPO models
        rationale = llm_entry.get("allocation_rationale", "") if llm_entry else ""
        items.append((mid, trials, rationale))
        allocated += trials

    # Redistribute remainder to the last HPO model (int() truncation may drop trials)
    if items and allocated < max_total_trials:
        remainder = max_total_trials - allocated
        last_mid, last_trials, last_rationale = items[-1]
        items[-1] = (last_mid, last_trials + remainder, last_rationale)

    for mid, trials, rationale in items:
        allocations.append(TrialAllocationItem(
            model_id=mid,
            max_trials=trials,
            allocation_rationale=rationale,
        ))

    return allocations


def _allocate_trials(
    candidate_models: List[dict],
    baseline_models: List[dict],
    max_total_trials: int,
) -> List[TrialAllocationItem]:
    """Allocate trial budget across models, weighted by priority."""
    allocations = []

    hpo_baselines = [b for b in baseline_models if b.get("hpo_enabled")]
    non_hpo_baselines = [b for b in baseline_models if not b.get("hpo_enabled")]

    for b in non_hpo_baselines:
        allocations.append(TrialAllocationItem(model_id=b["model_id"], max_trials=0))

    all_hpo_models = hpo_baselines + candidate_models
    if not all_hpo_models:
        return allocations

    priority_weight = {"high": 3, "medium": 2, "low": 1}
    weights = []
    for m in all_hpo_models:
        priority = m.get("priority", "medium")
        weights.append(priority_weight.get(priority, 2))

    total_weight = sum(weights)
    remaining = max_total_trials

    for i, m in enumerate(all_hpo_models):
        if i == len(all_hpo_models) - 1:
            trials = remaining
        else:
            trials = max(1, int(max_total_trials * weights[i] / total_weight))
        trials = max(1, min(trials, remaining))
        remaining -= trials
        allocations.append(TrialAllocationItem(model_id=m["model_id"], max_trials=trials))

    return allocations


def build_validation_plan(updated_validation_strategy: dict) -> ValidationPlan:
    """Build validation plan from updated strategy."""
    return ValidationPlan(
        split_strategy=updated_validation_strategy.get("split_strategy", "k_fold_cross_validation"),
        n_splits=int(updated_validation_strategy.get("n_splits", 5)),
        random_state=int(updated_validation_strategy.get("random_state", 42)),
        shuffle=bool(updated_validation_strategy.get("shuffle", True)),
        stratification_required=bool(updated_validation_strategy.get("stratification_required", False)),
        benchmark_split=bool(updated_validation_strategy.get("benchmark_split", False)),
    )


def _normalize_metric_name(name: str) -> str:
    """Map any casing of a known metric name to its canonical (Title Case) form."""
    if not name:
        return name
    for canonical in _METRIC_DIRECTIONS:
        if canonical.lower() == name.lower():
            return canonical
    return name


def build_evaluation_plan(
    primary_metric: str,
    task_type: str,
    updated_evaluation_strategy: dict,
) -> EvaluationPlan:
    """Build evaluation plan with metric direction and secondary metrics."""
    primary_metric = _normalize_metric_name(primary_metric)
    metric_direction = _METRIC_DIRECTIONS.get(primary_metric, MetricDirection.MINIMIZE)
    secondary = updated_evaluation_strategy.get(
        "secondary_metrics",
        _DEFAULT_SECONDARY.get(task_type, []),
    )
    return EvaluationPlan(
        primary_metric=primary_metric,
        metric_direction=metric_direction,
        secondary_metrics=list(secondary) if secondary else [],
        scorer_id=updated_evaluation_strategy.get("scorer_id"),
    )
