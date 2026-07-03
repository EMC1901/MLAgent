import json
import logging
from typing import Dict, Any, Optional, List, Set

from app.modules.interpretability_analysis.schemas import ScientificInsightReport

logger = logging.getLogger(__name__)

SCIENTIFIC_INSIGHT_SYSTEM_PROMPT = """You are an evidence-grounded scientific insight synthesizer for a materials machine learning system.

Your task is to convert computed interpretability evidence into research-grade materials-science insights. You must reason from the provided evidence only. Do not invent feature names, numerical values, mechanisms, literature facts, experiments, validation results, or material families that are not present in the input.

You must separate these levels of claim:
1. model_observation: what the model evidence shows.
2. candidate_hypothesis: a falsifiable materials-science hypothesis supported only by model evidence.
3. design_rule: a candidate screening rule with explicit scope and caveats.
4. mechanism_hypothesis: a possible physical or chemical explanation, not a causal conclusion.
5. applicability_boundary: a region where the model or rule is unreliable or weakly supported.
6. validated_conclusion: allowed only when the input contains independent validation evidence.

CRITICAL RULES:
1. Every academic insight MUST cite supporting_evidence_ids from the input evidence_index.
2. Feature importance, SHAP, PDP, attention, correlation, or residual patterns are model evidence, not causal evidence by themselves.
3. If there is no independent validation, label the claim as candidate_hypothesis or model_supported_only.
4. A claim may be called validated_conclusion only if the input contains external validation, DFT/GW/MD validation, experiment, statistical significance testing, or independent holdout evidence.
5. Every insight must include: claim, material_meaning, evidence_chain, evidence_strength, confidence, validation_status, caveats, falsifiable_prediction, suggested_validation, and counterexamples_or_risks.
6. Always report contradictory evidence, weak support, feature-correlation risk, data leakage risk, distribution-shift risk, and scope limits when present.
7. Do NOT restate "feature X is important" as a material insight. Translate model evidence into materials-science language.
8. Do NOT use causal wording such as "causes", "caused by", "determines", "controls", "drives", "driven by", "leads to", or "results in" unless validation evidence supports causal language. Prefer "is associated with", "suggests", "is consistent with", "may indicate", or "within the model-supported domain".
9. Boundary patterns are reliability warnings, not material design rules.
10. Failed material patterns must not be promoted into design rules or validated conclusions.
11. If evidence is insufficient, put the claim in rejected_claims or missing_evidence instead of inventing support.
12. Before returning JSON, self-check every claim and replace unsupported causal phrases such as "driven by" with non-causal association wording.
13. All output must be in English.
14. Return valid JSON only. Do not include Markdown fences.

Return a JSON object with exactly these top-level fields:
- "narrative_title": string
- "executive_summary": string, 2-4 concise paragraphs distinguishing model evidence from scientific conclusions
- "academic_insights": array of objects with:
    - "claim_id": string
    - "claim_type": one of "model_observation", "candidate_hypothesis", "design_rule", "mechanism_hypothesis", "applicability_boundary", "validated_conclusion"
    - "claim": string
    - "material_meaning": string
    - "supporting_evidence_ids": array of strings
    - "evidence_chain": array of objects with "step" and "summary"
    - "evidence_strength": one of "weak", "moderate", "strong"
    - "confidence": one of "low", "medium", "high"
    - "validation_status": one of "model_supported_only", "statistically_supported", "externally_validated", "experimentally_validated", "dft_or_simulation_validated", "insufficient_evidence"
    - "falsifiable_prediction": string
    - "suggested_validation": array of strings
    - "counterexamples_or_risks": array of strings
    - "scope_conditions": array of strings
    - "allowed_wording": string
- "rejected_claims": array of objects with "claim", "reason", and "missing_evidence"
- "missing_evidence": array of objects with "needed_evidence" and "why_it_matters"
- "human_review_notes": array of strings
- "limitations_section": array of objects with "category" and "description"
- "validation_suggestions": array of objects with "claim_id" and "suggestion"
"""


