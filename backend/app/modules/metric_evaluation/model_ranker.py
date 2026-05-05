from typing import List, Optional
from app.modules.metric_evaluation.schemas import (
    TrialMetricResult,
    PipelineMetricResult,
    ModelRankingItem,
)
from app.modules.metric_evaluation.enums import MetricDirection


def _extract_model_family(model_id: str) -> str:
    for prefix in [
        "RandomForest", "XGBoost", "LightGBM", "CatBoost",
        "LinearRegression", "Ridge", "Lasso", "ElasticNet",
        "SVR", "SVC", "LogisticRegression", "KNeighbors",
        "DecisionTree", "GradientBoosting", "AdaBoost",
        "MLP", "GaussianNB", "BernoulliNB",
    ]:
        if prefix.lower() in model_id.lower():
            return prefix
    return model_id.split("_")[0] if "_" in model_id else model_id


def rank_models_and_trials(
    trial_results: List[TrialMetricResult],
    pipeline_results: List[PipelineMetricResult],
    primary_metric: str,
    metric_direction: str,
) -> tuple:
    is_minimize = metric_direction == MetricDirection.MINIMIZE

    evaluated_trials = [
        t for t in trial_results
        if t.status == "evaluated" and t.primary_metric_mean is not None
    ]

    sorted_trials = sorted(
        evaluated_trials,
        key=lambda t: (
            t.primary_metric_mean if is_minimize else -t.primary_metric_mean,
            t.primary_metric_std if t.primary_metric_std is not None else float("inf"),
        ),
    )

    for rank, t in enumerate(sorted_trials, start=1):
        t.rank = rank
        t.is_best_trial = (rank == 1)

    if sorted_trials:
        sorted_trials[0].is_best_trial = True

    best_trial = sorted_trials[0] if sorted_trials else None
    best_model_id = best_trial.model_id if best_trial else None
    best_trial_id = best_trial.trial_id if best_trial else None
    best_pipeline_spec_id = best_trial.pipeline_spec_id if best_trial else None

    for pr in pipeline_results:
        pr_trials = [
            t for t in sorted_trials
            if t.pipeline_spec_id == pr.pipeline_spec_id and t.rank is not None
        ]
        if pr_trials:
            best_pr_trial = min(pr_trials, key=lambda t: t.rank)
            pr.best_trial_id = best_pr_trial.trial_id
            pr.best_primary_metric_value = best_pr_trial.primary_metric_mean

    evaluated_pipelines = [
        p for p in pipeline_results
        if p.n_trials_evaluated > 0 and p.best_primary_metric_value is not None
    ]

    sorted_pipelines = sorted(
        evaluated_pipelines,
        key=lambda p: (
            p.best_primary_metric_value if is_minimize else -p.best_primary_metric_value,
            p.std_primary_metric_value if p.std_primary_metric_value is not None else float("inf"),
        ),
    )

    for rank, p in enumerate(sorted_pipelines, start=1):
        p.rank = rank
        p.is_best_model = (rank == 1)

    ranking_items: List[ModelRankingItem] = []
    for p in sorted_pipelines:
        ranking_items.append(ModelRankingItem(
            rank=p.rank or 0,
            model_id=p.model_id,
            model_family=_extract_model_family(p.model_id),
            pipeline_spec_id=p.pipeline_spec_id,
            best_trial_id=p.best_trial_id,
            primary_metric=primary_metric,
            primary_metric_value=p.best_primary_metric_value,
            metric_direction=metric_direction,
            ranking_reason=(
                f"Rank {p.rank}: best trial {p.best_trial_id} achieved "
                f"{primary_metric}={p.best_primary_metric_value:.6f}"
                if p.best_primary_metric_value is not None
                else f"Rank {p.rank}"
            ),
        ))

    return best_trial, best_model_id, best_trial_id, best_pipeline_spec_id, ranking_items
