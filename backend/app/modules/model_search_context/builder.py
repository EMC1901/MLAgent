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

_COMPLEX_HPO_MODEL_FAMILIES = {
    "xgboost",
    "lightgbm",
    "gradient_boosting",
    "mlp",
}


def _profile_get(dataset_profile: dict, key: str, default=None):
    if not dataset_profile:
        return default
    if isinstance(dataset_profile, dict):
        return dataset_profile.get(key, default)
    return getattr(dataset_profile, key, default)


def _is_resource_constrained_profile(dataset_profile: dict) -> bool:
    if _profile_get(dataset_profile, "is_small_sample", False):
        return True
    if _profile_get(dataset_profile, "is_low_feature", False):
        return True

    n_samples = _profile_get(dataset_profile, "n_samples")
    n_features = _profile_get(dataset_profile, "n_final_features")
    small_sample_threshold = getattr(settings, "MODEL_CONTEXT_SMALL_SAMPLE_THRESHOLD", 200)
    low_feature_threshold = getattr(settings, "MODEL_CONTEXT_LOW_FEATURE_THRESHOLD", 20)
    return (
        (n_samples is not None and n_samples > 0 and n_samples < small_sample_threshold)
        or (n_features is not None and n_features > 0 and n_features < low_feature_threshold)
    )


def _is_large_hpo_profile(dataset_profile: dict) -> bool:
    n_samples = _profile_get(dataset_profile, "n_samples", 0) or 0
    n_features = _profile_get(dataset_profile, "n_final_features", 0) or 0
    return n_samples >= 1000 and n_features >= 50


def _resolve_max_total_trials(
    updated_hpo_strategy: dict,
    budget_level: str,
    method_spec: dict,
    max_total_trials_override: int = None,
    dataset_profile: dict = None,
) -> int:
    if max_total_trials_override is not None:
        requested = int(max_total_trials_override)
    else:
        requested = int(updated_hpo_strategy.get("max_trials", 30))

    normal_cap = int(getattr(settings, "MODEL_CONTEXT_MAX_HPO_TRIALS", 50))
    small_cap = int(getattr(settings, "MODEL_CONTEXT_DEFAULT_HPO_MAX_TRIALS_SMALL", 20))
    large_cap = int(getattr(settings, "MODEL_CONTEXT_LARGE_HPO_MAX_TRIALS", 100))
    hard_cap = int(getattr(settings, "MODEL_CONTEXT_HARD_MAX_HPO_TRIALS", 200))
    if method_spec:
        large_cap = max(large_cap, int(method_spec.get("default_max_trials_large", large_cap)))

    if _is_resource_constrained_profile(dataset_profile):
        adaptive_cap = min(normal_cap, small_cap)
    elif (
        budget_level == HPOBudgetLevel.HIGH
        or updated_hpo_strategy.get("search_space_width") == "wide"
        or _is_large_hpo_profile(dataset_profile)
    ):
        adaptive_cap = max(normal_cap, large_cap)
    else:
        adaptive_cap = normal_cap

    max_allowed = min(adaptive_cap, hard_cap)
    return max(1, min(requested, max_allowed))


def _model_id(model: dict) -> str:
    return model.get("model_id", "")


def _model_family(model: dict) -> str:
    return model.get("model_family") or model.get("model_id", "")


def _priority_trial_weight(model: dict) -> int:
    priority_weight = {"high": 3, "medium": 2, "low": 1}
    return priority_weight.get(model.get("priority", "medium"), 2)