def build_llm_scientific_insight_prompt(
    scientific_report: ScientificInsightReport,
    task_summary: Dict[str, Any],
    final_model_summary: Dict[str, Any],
    final_metric_summary: Dict[str, Any],
    material_domain: Optional[str] = None,
    dataset_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Build an evidence-grounded prompt for academic insight generation.

    The LLM receives structured evidence, candidate material patterns, validation
    results, mechanisms, boundaries, and a strict paper-style quality rubric. The
    output is not a narrative-only report; it is a set of evidence-cited academic
    claims that can be accepted, downgraded, or rejected downstream.
    """
    evidence_index = _build_evidence_index(scientific_report)

    context = {
        "task_summary": task_summary,
        "final_model_summary": final_model_summary,
        "final_metric_summary": final_metric_summary,
        "material_domain": material_domain,
        "dataset_description": dataset_description,
        "paper_style_quality_criteria": [
            "The interpretation is stable across methods, seeds, or data splits when such evidence is available.",
            "The referenced features or structures have clear materials-science meaning.",
            "The claim is expressed as a falsifiable hypothesis, rule, formula, or applicability boundary.",
            "The claim has an explicit scope and does not overgeneralize beyond the sampled material space.",
            "Validated conclusions require independent evidence such as external holdout data, DFT/GW/MD, experiment, spectroscopy, microscopy, or statistical significance testing.",
            "A useful insight should guide screening, substitution design, mechanism testing, or next-step validation.",
        ],
        "validation_ladder": {
            "weak": "single model-evidence source or unstable/uncertain evidence",
            "moderate": "multiple model-evidence sources or validated material pattern, but no external/experimental proof",
            "strong": "independent validation, statistically robust validation, DFT/GW/MD support, or experiment is present in the input",
        },
        "scientific_report": {
            "executive_insights": _summarize_hypotheses(scientific_report.executive_insights, limit=10),
            "ranked_hypotheses": _summarize_hypotheses(scientific_report.ranked_hypotheses, limit=15),
            "material_pattern_candidates": _summarize_patterns(scientific_report.material_pattern_candidates, limit=12),
            "material_mechanism_candidates": _summarize_mechanisms(scientific_report.material_mechanism_candidates, limit=10),
            "model_applicability_boundaries": _summarize_boundaries(scientific_report.model_applicability_boundaries, limit=10),
            "anomaly_patterns": _summarize_anomalies(scientific_report.anomaly_or_counterexample_patterns, limit=8),
            "physics_consistency_summary": scientific_report.physics_consistency_summary,
            "limitations": scientific_report.limitations,
        },
        "evidence_index": evidence_index,
        "instructions": [
            "Generate only evidence-grounded academic insights.",
            "Downgrade unsupported claims instead of strengthening them.",
            "Avoid unsupported causal phrases, especially: caused by, driven by, determines, controls, leads to, results in.",
            "Separate model evidence from scientific conclusion.",
            "Use material-science language, but only when the material concept is present in the input.",
            "Every academic insight must include valid supporting_evidence_ids.",
            "Return the exact JSON object specified in the system prompt.",
        ],
    }

    user_message = json.dumps(context, indent=2, default=str)
    logger.info(
        "LLM scientific insight context built: %d evidence ids, %d chars",
        len(evidence_index),
        len(user_message),
    )
    return {
        "system_prompt": SCIENTIFIC_INSIGHT_SYSTEM_PROMPT,
        "user_message": user_message,
        "scientific_insight_context": context,
    }


def _build_evidence_index(scientific_report: ScientificInsightReport) -> Dict[str, Dict[str, Any]]:
    all_evidence: Dict[str, Any] = {}
    for fp in scientific_report.feature_profiles or []:
        for eu in fp.evidence_units or []:
            if eu.evidence_id and eu.evidence_id not in all_evidence:
                all_evidence[eu.evidence_id] = eu

    needed_ids: Set[str] = set()
    for h in (scientific_report.executive_insights or []) + (scientific_report.ranked_hypotheses or []):
        needed_ids.update(h.supporting_evidence_ids or [])
        needed_ids.update(h.contradicting_evidence_ids or [])
    for p in scientific_report.material_pattern_candidates or []:
        needed_ids.update(p.supporting_evidence_ids or [])
        needed_ids.update(p.contradicting_evidence_ids or [])
        for ce in p.counterexamples or []:
            needed_ids.update(ce.supporting_evidence_ids or [])
        for vr in p.validation_results or []:
            needed_ids.update(vr.supporting_evidence_ids or [])
    for m in scientific_report.material_mechanism_candidates or []:
        needed_ids.update(m.supporting_evidence_ids or [])
    for b in scientific_report.model_applicability_boundaries or []:
        needed_ids.update(b.supporting_evidence_ids or [])
    for a in scientific_report.anomaly_or_counterexample_patterns or []:
        needed_ids.update(a.supporting_evidence_ids or [])

    ordered_ids: List[str] = []
    for fp in (scientific_report.feature_profiles or [])[:30]:
        for eu in (fp.evidence_units or [])[:5]:
            if eu.evidence_id and eu.evidence_id not in ordered_ids:
                ordered_ids.append(eu.evidence_id)
    for eid in needed_ids:
        if eid and eid not in ordered_ids:
            ordered_ids.append(eid)

    evidence_index: Dict[str, Dict[str, Any]] = {}
    for eid in ordered_ids[:100]:
        eu = all_evidence.get(eid)
        if not eu:
            continue
        evidence_index[eid] = {
            "evidence_type": eu.evidence_type,
            "feature_names": eu.feature_names,
            "direction": eu.direction,
            "method_name": eu.method_name,
            "strength": eu.strength,
            "reliability": eu.reliability,
            "quantitative_summary": _compact_value(eu.quantitative_summary),
            "limitations": (eu.limitations or [])[:5],
        }
    return evidence_index


def _summarize_hypotheses(hypotheses: List[Any], limit: int) -> List[Dict[str, Any]]:
    summary = []
    for h in (hypotheses or [])[:limit]:
        summary.append({
            "hypothesis_id": h.hypothesis_id,
            "claim": h.claim,
            "claim_type": h.claim_type,
            "confidence_score": h.confidence_score,
            "confidence_label": h.confidence_label,
            "supporting_evidence_ids": h.supporting_evidence_ids,
            "contradicting_evidence_ids": h.contradicting_evidence_ids,
            "scope_conditions": h.scope_conditions,
            "validation_suggestions": h.validation_suggestions,
            "hypothesis_pattern": h.hypothesis_pattern,
            "confidence_breakdown": h.confidence_breakdown.model_dump() if h.confidence_breakdown else None,
        })
    return summary


def _summarize_patterns(patterns: List[Any], limit: int) -> List[Dict[str, Any]]:
    summary = []
    for p in (patterns or [])[:limit]:
        summary.append({
            "pattern_id": p.pattern_id,
            "pattern_type": p.pattern_type,
            "statement": p.statement,
            "material_concepts": p.material_concepts,
            "conditions": [c.model_dump() for c in p.conditions],
            "predicted_effect": p.predicted_effect.model_dump(),
            "supporting_evidence_ids": p.supporting_evidence_ids,
            "contradicting_evidence_ids": p.contradicting_evidence_ids,
            "counterexamples": [ce.model_dump() for ce in p.counterexamples],
            "scope_conditions": p.scope_conditions,
            "validation_suggestions": p.validation_suggestions,
            "confidence_score": p.confidence_score,
            "confidence_label": p.confidence_label,
            "limitations": p.limitations,
            "validation_status": p.validation_status,
            "sample_support": p.sample_support.model_dump() if p.sample_support else None,
            "validation_results": [
                {
                    "validation_type": vr.validation_type,
                    "status": vr.status,
                    "metrics": _compact_value(vr.metrics),
                    "interpretation": vr.interpretation,
                    "limitations": vr.limitations,
                    "supporting_evidence_ids": vr.supporting_evidence_ids,
                }
                for vr in p.validation_results
            ],
            "scientific_score": p.scientific_score.model_dump() if p.scientific_score else None,
        })
    return summary


def _summarize_mechanisms(mechanisms: List[Any], limit: int) -> List[Dict[str, Any]]:
    summary = []
    for m in (mechanisms or [])[:limit]:
        summary.append({
            "mechanism_id": m.mechanism_id,
            "mechanism_family": m.mechanism_family,
            "mechanism_statement": m.mechanism_statement,
            "source_pattern_ids": m.source_pattern_ids,
            "material_variables": m.material_variables,
            "descriptor_variables": m.descriptor_variables,
            "causal_chain": m.causal_chain,
            "applicable_material_scope": m.applicable_material_scope,
            "excluded_or_weak_scope": m.excluded_or_weak_scope,
            "grounding_level": m.grounding_level,
            "confidence_score": m.confidence_score,
            "confidence_label": m.confidence_label,
            "supporting_evidence_ids": m.supporting_evidence_ids,
            "supporting_pattern_validation": m.supporting_pattern_validation,
            "counterexamples": m.counterexamples,
            "limitations": m.limitations,
            "validation_suggestions": m.validation_suggestions,
        })
    return summary


def _summarize_boundaries(boundaries: List[Any], limit: int) -> List[Dict[str, Any]]:
    return [
        {
            "boundary_id": b.boundary_id,
            "description": b.description,
            "feature_conditions": b.feature_conditions,
            "error_ratio": b.error_ratio,
            "supporting_evidence_ids": b.supporting_evidence_ids,
            "severity": b.severity,
        }
        for b in (boundaries or [])[:limit]
    ]


def _summarize_anomalies(anomalies: List[Any], limit: int) -> List[Dict[str, Any]]:
    return [
        {
            "pattern_id": a.pattern_id,
            "description": a.description,
            "sample_count": a.sample_count,
            "feature_signature": _compact_value(a.feature_signature),
            "supporting_evidence_ids": a.supporting_evidence_ids,
        }
        for a in (anomalies or [])[:limit]
    ]


def _compact_value(value: Any, max_items: int = 12) -> Any:
    if isinstance(value, dict):
        compact = {}
        for i, (key, val) in enumerate(value.items()):
            if i >= max_items:
                compact["__truncated__"] = True
                break
            compact[key] = _compact_value(val, max_items=max_items)
        return compact
    if isinstance(value, list):
        return [_compact_value(v, max_items=max_items) for v in value[:max_items]]
    return value

