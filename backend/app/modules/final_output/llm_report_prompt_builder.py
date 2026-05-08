import json
import logging
from typing import Dict, Any, Optional

from app.modules.final_output.schemas import (
    FinalModelSummary,
    FinalMetricSummary,
    InterpretabilitySummary,
    WorkflowTraceSummary,
)
from app.modules.final_output.final_output_input_loader import FinalOutputInput

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a report writer for a materials science AutoML system.

The system has already computed all metrics, selected the final pipeline, and computed interpretability results.

You must not change metric values.
You must not change the selected model.
You must not change feature importance or SHAP values.
You must not invent artifacts.
You must not output executable code.
You must clearly distinguish model-based interpretation from causal scientific conclusions.
You must write a concise, accurate, reproducible final report.

Return your response as a valid JSON object with exactly these fields:
- "executive_summary": string (2-4 sentence executive summary)
- "task_overview": string (summary of the task objective)
- "dataset_summary": string (summary of the dataset used)
- "workflow_summary": string (summary of the AutoML workflow steps)
- "feature_engineering_summary": string (summary of feature engineering)
- "model_search_summary": string (summary of model search and HPO)
- "final_model_summary": string (summary of the selected final model)
- "metric_summary": string (summary of key metrics and performance)
- "interpretability_summary": string (summary of model interpretation results)
- "material_insight_summary": string (summary of material science insights, clearly marked as hypotheses)
- "limitations_and_risks": string (limitations, risks, and caveats)
- "reproducibility_notes": string (notes on reproducibility)
- "artifact_summary": string (summary of generated artifacts)
- "next_steps": string (suggested next steps)
- "confidence_level": one of "low", "medium", "high"
"""


def build_llm_report_context(
    task_summary: Dict[str, Any],
    dataset_summary: Dict[str, Any],
    workflow_summary: Dict[str, Any],
    feature_summary: Dict[str, Any],
    model_search_summary: Dict[str, Any],
    final_model: Dict[str, Any],
    final_metrics: Dict[str, Any],
    selection_summary: Dict[str, Any],
    interpretability: Dict[str, Any],
    shap_summary: Optional[Dict[str, Any]],
    material_insight: Optional[Dict[str, Any]],
    reproducibility: Dict[str, Any],
    artifact_list: Dict[str, Any],
    warnings_list: list = None,
) -> Dict[str, Any]:
    context = {
        "task_overview": {
            "task_type": task_summary.get("task_type", ""),
            "target_column": task_summary.get("target_column", ""),
            "primary_metric": task_summary.get("primary_metric", ""),
        },
        "dataset": {
            "source": dataset_summary.get("source", ""),
            "target_column": dataset_summary.get("target_column", ""),
            "feature_count": dataset_summary.get("feature_count", 0),
        },
        "workflow": {
            "steps_completed": workflow_summary.get("steps_completed", 0),
            "iterations": workflow_summary.get("iterations", 0),
            "refinement_performed": workflow_summary.get("refinement_performed", False),
        },
        "feature_engineering": {
            "strategies": feature_summary.get("strategies", []),
            "feature_count": feature_summary.get("feature_count", 0),
        },
        "model_search": {
            "search_method": model_search_summary.get("search_method", ""),
            "models_evaluated": model_search_summary.get("models_evaluated", 0),
            "hpo_method": model_search_summary.get("hpo_method", ""),
        },
        "final_model": final_model,
        "final_metrics": final_metrics,
        "selection": selection_summary,
        "interpretability": {
            "top_features": interpretability.get("top_features", []),
            "shap_available": bool(shap_summary),
        },
        "material_insight": material_insight or {},
        "reproducibility": {
            "random_state": reproducibility.get("random_state"),
            "validation_strategy": reproducibility.get("validation_strategy", {}),
            "environment": reproducibility.get("environment_summary", {}),
        },
        "artifacts": artifact_list,
        "warnings": warnings_list or [],
    }

    user_message = json.dumps(context, indent=2, default=str)
    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_message": user_message,
        "report_context": context,
    }
