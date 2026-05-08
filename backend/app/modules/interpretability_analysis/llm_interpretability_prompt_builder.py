import json
import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    GlobalFeatureImportanceItem,
    ShapSummary,
    HighErrorSampleAnalysis,
    FeatureGroupSummary,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an interpretability summarizer for a materials science AutoML system.

The numerical interpretability results (feature importance, SHAP values, local explanations) have already been computed by the system. Your role is strictly to summarize these results in natural language for materials scientists.

CRITICAL RULES:
1. You must NOT modify feature importance values.
2. You must NOT modify SHAP values.
3. You must NOT modify model predictions.
4. You must NOT claim causal mechanisms unless supported by evidence.
5. You must describe model-based associations and hypotheses, not definitive conclusions.
6. You must NOT output executable code (no Python, shell, SQL).
7. You must NOT suggest model retraining or feature modifications.
8. Every material interpretation must be labeled as a hypothesis or model association.

Return your response as a valid JSON object with exactly these fields:
- "top_material_patterns": array of objects with "pattern" (string), "supporting_features" (array of strings), "possible_material_meaning" (string), "evidence_strength" (one of "weak"/"moderate"/"strong"), "caution" (string)
- "feature_groups_interpretation": array of objects with "feature_group" (string) and "summary" (string)
- "domain_hypotheses": array of strings (hypotheses derived from the model behavior)
- "limitations": array of strings (known limitations of the interpretation)
- "human_review_notes": array of strings (items for human reviewers to check)
- "confidence_level": one of "low", "medium", "high"
"""


def build_llm_interpretability_context(
    task_summary: Dict[str, Any],
    final_model_summary: Dict[str, Any],
    final_metric_summary: Dict[str, Any],
    global_feature_importance: List[GlobalFeatureImportanceItem],
    shap_summary: Optional[ShapSummary] = None,
    feature_group_summary: Optional[FeatureGroupSummary] = None,
    high_error_samples: Optional[List[HighErrorSampleAnalysis]] = None,
    feature_engineering_metadata: Optional[Dict[str, Any]] = None,
    preprocessing_metadata: Optional[Dict[str, Any]] = None,
    dataset_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    top_features = [
        {
            "rank": fi.importance_rank,
            "feature": fi.feature_name,
            "importance": round(fi.importance_value, 6),
            "method": fi.importance_method,
            "direction": fi.direction,
        }
        for fi in global_feature_importance[:20]
    ]

    shap_info = None
    if shap_summary and shap_summary.shap_available:
        shap_info = {
            "explainer_type": shap_summary.explainer_type,
            "n_samples": shap_summary.n_samples_explained,
            "top_shap_features": [
                {"rank": f.rank, "feature": f.feature_name, "mean_abs_shap": round(f.mean_abs_shap, 6)}
                for f in shap_summary.top_shap_features[:15]
            ],
        }

    error_sample_info = None
    if high_error_samples:
        error_sample_info = [
            {"rank": s.error_rank, "absolute_error": round(s.absolute_error, 6),
             "possible_factors": s.possible_error_factors[:3]}
            for s in high_error_samples[:5]
        ]

    context = {
        "task_summary": task_summary,
        "final_model_summary": final_model_summary,
        "final_metric_summary": final_metric_summary,
        "top_global_feature_importance": top_features,
        "shap_summary": shap_info,
        "feature_group_summary": feature_group_summary.summary_text if feature_group_summary else "",
        "high_error_samples": error_sample_info,
        "feature_engineering_metadata": feature_engineering_metadata,
        "preprocessing_metadata": preprocessing_metadata,
        "dataset_summary": dataset_summary,
        "instructions": [
            "Do NOT modify importance or SHAP values.",
            "Do NOT claim causal mechanisms.",
            "Label all interpretations as model-based associations.",
            "Do NOT output code.",
            "Do NOT suggest model retraining.",
        ],
    }

    user_message = json.dumps(context, indent=2, default=str)
    return {"system_prompt": SYSTEM_PROMPT, "user_message": user_message, "interpretability_context": context}
