import logging
from typing import List, Dict, Any, Optional

from app.modules.interpretability_analysis.schemas import (
    LLMInterpretabilitySummary,
    GlobalFeatureImportanceItem,
    ShapSummary,
    FeatureGroupSummary,
)

logger = logging.getLogger(__name__)


def build_full_report(
    llm_summary: LLMInterpretabilitySummary,
    global_feature_importance: List[GlobalFeatureImportanceItem],
    shap_summary: Optional[ShapSummary] = None,
    feature_group_summary: Optional[FeatureGroupSummary] = None,
    cross_method_consensus: Optional[Dict[str, Any]] = None,
    partial_dependence: Optional[Dict[str, Any]] = None,
    correlation_analysis: Optional[Dict[str, Any]] = None,
    residual_analysis: Optional[Dict[str, Any]] = None,
    physics_constraints: Optional[Dict[str, Any]] = None,
    task_summary: Optional[Dict[str, Any]] = None,
    model_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a comprehensive English-language interpretability report combining
    LLM-generated insights with structured numerical results.
    """
    sections: List[Dict[str, Any]] = []

    # Section 1: Model overview
    sections.append(_build_model_overview(task_summary, model_summary, residual_analysis))

    # Section 2: Key findings summary (from LLM)
    sections.append(_build_key_findings(llm_summary))

    # Section 3: Global feature importance
    sections.append(_build_importance_section(global_feature_importance, cross_method_consensus))

    # Section 4: Feature group analysis
    if feature_group_summary:
        sections.append(_build_group_section(feature_group_summary))

    # Section 5: SHAP analysis
    if shap_summary and shap_summary.shap_available:
        sections.append(_build_shap_section(shap_summary))

    # Section 6: Partial dependence
    if partial_dependence:
        sections.append(_build_pdp_section(partial_dependence))

    # Section 7: Correlation structure
    if correlation_analysis:
        sections.append(_build_correlation_section(correlation_analysis))

    # Section 8: Error analysis
    if residual_analysis:
        sections.append(_build_residual_section(residual_analysis))

    # Section 9: Physics constraints
    if physics_constraints:
        sections.append(_build_physics_section(physics_constraints))

    # Section 10: Material insights (from LLM)
    sections.append(_build_material_insights(llm_summary))

    # Section 11: Domain hypotheses (from LLM)
    sections.append(_build_hypotheses(llm_summary))

    # Section 12: Limitations and review notes
    sections.append(_build_limitations(llm_summary))

    logger.info("Full report built — %d sections, confidence=%s",
                 len(sections), llm_summary.confidence_level)
    return {
        "title": "Model Interpretability Analysis Report",
        "language": "en",
        "sections": sections,
        "confidence_level": llm_summary.confidence_level,
    }


def _build_model_overview(
    task_summary: Optional[Dict[str, Any]],
    model_summary: Optional[Dict[str, Any]],
    residual_analysis: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    metrics_text = ""
    if residual_analysis:
        r2 = residual_analysis.get("r_squared", "N/A")
        rmse = residual_analysis.get("rmse", "N/A")
        metrics_text = f"Model performance: R² = {r2}, RMSE = {rmse}"

    return {
        "section_id": "model_overview",
        "title": "Model Overview",
        "content_type": "text",
        "text": metrics_text or "Model performance metrics are available in the detailed analysis below.",
        "data": {
            "task": task_summary or {},
            "model": model_summary or {},
            "performance": {
                "r_squared": residual_analysis.get("r_squared") if residual_analysis else None,
                "rmse": residual_analysis.get("rmse") if residual_analysis else None,
            },
        },
    }


def _build_key_findings(llm_summary: LLMInterpretabilitySummary) -> Dict[str, Any]:
    return {
        "section_id": "key_findings",
        "title": "Key Findings",
        "content_type": "text",
        "text": (
            "The interpretability analysis reveals the following key patterns in how "
            "the model makes predictions. These findings are based on a combination of "
            "feature importance rankings, SHAP value analysis, partial dependence plots, "
            "and cross-method validation."
        ),
        "data": {},
    }


def _build_importance_section(
    global_feature_importance: List[GlobalFeatureImportanceItem],
    cross_method_consensus: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    top_10 = [
        {
            "rank": fi.importance_rank,
            "feature": fi.feature_name,
            "importance": round(fi.importance_value, 6),
            "method": fi.importance_method,
            "group": fi.feature_group,
        }
        for fi in global_feature_importance[:10]
    ]

    consensus_text = ""
    if cross_method_consensus:
        score = cross_method_consensus.get("overall_agreement_score", 0)
        consensus_features = cross_method_consensus.get("consensus_features", [])
        divergent = cross_method_consensus.get("divergent_features", [])
        consensus_text = (
            f"Cross-method agreement score: {score:.2f}. "
            f"{len(consensus_features)} features show consensus across methods. "
            f"{len(divergent)} features show divergent rankings."
        )

    return {
        "section_id": "feature_importance",
        "title": "Global Feature Importance",
        "content_type": "ranking_table",
        "text": consensus_text or "Top features by importance across all computed methods.",
        "data": {
            "top_features": top_10,
            "cross_method_consensus": {
                "agreement_score": cross_method_consensus.get("overall_agreement_score") if cross_method_consensus else None,
                "consensus_features": cross_method_consensus.get("consensus_features", [])[:10] if cross_method_consensus else [],
                "divergent_features": cross_method_consensus.get("divergent_features", [])[:5] if cross_method_consensus else [],
            },
        },
    }


def _build_group_section(feature_group_summary: FeatureGroupSummary) -> Dict[str, Any]:
    groups = feature_group_summary.feature_groups
    group_data = {}
    for name, info in sorted(groups.items(), key=lambda x: x[1].get("total_importance", 0), reverse=True):
        group_data[name] = {
            "feature_count": info.get("feature_count", 0),
            "total_importance": round(info.get("total_importance", 0), 6),
            "mean_importance": round(info.get("mean_importance", 0), 6),
            "top_features": info.get("top_features", []),
        }

    return {
        "section_id": "feature_groups",
        "title": "Feature Group Analysis",
        "content_type": "group_breakdown",
        "text": feature_group_summary.summary_text,
        "data": {"groups": group_data},
    }


def _build_shap_section(shap_summary: ShapSummary) -> Dict[str, Any]:
    top_shap = [
        {
            "rank": f.rank,
            "feature": f.feature_name,
            "mean_abs_shap": round(f.mean_abs_shap, 6),
        }
        for f in shap_summary.top_shap_features[:15]
    ]

    return {
        "section_id": "shap_analysis",
        "title": "SHAP Value Analysis",
        "content_type": "text",
        "text": (
            f"SHAP analysis was performed using {shap_summary.explainer_type} explainer "
            f"on {shap_summary.n_samples_explained} samples. "
            f"The mean absolute SHAP value measures the average impact of each feature "
            f"on the model's output magnitude."
        ),
        "data": {
            "explainer_type": shap_summary.explainer_type,
            "n_samples": shap_summary.n_samples_explained,
            "top_shap_features": top_shap,
        },
    }


def _build_pdp_section(pdp: Dict[str, Any]) -> Dict[str, Any]:
    pdp_1d = pdp.get("pdp_1d", [])
    pdp_2d = pdp.get("pdp_2d", [])
    feature_names = [p["feature_name"] for p in pdp_1d]

    return {
        "section_id": "partial_dependence",
        "title": "Partial Dependence Analysis",
        "content_type": "text",
        "text": (
            f"1D partial dependence plots were computed for {len(pdp_1d)} features: "
            f"{', '.join(feature_names[:8])}. "
            f"{len(pdp_2d)} 2D interaction PDPs were computed. "
            f"These plots show how the model's predictions change as each feature varies, "
            f"marginalizing over all other features."
        ),
        "data": {"n_1d_plots": len(pdp_1d), "n_2d_plots": len(pdp_2d), "features": feature_names},
    }


def _build_correlation_section(corr: Dict[str, Any]) -> Dict[str, Any]:
    high_pairs = corr.get("high_correlation_pairs", [])
    target_corr = corr.get("target_correlations", [])
    n_features = len(corr.get("feature_names", []))

    high_pair_text = ""
    if high_pairs:
        top_pair = high_pairs[0]
        high_pair_text = (
            f"Strongest feature-feature correlation: {top_pair['feature_1']} vs "
            f"{top_pair['feature_2']} (r={top_pair['correlation']:.3f}). "
        )

    top_target = ""
    if target_corr:
        best = target_corr[0]
        top_target = (
            f"Strongest feature-target correlation: {best['feature_name']} "
            f"(Pearson r={best['pearson_r']:.3f}, Spearman ρ={best['spearman_rho']:.3f})."
        )

    return {
        "section_id": "correlation_analysis",
        "title": "Feature Correlation Structure",
        "content_type": "text",
        "text": f"Correlation analysis across {n_features} features. {high_pair_text}{top_target}",
        "data": {
            "n_features": n_features,
            "high_correlation_pairs": high_pairs[:10],
            "top_target_correlations": target_corr[:10],
        },
    }


def _build_residual_section(res: Dict[str, Any]) -> Dict[str, Any]:
    r2 = res.get("r_squared", 0)
    rmse = res.get("rmse", 0)
    seg_count = len(res.get("systematic_error_segments", []))

    quality = "excellent" if r2 > 0.9 else "good" if r2 > 0.7 else "moderate" if r2 > 0.5 else "limited"

    return {
        "section_id": "residual_analysis",
        "title": "Residual & Error Analysis",
        "content_type": "text",
        "text": (
            f"The model achieves {quality} predictive accuracy (R² = {r2:.4f}, "
            f"RMSE = {rmse:.6f}). Residual mean = {res.get('residual_mean', 0):.6f}, "
            f"std = {res.get('residual_std', 0):.6f}. "
            f"Systematic error patterns were detected across {seg_count} prediction segments."
        ),
        "data": {
            "r_squared": r2,
            "rmse": rmse,
            "residual_mean": res.get("residual_mean"),
            "residual_std": res.get("residual_std"),
            "systematic_error_segments": res.get("systematic_error_segments", []),
            "histogram_bins": res.get("histogram_bins", []),
        },
    }


def _build_physics_section(phys: Dict[str, Any]) -> Dict[str, Any]:
    constraints = phys.get("constraints", [])
    all_passed = phys.get("passed", True)
    violations = [c for c in constraints if not c.get("passed", True)]

    status = "All physics constraints passed." if all_passed else (
        f"{len(violations)} constraint(s) violated: "
        + ", ".join(c["constraint_name"] for c in violations)
    )

    return {
        "section_id": "physics_constraints",
        "title": "Physics Constraint Validation",
        "content_type": "text",
        "text": status,
        "data": {
            "all_passed": all_passed,
            "constraints": constraints,
            "n_violations": len(violations),
        },
    }


def _build_material_insights(llm_summary: LLMInterpretabilitySummary) -> Dict[str, Any]:
    patterns = []
    for mp in llm_summary.top_material_patterns:
        if hasattr(mp, "model_dump"):
            mp = mp.model_dump()
        patterns.append(mp)

    return {
        "section_id": "material_insights",
        "title": "Material Science Insights",
        "content_type": "insight_cards",
        "text": (
            "The following material science patterns were identified from the model's "
            "feature importance structure. Each pattern is labeled with its evidence "
            "strength and should be treated as a model-based association."
        ),
        "data": {
            "patterns": patterns,
            "feature_group_interpretations": [
                fg.model_dump() if hasattr(fg, "model_dump") else fg
                for fg in llm_summary.feature_groups_interpretation
            ],
        },
    }


def _build_hypotheses(llm_summary: LLMInterpretabilitySummary) -> Dict[str, Any]:
    return {
        "section_id": "domain_hypotheses",
        "title": "Domain Hypotheses",
        "content_type": "bullet_list",
        "text": (
            "The following hypotheses are derived from model behavior and should be "
            "validated through targeted experiments or literature review."
        ),
        "data": {
            "hypotheses": llm_summary.domain_hypotheses,
        },
    }


def _build_limitations(llm_summary: LLMInterpretabilitySummary) -> Dict[str, Any]:
    return {
        "section_id": "limitations",
        "title": "Limitations & Review Notes",
        "content_type": "bullet_list",
        "text": "Every interpretability analysis has inherent limitations. The items below highlight known caveats and areas requiring human expert review.",
        "data": {
            "limitations": llm_summary.limitations,
            "human_review_notes": llm_summary.human_review_notes,
        },
    }
