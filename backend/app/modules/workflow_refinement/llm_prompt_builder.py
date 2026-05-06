import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an LLM-driven workflow refinement decision maker for an AutoML system in materials science.

Your task is to decide whether the system should proceed to Final Pipeline Selection or iterate by generating a revised WorkflowPlanResponse.

You must base your decision on the provided diagnosis, metrics, pipeline logs, workflow records, and experiment history.

If you choose iteration, you must output a revised WorkflowPlanResponse and detailed reasons for each changed section.

You are not allowed to output executable code.
You are not allowed to directly train models.
You are not allowed to modify registries.
You are not allowed to create Python scripts.
You are not allowed to bypass system validators.

You must answer:
1. Can the system proceed to Final Pipeline Selection now?
2. If yes, why?
3. If no, what are the main blockers?
4. Should a revised WorkflowPlanResponse be generated?
5. Which workflow sections need to change?
6. Which workflow sections should stay the same?
7. Which module should the system re-enter from?
8. Which artifacts can be reused?
9. Which artifacts must be regenerated?
10. What should the next iteration try to solve?
11. If the next iteration does not improve, should we stop?

You MUST output valid JSON matching the schema provided. Do NOT include any text outside the JSON."""


def build_user_message(context: Dict[str, Any]) -> str:
    """Build the user message with the full refinement context."""
    context_str = json.dumps(context, default=str, indent=2)
    return f"""Here is the full workflow refinement context. Analyze it and produce your decision.

{context_str}

Output your response as a single JSON object with this structure:

{{
  "workflow_refinement_decision": {{
    "decision": "proceed_next_stage" or "iterate_refinement",
    "decision_confidence_level": "low" or "medium" or "high",
    "primary_reason": "concise primary reason for the decision",
    "should_generate_revised_workflow_plan": true or false,
    "recommended_rerun_from_stage": "workflow_planning" or "feature_engineering" or "feature_preprocessing" or "model_search_context" or "model_search" or "pipeline_generation" or "pipeline_execution" or "metric_evaluation" or "final_pipeline_selection" or null,
    "should_proceed_to_final_selection": true or false
  }},
  "decision_reasoning": {{
    "performance_assessment": "...",
    "baseline_assessment": "...",
    "stability_assessment": "...",
    "diagnosis_assessment": "...",
    "cost_assessment": "...",
    "risk_assessment": "...",
    "final_reasoning_summary": "..."
  }},
  "evidence_used": [
    {{
      "source_module": "metric_evaluation" or "result_diagnosis" or "pipeline_execution" or "dataset_profile",
      "evidence_type": "metric" or "baseline" or "stability" or "diagnosis" or "runtime" or "feature",
      "source_field": "the specific field name",
      "value": "the value",
      "interpretation": "your interpretation of this evidence",
      "supports_decision": "proceed_next_stage" or "iterate_refinement"
    }}
  ],
  "revised_workflow_plan": null or {{
    "status": "planned_by_refinement",
    "planning_mode": "llm_refinement",
    "task_summary": {{}},
    "data_strategy": {{}},
    "feature_strategy": {{}},
    "model_strategy": {{}},
    "validation_strategy": {{}},
    "evaluation_strategy": {{}},
    "hpo_strategy": {{}},
    "interpretability_strategy": {{}},
    "pipeline_generation_input": {{}},
    "planning_warnings": [],
    "planning_assumptions": [],
    "llm_reasoning_summary": "",
    "confidence_score": 0.0,
    "refinement_metadata": {{
      "changed_sections": [],
      "preserved_sections": [],
      "recommended_rerun_from_stage": "workflow_planning"
    }}
  }},
  "iteration_rerun_plan": null or {{
    "next_iteration_index": 0,
    "recommended_rerun_from_stage": "workflow_planning",
    "rerun_stages": [],
    "reuse_artifacts": [],
    "invalidate_artifacts": [],
    "expected_improvement_targets": [],
    "minimum_improvement_threshold": null,
    "stop_after_next_iteration_if_no_gain": true,
    "reasoning": ""
  }},
  "final_pipeline_selection_input": null or {{
    "candidate_metric_evaluation_ids": [],
    "candidate_pipeline_execution_ids": [],
    "best_metric_evaluation_id": null,
    "current_best_model_id": null,
    "current_best_trial_id": null,
    "current_best_pipeline_spec_id": null,
    "selection_policy": {{}},
    "constraints": {{}},
    "ready_for_final_pipeline_selection": true
  }},
  "confidence_level": "low" or "medium" or "high"
}}

CRITICAL RULES:
- If decision is "proceed_next_stage", revised_workflow_plan and iteration_rerun_plan MUST be null, and final_pipeline_selection_input MUST be populated.
- If decision is "iterate_refinement", revised_workflow_plan and iteration_rerun_plan MUST be populated, and final_pipeline_selection_input MUST be null.
- NEVER output Python code, import statements, class/def definitions, model.fit(), Pipeline(), SQL, shell commands, or any executable code.
- All strategy objects in revised_workflow_plan must be objects with proper fields (not strings, not code blocks).
- Evidence used must come from the provided context data — do not fabricate evidence.
- confidence_score must be a float between 0.0 and 1.0.
- reuse_artifacts and invalidate_artifacts MUST be arrays of plain strings, NOT arrays of objects. Example: ["feature_matrix", "raw_dataset"]
- expected_improvement_targets MUST be an array of plain strings. Example: ["reduce fold variance", "improve baseline improvement"]
- minimum_improvement_threshold MUST be a plain float number or null. Example: 0.03
- rerun_stages MUST be an array of plain strings matching the allowed stage names.
"""


def build_llm_prompt(context: Dict[str, Any]) -> Dict[str, Any]:
    """Build the full LLM prompt (system + user) for workflow refinement."""
    return {
        "system_prompt": SYSTEM_PROMPT,
        "user_message": build_user_message(context),
    }
