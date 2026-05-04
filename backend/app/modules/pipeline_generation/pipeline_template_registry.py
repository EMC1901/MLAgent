from typing import List
from app.modules.pipeline_generation.enums import TaskType
from app.modules.pipeline_generation.exceptions import PipelineSpecBuildException


PIPELINE_TEMPLATES = {
    "tabular_regression_basic": {
        "template_id": "tabular_regression_basic",
        "description": "Basic tabular regression pipeline.",
        "task_type": TaskType.REGRESSION,
        "supports_hpo": False,
        "steps": [
            "load_model_ready_matrix",
            "select_feature_target_columns",
            "apply_validation_split",
            "instantiate_registered_estimator",
            "evaluate_with_registered_metrics",
        ],
    },
    "tabular_regression_hpo": {
        "template_id": "tabular_regression_hpo",
        "description": "Tabular regression pipeline with HPO.",
        "task_type": TaskType.REGRESSION,
        "supports_hpo": True,
        "steps": [
            "load_model_ready_matrix",
            "select_feature_target_columns",
            "apply_validation_split",
            "run_hpo_controller",
            "instantiate_registered_estimator",
            "evaluate_with_registered_metrics",
        ],
    },
    "tabular_classification_basic": {
        "template_id": "tabular_classification_basic",
        "description": "Basic tabular classification pipeline.",
        "task_type": TaskType.CLASSIFICATION,
        "supports_hpo": False,
        "steps": [
            "load_model_ready_matrix",
            "select_feature_target_columns",
            "apply_validation_split",
            "instantiate_registered_estimator",
            "evaluate_with_registered_metrics",
        ],
    },
    "tabular_classification_hpo": {
        "template_id": "tabular_classification_hpo",
        "description": "Tabular classification pipeline with HPO.",
        "task_type": TaskType.CLASSIFICATION,
        "supports_hpo": True,
        "steps": [
            "load_model_ready_matrix",
            "select_feature_target_columns",
            "apply_validation_split",
            "run_hpo_controller",
            "instantiate_registered_estimator",
            "evaluate_with_registered_metrics",
        ],
    },
}


def get_template(task_type: str, hpo_enabled: bool) -> dict:
    if task_type == TaskType.CLASSIFICATION:
        template_id = "tabular_classification_hpo" if hpo_enabled else "tabular_classification_basic"
    else:
        template_id = "tabular_regression_hpo" if hpo_enabled else "tabular_regression_basic"
    return PIPELINE_TEMPLATES.get(template_id, PIPELINE_TEMPLATES["tabular_regression_basic"])


def list_template_ids() -> List[str]:
    return sorted(PIPELINE_TEMPLATES.keys())


def get_template_by_id(template_id: str) -> dict:
    template = PIPELINE_TEMPLATES.get(template_id)
    if not template:
        raise PipelineSpecBuildException(f"Pipeline template '{template_id}' not found.")
    return template
