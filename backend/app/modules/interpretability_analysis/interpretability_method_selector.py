import logging
from typing import Any

from app.modules.interpretability_analysis.schemas import InterpretabilityMethodPlan
from app.modules.interpretability_analysis.enums import ImportanceMethod, AnalysisProfile

logger = logging.getLogger(__name__)

SHAP_LINEAR_MODELS = {"linear", "ridge", "lasso", "elastic_net", "elasticnet", "linear_regression", "logistic_regression", "logisticregression"}
SHAP_TREE_MODELS = {"random_forest", "randomforest", "gradient_boosting", "gradientboosting", "xgboost", "xgb", "lightgbm", "lgbm", "decision_tree", "decisiontree", "extra_trees", "extratrees"}
PERMUTATION_ONLY_MODELS = {"svr", "svm", "svc", "knn", "kneighbors", "gaussian_process", "gaussianprocess", "gp", "mlp"}
BASELINE_MODELS = {"dummy_mean", "dummy", "baseline", "dummy_classifier", "dummy_regressor"}


def select_interpretability_methods(
    model_family: str,
    include_shap: bool = True,
    include_permutation: bool = True,
    profile: str = "standard",
) -> InterpretabilityMethodPlan:
    family = (model_family or "").lower()
    methods: list[str] = []
    skipped: list[str] = []
    shap_supported = False
    shap_explainer_type = ""
    notes: list[str] = []

    if family in BASELINE_MODELS:
        notes.append("Baseline model (dummy) - no formal interpretability analysis supported.")
        return InterpretabilityMethodPlan(
            methods_selected=[],
            methods_skipped=["coefficient", "native_importance", "permutation_importance", "shap"],
            methods_failed=[],
            fallbacks_used={},
            shap_supported=False,
            shap_explainer_type="",
            notes=notes,
        )

    if family in SHAP_LINEAR_MODELS:
        if include_permutation:
            methods.append(ImportanceMethod.COEFFICIENT)
        if include_permutation:
            methods.append(ImportanceMethod.PERMUTATION)
        if include_shap:
            methods.append(ImportanceMethod.SHAP)
            shap_supported = True
            shap_explainer_type = "linear_explainer"
    elif family in SHAP_TREE_MODELS:
        methods.append(ImportanceMethod.NATIVE)
        if include_permutation:
            methods.append(ImportanceMethod.PERMUTATION)
        if include_shap:
            methods.append(ImportanceMethod.SHAP)
            shap_supported = True
            shap_explainer_type = "tree_explainer"
    elif family in PERMUTATION_ONLY_MODELS:
        if include_permutation:
            methods.append(ImportanceMethod.PERMUTATION)
        if include_shap:
            if profile == AnalysisProfile.FULL:
                methods.append(ImportanceMethod.SHAP)
                shap_supported = True
                shap_explainer_type = "sampling_explainer"
                notes.append("SHAP for kernel-based models is computationally expensive.")
            else:
                skipped.append("shap")
                notes.append("SHAP skipped for kernel-based model in standard/compact profile.")
    else:
        if include_permutation:
            methods.append(ImportanceMethod.PERMUTATION)
        notes.append(f"Unknown model family '{family}', defaulting to permutation importance only.")

    return InterpretabilityMethodPlan(
        methods_selected=methods,
        methods_skipped=skipped,
        methods_failed=[],
        fallbacks_used={},
        shap_supported=shap_supported,
        shap_explainer_type=shap_explainer_type,
        notes=notes,
    )
