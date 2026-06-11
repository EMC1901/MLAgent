import json
import logging

logger = logging.getLogger(__name__)

REVIEW_DIMENSIONS = [
    "model_task_compatibility",
    "baseline_coverage",
    "hpo_budget_reasonableness",
    "validation_strategy_suitability",
    "metric_consistency",
    "overfitting_risk",
    "resource_cost_risk",
    "reproducibility_readiness",
]


def build_llm_review_prompt(
    context: dict, pipeline_specs: list, trial_plan, validation_result,
    iteration_guidance: dict = None,
) -> dict:
    specs = [s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs]
    tp = trial_plan if isinstance(trial_plan, dict) else trial_plan.model_dump() if trial_plan else {}

    model_summary = []
    for s in specs:
        model_summary.append({
            "model_id": s.get("model_id"),
            "role": s.get("pipeline_role"),
            "hpo_enabled": s.get("hpo_enabled"),
            "priority": s.get("priority"),
        })

    system_prompt = (
        "You are an ADVISORY reviewer for a generated machine learning pipeline specification. "
        "The system validator has ALREADY checked structural validity, registry validity, artifact "
        "availability, and safety constraints. These checks PASSED.\n\n"
        "Your role is NOT to approve, reject, modify, or execute the pipeline.\n"
        "Your role is ONLY to identify non-blocking machine learning practice risks and future "
        "improvement suggestions.\n\n"
        "RULES:\n"
        "- Do NOT output executable code (no Python, no sklearn, no import statements).\n"
        "- Do NOT modify pipeline specifications.\n"
        "- Do NOT invent new models or HPO methods.\n"
        "- Do NOT output approval_status, approved, rejected, conditional, or needs_improvement.\n"
        "- If no blocking issue is found, set execution_impact to \"non_blocking\".\n"
        "- Only output valid JSON. No markdown, no code fences.\n\n"
        "OUTPUT SCHEMA (strict):\n"
        "{\n"
        '  "review_status": "advisory_completed",\n'
        '  "execution_impact": "non_blocking",\n'
        '  "risk_level": "none|low|medium|high",\n'
        '  "checklist": [\n'
        '    {"dimension": "<name>", "status": "pass|warning|not_applicable", "comment": "<brief>"}\n'
        '  ],\n'
        '  "blocking_issues": [],\n'
        '  "non_blocking_risks": [\n'
        '    {"category": "<topic>", "severity": "low|medium|high", "message": "<text>", "suggested_action": "<text>"}\n'
        '  ],\n'
        '  "resource_warnings": [],\n'
        '  "future_improvement_suggestions": [],\n'
        '  "confidence_level": "low|medium|high"\n'
        "}\n\n"
        "REVIEW DIMENSIONS for checklist: " + ", ".join(REVIEW_DIMENSIONS)
    )

    user_message = json.dumps({
        "context": {
            "task_type": context.get("task_type"),
            "n_samples": context.get("n_samples"),
            "n_features": context.get("n_features"),
            "primary_metric": context.get("primary_metric"),
            "iteration_guidance": iteration_guidance,
        },
        "pipeline_summary": {
            "candidate_models": model_summary,
            "total_pipeline_specs": len(specs),
            "hpo_enabled": tp.get("hpo_enabled"),
            "search_method": tp.get("search_method"),
            "max_total_trials": tp.get("max_total_trials"),
            "validation_strategy": context.get("validation_plan", {}).get("split_strategy"),
            "evaluation_metric": context.get("evaluation_plan", {}).get("primary_metric"),
        },
        "system_validation_passed": validation_result.is_valid if validation_result else False,
        "instruction": (
            "Review the pipeline using the " + str(len(REVIEW_DIMENSIONS)) + " dimensions listed. "
            "Provide a checklist entry for each applicable dimension. "
            "Only report blocking_issues if you find a critical ML practice error "
            "(e.g. classification metric used for regression). Even then, execution_impact "
            "must remain non_blocking because system validator is authoritative. "
            "Set confidence_level based on how much information you have to judge."
        ),
    }, indent=2)

    return {"system_prompt": system_prompt, "user_message": user_message}
