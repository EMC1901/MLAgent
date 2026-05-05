from typing import Dict, Any
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.result_diagnosis.exceptions import DiagnosisInputInvalidException


def load_result_diagnosis_input(me: MetricEvaluation) -> Dict[str, Any]:
    di_input = me.result_diagnosis_input_json
    if not di_input:
        raise DiagnosisInputInvalidException(
            f"MetricEvaluation '{me.id}' has no result_diagnosis_input_json."
        )

    required_fields = [
        "metric_evaluation_id",
        "pipeline_execution_id",
        "task_id",
        "primary_metric",
        "metric_direction",
        "best_trial",
        "model_ranking",
        "baseline_comparison",
        "metric_summary",
    ]

    missing = [f for f in required_fields if di_input.get(f) is None and f not in ("metric_summary", "best_trial")]
    if missing:
        raise DiagnosisInputInvalidException(
            f"result_diagnosis_input_json missing required fields: {', '.join(missing)}."
        )

    if not isinstance(di_input.get("model_ranking"), list) or len(di_input.get("model_ranking", [])) == 0:
        raise DiagnosisInputInvalidException(
            "result_diagnosis_input_json has empty or missing model_ranking."
        )

    return di_input
