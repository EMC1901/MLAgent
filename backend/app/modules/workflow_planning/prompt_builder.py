import json
from typing import Tuple
from app.shared.registry.featurizer_registry import get_available_featurizers, get_planned_featurizers
from app.shared.registry.fe_capability_registry import (
    get_available_fe_capabilities,
    get_all_fe_capabilities,
    get_registry_snapshot,
)


OUTPUT_JSON_SCHEMA = {
    "type": "object",
    "required": [
        "task_summary",
        "data_strategy",
        "feature_strategy",
        "preprocessing_intent",
        "model_strategy",
        "validation_strategy",
        "evaluation_strategy",
        "hpo_strategy",
        "interpretability_strategy",
        "pipeline_generation_input",
        "workflow_rationale",
        "planning_warnings",
        "planning_assumptions",
        "llm_reasoning_summary",
        "confidence_score",
    ],
    "properties": {
        "task_summary": {
            "type": "object",
            "required": ["task_type", "input_modality", "prediction_target", "material_domain", "primary_goal"],
            "properties": {
                "task_type": {"type": "string", "enum": ["regression", "classification", "ranking"]},
                "input_modality": {"type": "string", "enum": ["composition", "structure", "descriptor", "text", "mixed"]},
                "prediction_target": {"type": "string"},
                "material_domain": {"type": "string"},
                "primary_goal": {"type": "string"},
            },
        },
        "data_strategy": {
            "type": "object",
            "required": ["input_columns", "target_column", "required_cleaning_steps", "target_handling", "duplicate_handling", "missing_value_strategy"],
            "properties": {
                "input_columns": {"type": "array", "items": {"type": "string"}},
                "target_column": {"type": "string"},
                "required_cleaning_steps": {"type": "array", "items": {"type": "string"}},
                "target_handling": {
                    "type": "object",
                    "properties": {
                        "requires_transformation_check": {"type": "boolean"},
                        "recommended_transformation": {"type": "string"},
                    },
                },
                "duplicate_handling": {"type": "string"},
                "missing_value_strategy": {"type": "string"},
            },
        },
        "feature_strategy": {
            "type": "object",
            "required": ["feature_type", "executable_featurizers", "selected_feature_actions", "rejected_feature_actions"],
            "properties": {
                "feature_type": {"type": "string"},
                "executable_featurizers": {"type": "array", "items": {"type": "string"}},
                "semantic_featurizers": {"type": "array", "items": {"type": "string"}},
                "unsupported_future_featurizers": {"type": "array", "items": {"type": "string"}},
                "recommended_featurizers": {"type": "array", "items": {"type": "string"}},
                "requires_structure_features": {"type": "boolean"},
                "feature_selection_required": {"type": "boolean"},
                "feature_scaling_required": {"type": "boolean"},
                "strategy_id": {"type": "string"},
                "strategy_version": {"type": "string"},
                "input_modality_assessment": {
                    "type": "object",
                    "properties": {
                        "detected_modalities": {"type": "array", "items": {"type": "string"}},
                        "usable_modalities": {"type": "array", "items": {"type": "string"}},
                        "unusable_modalities": {"type": "array", "items": {"type": "string"}},
                        "rationale": {"type": "string"},
                    },
                },
                "selected_feature_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["action_id", "capability_id", "priority", "decision_rationale"],
                        "properties": {
                            "action_id": {"type": "string"},
                            "capability_id": {"type": "string", "description": "Must match a capability_id from the FE Capability Registry with status=available"},
                            "priority": {"type": "string", "enum": ["required", "recommended", "optional", "fallback"]},
                            "input_columns": {"type": "array", "items": {"type": "string"}},
                            "parameters": {"type": "object"},
                            "output_feature_group": {"type": "string"},
                            "decision_rationale": {
                                "type": "object",
                                "required": ["reason", "evidence", "material_science_basis", "expected_benefit", "risk", "fallback"],
                                "properties": {
                                    "reason": {"type": "string"},
                                    "evidence": {"type": "array", "items": {"type": "string"}},
                                    "material_science_basis": {"type": "string"},
                                    "expected_benefit": {"type": "string"},
                                    "risk": {"type": "string"},
                                    "fallback": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "rejected_feature_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "capability_id": {"type": "string"},
                            "reason": {"type": "string"},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
                "fallback_strategy": {
                    "type": "object",
                    "properties": {
                        "fallback_actions": {"type": "array", "items": {"type": "string"}},
                        "trigger_conditions": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "feature_group_expectations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "feature_group": {"type": "string"},
                            "expected_signal": {"type": "string"},
                            "known_limitations": {"type": "string"},
                        },
                    },
                },
            },
        },
        "preprocessing_intent": {
            "type": "object",
            "required": ["high_level_goals"],
            "properties": {
                "intent_id": {"type": "string"},
                "high_level_goals": {"type": "array", "items": {"type": "string"}},
                "risks_to_check_after_feature_engineering": {"type": "array", "items": {"type": "string"}},
                "non_final_notes": {
                    "type": "string",
                    "const": "Final executable preprocessing decisions will be made by Feature Preprocessing after Feature Engineering output is available.",
                },
            },
        },
        "model_strategy": {
            "type": "object",
            "required": [
                "candidate_model_families",
                "baseline_models",
                "preferred_model_bias",
                "excluded_model_families",
                "selected_model_actions",
                "rejected_model_actions",
            ],
            "properties": {
                "candidate_model_families": {"type": "array", "items": {"type": "string"}},
                "baseline_models": {"type": "array", "minItems": 1, "maxItems": 1, "items": {"type": "string"}, "description": "EXACTLY ONE model family to serve as the comparative baseline. Must be a simple, fast, well-understood model."},
                "preferred_model_bias": {"type": "string"},
                "excluded_model_families": {"type": "array", "items": {"type": "string"}},
                "model_selection_rationale_summary": {"type": "string"},
                "selected_model_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["action_id", "model_family", "priority", "decision_rationale"],
                        "properties": {
                            "action_id": {"type": "string"},
                            "model_family": {"type": "string"},
                            "priority": {"type": "string", "enum": ["required", "recommended", "optional", "fallback"]},
                            "decision_rationale": {
                                "type": "object",
                                "required": ["reason", "evidence", "expected_performance", "risk", "fallback"],
                                "properties": {
                                    "reason": {"type": "string"},
                                    "evidence": {"type": "array", "items": {"type": "string"}},
                                    "expected_performance": {"type": "string"},
                                    "risk": {"type": "string"},
                                    "fallback": {"type": "string"},
                                },
                            },
                        },
                    },
                },
                "rejected_model_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "model_family": {"type": "string"},
                            "reason": {"type": "string"},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        },
        "validation_strategy": {
            "type": "object",
            "required": ["split_strategy", "n_splits", "random_state", "stratification_required"],
            "properties": {
                "split_strategy": {"type": "string", "enum": ["train_test_split", "k_fold_cross_validation", "stratified_k_fold", "repeated_cv"]},
                "n_splits": {"type": "integer", "minimum": 2, "maximum": 10},
                "test_size": {"type": ["number", "null"]},
                "random_state": {"type": "integer"},
                "stratification_required": {"type": "boolean"},
            },
        },
        "evaluation_strategy": {
            "type": "object",
            "required": ["primary_metric", "secondary_metrics", "metric_direction"],
            "properties": {
                "primary_metric": {"type": "string"},
                "secondary_metrics": {"type": "array", "items": {"type": "string"}},
                "metric_direction": {"type": "string", "enum": ["minimize", "maximize"]},
            },
        },
        "hpo_strategy": {
            "type": "object",
            "required": ["enabled", "search_method", "budget_level", "max_trials"],
            "properties": {
                "enabled": {"type": "boolean"},
                "search_method": {"type": "string", "enum": ["grid_search", "random_search", "bayesian_optimization", "optuna_tpe", "successive_halving"]},
                "budget_level": {"type": "string", "enum": ["low", "medium", "high"]},
                "max_trials": {"type": "integer", "minimum": 1},
            },
        },
        "interpretability_strategy": {
            "type": "object",
            "required": ["enabled", "methods", "priority"],
            "properties": {
                "enabled": {"type": "boolean"},
                "methods": {"type": "array", "items": {"type": "string"}},
                "priority": {"type": "string"},
            },
        },
        "pipeline_generation_input": {
            "type": "object",
            "required": ["pipeline_steps", "required_components"],
            "properties": {
                "pipeline_steps": {"type": "array", "items": {"type": "string"}},
                "required_components": {
                    "type": "object",
                    "properties": {
                        "data_cleaner": {"type": "boolean"},
                        "featurizer": {"type": "boolean"},
                        "model_trainer": {"type": "boolean"},
                        "evaluator": {"type": "boolean"},
                    },
                },
            },
        },
        "workflow_rationale": {
            "type": "object",
            "properties": {
                "overall_reasoning_summary": {"type": "string"},
                "key_assumptions": {"type": "array", "items": {"type": "string"}},
                "known_risks": {"type": "array", "items": {"type": "string"}},
            },
        },
        "planning_warnings": {"type": "array", "items": {"type": "string"}},
        "planning_assumptions": {"type": "array", "items": {"type": "string"}},
        "llm_reasoning_summary": {"type": "string"},
        "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}


SYSTEM_PROMPT = """You are an expert AutoML workflow planner for materials science. Your task is to generate a COMPLETE structured machine learning workflow plan based on task specifications, task interpretation, dataset profiling results, and the Feature Engineering Capability Registry.

**CRITICAL: You MUST generate a COMPLETE WorkflowPlan.**
You must NOT only generate FeatureStrategy. FeatureStrategy is ONE section of the full WorkflowPlan.
The full WorkflowPlan must include: task_summary, data_strategy, feature_strategy, preprocessing_intent, model_strategy, hpo_strategy, evaluation_strategy, validation_strategy, pipeline_generation_input, workflow_rationale.

**CRITICAL BOUNDARY RULES — You MUST follow these:**

1. You ONLY plan the machine learning workflow. You do NOT execute anything.
2. You MUST NOT generate Python code, pseudocode, or any executable code.
3. You MUST NOT fabricate or predict model training results, metrics values, or evaluation scores.
4. You MUST NOT claim that models have been trained.
5. You MUST NOT load, clean, or transform any actual data.
6. You MUST NOT modify upstream task specification, interpretation, or dataset profile.
7. You MUST base all decisions on the data facts provided in the dataset profile.
8. If something is uncertain, put it in "planning_assumptions", not in the main plan.
9. If there are risks or limitations, put them in "planning_warnings".
10. You MUST output ONLY valid JSON matching the exact schema provided. No other text.

**Feature Engineering Capability Rules:**

- You MUST select capability_id values ONLY from the provided Feature Engineering Capability Registry.
- Only capabilities with status="available" may be used as selected_feature_actions.
- Each selected_feature_action MUST have a complete decision_rationale with: reason, evidence, material_science_basis, expected_benefit, risk, fallback.
- Rejected capabilities MUST have a reason explaining why they were rejected.
- "planned" capabilities CANNOT be used as required or recommended actions.
- You MUST NOT invent capability_ids that are not in the Registry.

**PreprocessingIntent Rules:**

- preprocessing_intent must ONLY contain high_level_goals (e.g., "handle_missing_values", "standardize_numeric_features").
- preprocessing_intent must NOT contain column-level operations or executable PreprocessingPlan.
- The actual PreprocessingPlan will be generated by the Feature Preprocessing module after Feature Engineering output is available.

**Featurizer Selection Rules:**

- You MUST select executable_featurizers ONLY from the available_featurizers list.
- Use exact featurizer "id" values — do NOT invent new IDs.
- Scientific/semantic concepts go into semantic_featurizers.
- Planned featurizers go into unsupported_future_featurizers.

**Model Selection Rules:**

- You MUST pick EXACTLY ONE model as the baseline_model. The baseline must be a simple, fast, well-established model (e.g. dummy_mean, linear_regression, ridge) that serves as the minimum-performance reference point. Do NOT select more than one baseline.
- You MUST provide detailed rationale for BOTH selected AND rejected models.
- Each selected_model_action MUST have a complete decision_rationale with: reason, evidence, expected_performance, risk, fallback.
- Each rejected model in rejected_model_actions MUST have a reason explaining why it was excluded for this specific task.
- Consider: sample size, feature dimensionality, expected noise level, interpretability requirements, and task type when making model decisions.
- For materials science tasks, prefer models that handle small-to-medium datasets well and offer interpretability.
- The candidate_model_families list should be a concise summary; the detailed justification goes into selected_model_actions and rejected_model_actions.

For materials science tasks:
- **composition** -> composition-based featurizers + descriptor fallback
- **structure** -> structure-based featurizers if available, descriptor fallback otherwise
- **descriptor** -> numeric descriptors with scaling and feature selection
- **regression** -> MAE/RMSE/R2 metrics, tree-based + linear models
- **classification** -> Accuracy/F1/ROC-AUC metrics, tree-based + linear models
- Small samples (n < 100) -> simple models, fewer CV folds, limited HPO
- Medium samples (100 <= n < 1000) -> moderate complexity
- Large samples (n >= 1000) -> complex models, more HPO budget"""


def build_prompt(context: dict) -> Tuple[str, str]:
    data_ctx = context.get("data_context") or {}
    input_modality = data_ctx.get("input_modality")
    task_type = (context.get("task_context") or {}).get("task_type")

    # Featurizers from legacy registry
    available_featurizers = get_available_featurizers(
        input_modality=input_modality,
        task_type=task_type,
    )
    planned_featurizers = get_planned_featurizers(input_modality=input_modality)

    available_for_prompt = [
        {
            "id": s.id,
            "display_name": s.display_name,
            "feature_type": s.feature_type,
            "input_modalities": s.input_modalities,
            "description": s.description,
            "estimated_feature_count": s.estimated_feature_count,
        }
        for s in available_featurizers
    ]

    planned_for_prompt = [
        {
            "id": s.id,
            "display_name": s.display_name,
            "description": s.description,
            "why_not_available": "Requires: " + ", ".join(s.requires_dependencies),
        }
        for s in planned_featurizers
    ]

    # FE Capability Registry for capability-aware FeatureStrategy
    fe_capabilities = get_available_fe_capabilities(
        input_modality=input_modality,
        task_type=task_type,
    )
    fe_caps_for_prompt = []
    for c in fe_capabilities:
        cap_dict = c.model_dump()
        if not c.featurizer_ids:
            cap_dict["_warning"] = (
                "This capability has NO mapped executable featurizer. "
                "Do NOT use it in selected_feature_actions."
            )
        fe_caps_for_prompt.append(cap_dict)

    # All capabilities (for rejection reference)
    all_fe_caps = get_available_fe_capabilities()
    all_fe_caps_for_prompt = [
        {
            "capability_id": c.capability_id,
            "display_name": c.display_name,
            "status": c.status,
            "feature_family": c.feature_family,
            "featurizer_ids": c.featurizer_ids,
        }
        for c in all_fe_caps
    ]

    # Planned capabilities (for awareness, NOT selectable)
    planned_fe_caps = get_all_fe_capabilities(status="planned")
    planned_fe_caps_for_prompt = [
        {
            "capability_id": c.capability_id,
            "display_name": c.display_name,
            "feature_family": c.feature_family,
            "why_not_available": (
                "No featurizer implementation yet"
                if not c.featurizer_ids
                else f"Mapped featurizers {c.featurizer_ids} are not yet available"
            ),
        }
        for c in planned_fe_caps
    ]

    # Registry snapshot
    registry_snapshot = get_registry_snapshot()

    user_message_parts = [
        "## Task Context",
        json.dumps(context.get("task_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Interpretation Context",
        json.dumps(context.get("interpretation_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Data Context",
        json.dumps(context.get("data_context", {}), indent=2, ensure_ascii=False),
        "",
        "## Feature Engineering Capability Registry",
        "### All Registered Capabilities (for reference)",
        json.dumps(all_fe_caps_for_prompt, indent=2, ensure_ascii=False),
        "",
        "### Available Capabilities for This Task",
        json.dumps(fe_caps_for_prompt, indent=2, ensure_ascii=False),
        "",
        "### Planned Capabilities (for awareness — do NOT use in selected_feature_actions)",
        json.dumps(planned_fe_caps_for_prompt, indent=2, ensure_ascii=False),
        "",
        "### Registry Snapshot Version",
        registry_snapshot["snapshot_version"],
        "",
        "## Available Featurizers (for executable_featurizers field)",
        json.dumps(available_for_prompt, indent=2, ensure_ascii=False),
        "",
        "## Planned / Future Featurizers (for unsupported_future_featurizers)",
        json.dumps(planned_for_prompt, indent=2, ensure_ascii=False),
        "",
        "## Output JSON Schema",
        "You MUST output a single JSON object that strictly follows this schema:",
        json.dumps(OUTPUT_JSON_SCHEMA, indent=2),
        "",
        "Remember:",
        "1. Output ONLY the JSON object. No markdown, no code blocks, no explanatory text.",
        "2. Generate a COMPLETE WorkflowPlan — not just FeatureStrategy.",
        "3. FeatureStrategy.selected_feature_actions must use capability_id from the FE Capability Registry.",
        "4. Each selected capability MUST have at least one mapped featurizer_id (check the featurizer_ids field).",
        "5. Capabilities with empty featurizer_ids or a _warning MUST NOT be used as 'required' or 'recommended'.",
        "6. Each selected feature action MUST have complete decision_rationale.",
        "7. Each selected model action MUST have complete decision_rationale (reason, evidence, expected_performance, risk, fallback).",
        "8. Each rejected model MUST have a reason explaining why it was excluded.",
        "9. preprocessing_intent must ONLY contain high-level goals.",
    ]

    user_message = "\n".join(user_message_parts)
    return SYSTEM_PROMPT, user_message
