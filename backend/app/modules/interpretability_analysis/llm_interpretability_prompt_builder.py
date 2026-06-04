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

The numerical interpretability results (feature importance, SHAP values, PDP, correlation analysis, residual analysis, physics constraint checks, local explanations) have already been computed by the system. Your role is strictly to summarize these results in natural language for materials scientists.

CRITICAL RULES:
1. You must NOT modify feature importance values.
2. You must NOT modify SHAP values.
3. You must NOT modify model predictions.
4. You must NOT claim causal mechanisms unless supported by evidence.
5. You must describe model-based associations and hypotheses, not definitive conclusions.
6. You must NOT output executable code (no Python, shell, SQL).
7. You must NOT suggest model retraining or feature modifications.
8. Every material interpretation must be labeled as a hypothesis or model association.
9. All output must be in English. Write a complete, well-structured English report.

When analyzing results, consider:
- Cross-method consensus: features ranked highly by multiple importance methods are more trustworthy.
- Partial dependence: monotonic trends suggest straightforward relationships; non-monotonic PDPs suggest complex interactions.
- Correlation structure: highly correlated features may share importance; check for redundancy.
- Residual patterns: systematic errors in specific predicted-value ranges indicate model limitations.
- Physics constraints: violations of known physical laws (e.g., negative band gap) indicate prediction unreliability.
- SHAP interactions: strong feature interactions suggest the model is capturing coupled physical effects.

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
    cross_method_consensus: Optional[Dict[str, Any]] = None,
    partial_dependence: Optional[Dict[str, Any]] = None,
    correlation_analysis: Optional[Dict[str, Any]] = None,
    residual_analysis: Optional[Dict[str, Any]] = None,
    physics_constraints: Optional[Dict[str, Any]] = None,
    material_domain: Optional[str] = None,
    dataset_description: Optional[str] = None,
    stop_rationale: Optional[Dict[str, Any]] = None,
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

    # Extract cross-method consensus summary
    consensus_info = None
    if cross_method_consensus:
        consensus_info = {
            "overall_agreement_score": cross_method_consensus.get("overall_agreement_score"),
            "consensus_features": cross_method_consensus.get("consensus_features", [])[:10],
            "divergent_features": [
                {"feature_name": d["feature_name"], "rank_std": d.get("rank_std")}
                for d in cross_method_consensus.get("divergent_features", [])[:5]
            ],
        }

    # Extract PDP summary
    pdp_info = None
    if partial_dependence:
        pdp_1d = partial_dependence.get("pdp_1d", [])
        if pdp_1d:
            pdp_info = {
                "n_features_with_pdp": len(pdp_1d),
                "top_pdp_features": [
                    {"feature_name": p["feature_name"], "trend": _describe_pdp_trend(p)}
                    for p in pdp_1d[:10]
                ],
            }

    # Extract correlation summary
    corr_info = None
    if correlation_analysis:
        high_pairs = correlation_analysis.get("high_correlation_pairs", [])
        target_corr = correlation_analysis.get("target_correlations", [])
        corr_info = {
            "n_high_correlation_pairs": len(high_pairs),
            "top_high_correlation_pairs": [
                {"feature_1": p["feature_1"], "feature_2": p["feature_2"], "correlation": p["correlation"]}
                for p in high_pairs[:5]
            ],
            "top_target_correlations": target_corr[:10] if target_corr else [],
        }

    # Extract residual summary
    res_info = None
    if residual_analysis:
        res_info = {
            "r_squared": residual_analysis.get("r_squared"),
            "rmse": residual_analysis.get("rmse"),
            "residual_mean": residual_analysis.get("residual_mean"),
            "residual_std": residual_analysis.get("residual_std"),
            "n_systematic_error_segments": len(residual_analysis.get("systematic_error_segments", [])),
        }

    # Extract physics constraint summary
    phys_info = None
    if physics_constraints:
        constraints = physics_constraints.get("constraints", [])
        phys_info = {
            "all_passed": physics_constraints.get("passed", True),
            "violations": [
                {"constraint": c["constraint_name"], "n_violations": c.get("n_violations", 0),
                 "severity": c.get("severity", "warning")}
                for c in constraints if not c.get("passed", True)
            ],
        }

    context = {
        "task_summary": task_summary,
        "final_model_summary": final_model_summary,
        "final_metric_summary": final_metric_summary,
        "top_global_feature_importance": top_features,
        "shap_summary": shap_info,
        "feature_group_summary": feature_group_summary.summary_text if feature_group_summary else "",
        "high_error_samples": error_sample_info,
        "cross_method_consensus": consensus_info,
        "partial_dependence_summary": pdp_info,
        "correlation_summary": corr_info,
        "residual_analysis_summary": res_info,
        "physics_constraint_check": phys_info,
        "material_domain": material_domain,
        "dataset_description": dataset_description,
        "stop_rationale": stop_rationale,
        "feature_engineering_metadata": feature_engineering_metadata,
        "preprocessing_metadata": preprocessing_metadata,
        "dataset_summary": dataset_summary,
        "instructions": [
            "Do NOT modify importance or SHAP values.",
            "Do NOT claim causal mechanisms.",
            "Label all interpretations as model-based associations.",
            "Do NOT output code.",
            "Do NOT suggest model retraining.",
            "Write the complete report in English.",
            "Cross-reference findings across different analysis methods.",
            "Flag any contradictions between model behavior and known physics.",
        ],
    }

    user_message = json.dumps(context, indent=2, default=str)
    logger.info("LLM interpretability context built — %d sections, %d chars",
                 len(context), len(user_message))
    return {"system_prompt": SYSTEM_PROMPT, "user_message": user_message, "interpretability_context": context}


def _describe_pdp_trend(pdp_item: Dict[str, Any]) -> str:
    """Generate a short text description of a PDP curve's trend."""
    values = pdp_item.get("pdp_values", [])
    if not values or len(values) < 2:
        return "insufficient data"
    first, last = values[0], values[-1]
    range_val = max(values) - min(values)
    if range_val < 1e-10:
        return "flat (no variation)"
    change = last - first
    if abs(change) / range_val < 0.1:
        return "mostly flat"
    direction = "increasing" if change > 0 else "decreasing"
    # Check for non-monotonic
    diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
    sign_changes = sum(1 for i in range(1, len(diffs)) if diffs[i] * diffs[i-1] < 0)
    if sign_changes > 1:
        return f"non-monotonic, generally {direction}"
    return direction
