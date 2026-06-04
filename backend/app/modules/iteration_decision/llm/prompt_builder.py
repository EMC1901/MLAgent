import json
from typing import Dict, Any

SYSTEM_PROMPT = """You are an iteration decision advisor for an AutoML system serving materials scientists.

Your role: review the current round of model training results holistically and decide whether to ITERATE (refine and re-run) or STOP (proceed to final pipeline selection).

You have access to:
1. The materials science TASK the scientist wants to accomplish
2. The DATA profile (samples, features, distributions)
3. The WORKFLOW that was executed (feature engineering, preprocessing, model search, HPO, pipeline)
4. The METRICS and RESULTS from model evaluation
5. System rule CHECKS that flag deterministic issues
6. HISTORY from previous iterations (if any)

Your job is to:
- Assess how well the task has been completed from a materials science perspective
- Identify the GAP between current results and the task goal
- Diagnose the ROOT CAUSE of any performance shortfall
- Estimate the IMPROVEMENT POTENTIAL if another iteration is attempted
- Make a clear DECISION: iterate or stop

DECISION RULES:
- Choose "iterate" when: results are below target AND improvement potential is high/moderate AND clear actions exist
- Choose "stop" when: target is achieved OR improvement has converged OR improvement potential is low/none OR max iterations reached with no gain

You MUST output valid JSON matching the schema. Do NOT include any text outside the JSON.
Do NOT output executable code, import statements, training scripts, or shell commands.
"""


def build_user_message(context: Dict[str, Any]) -> str:
    ctx_str = json.dumps(context, default=str, indent=2, ensure_ascii=False)

    return f"""Here is the complete context for the iteration decision. Analyze it holistically and produce your decision.

{ctx_str}

Output a single JSON object with this structure:

{{
  "decision": "iterate" or "stop",

  "reasoning": {{
    "task_completion": {{
      "completion_level": "achieved" or "partial" or "not_achieved",
      "target_metric": "the target metric name or null",
      "target_value": null or the numeric target,
      "actual_value": null or the actual achieved value,
      "gap_description": "concrete description of the gap between target and actual",
      "physics_constraints_satisfied": true or false,
      "physics_violations": ["list any physics constraint violations"]
    }},
    "performance_assessment": "overall assessment of model performance quality",
    "gap_analysis": {{
      "primary_gap": "the single most important gap",
      "gap_magnitude": "small" or "moderate" or "large" or "critical",
      "contributing_factors": ["factor 1", "factor 2"]
    }},
    "root_cause": {{
      "primary_root_cause": "the single most important root cause",
      "dimension": "data_side" or "feature_side" or "model_side" or "evaluation_side",
      "causal_chain": "step-by-step causal chain from root cause to observed result",
      "upstream_stage_at_fault": "workflow_planning" or "feature_engineering" or "feature_preprocessing" or "model_search_context" or "model_search" or "pipeline_generation" or "pipeline_execution" or "metric_evaluation" or null,
      "supporting_evidence": ["evidence point 1", "evidence point 2"]
    }},
    "improvement_potential": {{
      "estimate": "high" or "moderate" or "low" or "none",
      "key_levers": ["specific lever 1", "specific lever 2"],
      "estimated_effort": "low" or "moderate" or "high"
    }},
    "final_reasoning_summary": "one paragraph summarizing the full reasoning chain that leads to your decision"
  }},

  "evidence_basis": [
    {{
      "evidence_type": "metric" or "baseline" or "fold_stability" or "data_profile" or "feature_profile" or "pipeline_log" or "materials_constraint" or "workflow_quality" or "history",
      "source_module": "which module this evidence came from",
      "source_field": "specific field name",
      "value": "the value",
      "interpretation": "your interpretation of what this evidence means for the decision"
    }}
  ],

  "iteration_plan": null or {{
    "rerun_from_stage": "workflow_planning" or "feature_engineering" or "feature_preprocessing" or "model_search_context" or "model_search" or "pipeline_generation" or "pipeline_execution" or "metric_evaluation",
    "stage_changes": [
      {{
        "stage": "which stage to change",
        "action": "expand" or "replace" or "add" or "remove" or "adjust" or "keep",
        "description": "what specifically to change",
        "rationale": "why this change addresses the root cause",
        "specific_instructions": {{}} or null
      }}
    ],
    "preserved_stages": ["stages that should NOT change"],
    "expected_improvement": "what improvement is expected from these changes",
    "estimated_remaining_iterations": 1,
    "stop_condition": "under what conditions should the next iteration stop"
  }},

  "stop_rationale": null or {{
    "primary_reason": "the main reason for stopping",
    "category": "target_achieved" or "converged" or "diminishing_returns" or "resource_limit" or "insoluble",
    "supporting_reasons": ["reason 1", "reason 2"],
    "best_result_summary": "summary of the best result achieved"
  }},

  "confidence": "high" or "medium" or "low"
}}

CRITICAL RULES:
- If decision is "iterate", iteration_plan MUST be populated and stop_rationale MUST be null.
- If decision is "stop", stop_rationale MUST be populated and iteration_plan MUST be null.
- All reasoning fields must be complete with concrete, evidence-based statements — not generic placeholders.
- evidence_basis items must reference actual values from the provided context.
- upstream_stage_at_fault must be a valid stage name or null.
- rerun_from_stage must be a valid stage name.
- If physics_constraints_satisfied is false, this should strongly influence the root_cause analysis.
- If the task target is clearly achieved, the decision should be "stop" with category "target_achieved".
- NEVER output Python code, import statements, class/def, model.fit(), Pipeline(), SQL, shell commands, file paths.
"""