def _build_trial_floors(
    all_hpo_models: List[dict],
    max_total_trials: int,
    budget_level: str,
    dataset_profile: dict = None,
) -> dict:
    floors = {_model_id(model): 1 for model in all_hpo_models}
    if (
        budget_level == HPOBudgetLevel.LOW
        or _is_resource_constrained_profile(dataset_profile)
        or not all_hpo_models
    ):
        return floors

    complex_models = [
        model
        for model in all_hpo_models
        if _model_family(model) in _COMPLEX_HPO_MODEL_FAMILIES
    ]
    if not complex_models:
        return floors

    requested_min = int(getattr(settings, "MODEL_CONTEXT_COMPLEX_MODEL_MIN_TRIALS", 20))
    if budget_level == HPOBudgetLevel.HIGH:
        requested_min = int(getattr(settings, "MODEL_CONTEXT_COMPLEX_MODEL_HIGH_MIN_TRIALS", 30))

    non_complex_count = len(all_hpo_models) - len(complex_models)
    reserve_for_complex = max_total_trials - non_complex_count
    if reserve_for_complex < len(complex_models):
        return floors

    effective_min = min(requested_min, reserve_for_complex // len(complex_models))
    if effective_min <= 1:
        return floors

    for model in complex_models:
        floors[_model_id(model)] = effective_min
    return floors


def _allocate_hpo_model_trials(
    all_hpo_models: List[dict],
    max_total_trials: int,
    weights_by_model: dict,
    rationales_by_model: dict = None,
    budget_level: str = HPOBudgetLevel.MODERATE,
    dataset_profile: dict = None,
) -> List[TrialAllocationItem]:
    if not all_hpo_models:
        return []

    rationales_by_model = rationales_by_model or {}
    floors = _build_trial_floors(
        all_hpo_models,
        max_total_trials,
        budget_level,
        dataset_profile,
    )
    total_floor = sum(floors.values())
    if total_floor > max_total_trials:
        floors = {_model_id(model): 1 for model in all_hpo_models}
        total_floor = sum(floors.values())

    allocations = dict(floors)
    remaining = max_total_trials - total_floor
    if remaining > 0:
        weights = {
            _model_id(model): max(float(weights_by_model.get(_model_id(model), 0)), 0.0)
            for model in all_hpo_models
        }
        if sum(weights.values()) <= 0:
            weights = {_model_id(model): float(_priority_trial_weight(model)) for model in all_hpo_models}

        total_weight = sum(weights.values())
        additions = []
        used = 0
        for index, model in enumerate(all_hpo_models):
            mid = _model_id(model)
            exact = remaining * weights[mid] / total_weight
            whole = int(exact)
            additions.append((mid, whole, exact - whole, index))
            used += whole

        for mid, whole, _, _ in additions:
            allocations[mid] += whole

        remainder = remaining - used
        for mid, _, _, _ in sorted(additions, key=lambda item: (-item[2], item[3]))[:remainder]:
            allocations[mid] += 1

    return [
        TrialAllocationItem(
            model_id=_model_id(model),
            max_trials=int(allocations.get(_model_id(model), 0)),
            allocation_rationale=rationales_by_model.get(_model_id(model)),
        )
        for model in all_hpo_models
    ]


def build_hpo_plan(
    updated_hpo_strategy: dict,
    candidate_models: List[dict],
    baseline_models: List[dict],
    preferred_search_method: str = None,
    max_total_trials_override: int = None,
    llm_trial_allocation: List[dict] = None,
    dataset_profile: dict = None,
) -> HPOPlan:
    """Build HPO plan from the context's updated_hpo_strategy."""
    enabled = updated_hpo_strategy.get("enabled", True)

    search_method = preferred_search_method or updated_hpo_strategy.get("search_method") or "random_search"
    method_spec = get_hpo_method_spec(search_method)
    if not method_spec:
        search_method = "random_search"

    budget_level = updated_hpo_strategy.get("budget_level", "moderate")
    max_total_trials = _resolve_max_total_trials(
        updated_hpo_strategy=updated_hpo_strategy,
        budget_level=budget_level,
        method_spec=method_spec,
        max_total_trials_override=max_total_trials_override,
        dataset_profile=dataset_profile,
    )

    max_parallel = getattr(settings, "MODEL_SEARCH_DEFAULT_MAX_PARALLEL_TRIALS", 1)

    if llm_trial_allocation:
        trial_allocation = _apply_llm_trial_allocation(
            llm_trial_allocation,
            candidate_models,
            baseline_models,
            max_total_trials,
            budget_level,
            dataset_profile,
        )
    else:
        trial_allocation = _allocate_trials(
            candidate_models,
            baseline_models,
            max_total_trials,
            budget_level,
            dataset_profile,
        )

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
    budget_level: str = HPOBudgetLevel.MODERATE,
    dataset_profile: dict = None,
) -> List[TrialAllocationItem]:
    """Use LLM-provided trial allocation, mapped from model_family to model_id."""
    # Build family-to-rationale lookup from LLM
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
            allocation_rationale="Baseline model uses fixed defaults; no HPO needed.",
        ))

    # Handle HPO baselines + candidates with LLM allocation
    hpo_baselines = [b for b in baseline_models if b.get("hpo_enabled")]
    all_hpo_models = hpo_baselines + candidate_models
    weights_by_model = {}
    rationales_by_model = {}
    for model in all_hpo_models:
        mid = _model_id(model)
        family = _model_family(model)
        llm_entry = llm_map.get(mid) or llm_map.get(family, {})
        weights_by_model[mid] = int(llm_entry.get("max_trials", 0)) if llm_entry else 0
        rationales_by_model[mid] = llm_entry.get("allocation_rationale", "") if llm_entry else ""

    allocations.extend(_allocate_hpo_model_trials(
        all_hpo_models,
        max_total_trials,
        weights_by_model,
        rationales_by_model,
        budget_level,
        dataset_profile,
    ))

    return allocations


def _allocate_trials(
    candidate_models: List[dict],
    baseline_models: List[dict],
    max_total_trials: int,
    budget_level: str = HPOBudgetLevel.MODERATE,
    dataset_profile: dict = None,
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

    weights_by_model = {_model_id(model): _priority_trial_weight(model) for model in all_hpo_models}
    allocations.extend(_allocate_hpo_model_trials(
        all_hpo_models,
        max_total_trials,
        weights_by_model,
        budget_level=budget_level,
        dataset_profile=dataset_profile,
    ))

    return allocations


def build_validation_plan(updated_validation_strategy: dict) -> ValidationPlan:
    """Build validation plan from updated strategy."""
    def _optional_float(value):
        return None if value is None else float(value)

    return ValidationPlan(
        split_strategy=updated_validation_strategy.get("split_strategy", "k_fold_cross_validation"),
        n_splits=int(updated_validation_strategy.get("n_splits", 5)),
        test_size=_optional_float(updated_validation_strategy.get("test_size")),
        external_test_enabled=bool(updated_validation_strategy.get("external_test_enabled", True) or updated_validation_strategy.get("use_external_test", False)),
        external_test_size=_optional_float(updated_validation_strategy.get("external_test_size", 0.2)),
        cv_strategy=updated_validation_strategy.get("cv_strategy") or updated_validation_strategy.get("inner_split_strategy"),
        random_state=int(updated_validation_strategy.get("random_state", 42)),
        shuffle=bool(updated_validation_strategy.get("shuffle", True)),
        stratification_required=bool(updated_validation_strategy.get("stratification_required", False)),
        benchmark_split=bool(updated_validation_strategy.get("benchmark_split", False)),
    )


def _normalize_metric_name(name: str) -> str:
    """Map any casing of a known metric name to its canonical (Title Case) form."""
    if not name:
        return name
    normalised = name.replace("-", "_")
    for canonical in _METRIC_DIRECTIONS:
        if canonical.lower() == normalised.lower():
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
