"""
LLM-guided Feature Preprocessing Planner.

Builds a structured PreprocessingPlan using the Feature Preprocessing Capability Registry
and the FeaturePreprocessingDecisionInput from Feature Engineering.
"""
import json
import logging
from typing import Tuple, Dict, Any

from app.shared.registry.fp_capability_registry import (
    get_available_fp_capabilities,
    get_registry_snapshot_fp,
    CAPABILITY_GROUPS,
)

logger = logging.getLogger(__name__)


PREPROCESSING_PLAN_SCHEMA = {
    "type": "object",
    "required": [
        "plan_version", "global_policy", "capability_groups_used",
        "column_policies", "feature_group_policies", "operation_sequence",
        "rejected_operations", "warnings_for_downstream",
    ],
    "properties": {
        "plan_version": {"type": "string", "const": "1.0.0"},
        "global_policy": {
            "type": "object",
            "required": ["leakage_prevention", "variant_strategy"],
            "properties": {
                "leakage_prevention": {
                    "type": "object",
                    "required": ["fit_transform_scope", "target_column_excluded", "id_columns_excluded", "target_aware_selection_allowed", "rationale"],
                    "properties": {
                        "fit_transform_scope": {"type": "string", "enum": ["train_fold_only"]},
                        "target_column_excluded": {"type": "boolean"},
                        "id_columns_excluded": {"type": "boolean"},
                        "target_aware_selection_allowed": {"type": "boolean"},
                        "rationale": {"type": "string"},
                    },
                },
                "variant_strategy": {
                    "type": "object",
                    "required": ["mode", "rationale"],
                    "properties": {
                        "mode": {"type": "string", "enum": ["single", "model_family_specific", "multiple_variants"]},
                        "rationale": {"type": "string"},
                    },
                },
            },
        },
        "capability_groups_used": {"type": "array", "items": {"type": "string"}},
        "column_policies": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["column_name", "action", "reason", "evidence", "risk"],
                "properties": {
                    "column_name": {"type": "string"},
                    "action": {"type": "string", "enum": ["keep", "drop", "transform", "flag_for_review"]},
                    "reason": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                    "risk": {"type": "string"},
                },
            },
        },
        "feature_group_policies": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["feature_group", "policy", "operations"],
                "properties": {
                    "feature_group": {"type": "string"},
                    "policy": {"type": "string", "enum": ["preserve", "filter", "transform", "reduce_dimension", "drop", "flag_for_review"]},
                    "operations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["operation_id", "capability_id", "parameters", "execution_scope", "decision_rationale"],
                            "properties": {
                                "operation_id": {"type": "string"},
                                "capability_id": {"type": "string"},
                                "parameters": {"type": "object"},
                                "execution_scope": {"type": "string", "enum": ["dataset_profile_only", "train_only", "fold_only"]},
                                "decision_rationale": {
                                    "type": "object",
                                    "required": ["reason", "evidence", "expected_benefit", "risk", "fallback"],
                                    "properties": {
                                        "reason": {"type": "string"},
                                        "evidence": {"type": "array", "items": {"type": "string"}},
                                        "expected_benefit": {"type": "string"},
                                        "risk": {"type": "string"},
                                        "fallback": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        },
        "operation_sequence": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["step_order", "operation_id", "capability_id", "target_feature_groups", "parameters", "execution_scope", "decision_rationale"],
                "properties": {
                    "step_order": {"type": "integer", "minimum": 1},
                    "operation_id": {"type": "string"},
                    "capability_id": {"type": "string"},
                    "target_feature_groups": {"type": "array", "items": {"type": "string"}},
                    "target_columns": {"type": "array", "items": {"type": "string"}},
                    "parameters": {"type": "object"},
                    "execution_scope": {"type": "string", "enum": ["dataset_profile_only", "train_only", "fold_only"]},
                    "decision_rationale": {
                        "type": "object",
                        "required": ["reason", "evidence", "expected_benefit", "risk", "fallback"],
                        "properties": {
                            "reason": {"type": "string"},
                            "evidence": {"type": "array", "items": {"type": "string"}},
                            "expected_benefit": {"type": "string"},
                            "risk": {"type": "string"},
                            "fallback": {"type": "string"},
                        },
                    },
                },
            },
        },
        "model_family_specific_notes": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["model_family", "preprocessing_needs", "rationale"],
                "properties": {
                    "model_family": {"type": "string"},
                    "preprocessing_needs": {"type": "array", "items": {"type": "string"}},
                    "rationale": {"type": "string"},
                },
            },
        },
        "rejected_operations": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["capability_id", "reason", "evidence"],
                "properties": {
                    "capability_id": {"type": "string"},
                    "reason": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "warnings_for_downstream": {"type": "array", "items": {"type": "string"}},
    },
}


SYSTEM_PROMPT = """You are an expert feature preprocessing planner for materials science machine learning.
Your task is to generate a structured, executable PreprocessingPlan based on:
1. FeaturePreprocessingDecisionInput (real feature matrix data from Feature Engineering)
2. Feature Preprocessing Capability Registry (available preprocessing operations)
3. WorkflowPlan.preprocessing_intent (high-level goals, reference only)

**CRITICAL RULES:**

1. You MUST ONLY select capability_id values from the provided Feature Preprocessing Capability Registry.
2. Only capabilities with status="available" may be used in operations.
3. You MUST NOT invent capability_ids or preprocessing operations.
4. You MUST NOT generate Python code, SQL, or any executable code.
5. Every operation MUST have a complete decision_rationale with: reason, evidence, expected_benefit, risk, fallback.
6. Each operation's execution_scope MUST match the capability's declared fit_scope (no looser scope allowed).
7. Target-aware selection MUST be disabled by default (target_aware_selection_allowed=false).
8. Target column MUST be excluded from feature matrix (scope per capability's fit_scope).
9. ID columns MUST be excluded or flagged.
10. You MUST NOT fit any transformer on full data for CV evaluation.
11. Feature lineage MUST be traceable through all operations.
12. Rejected operations MUST have a reason and evidence.

**Operational Sequence Order (enforce this order):**
1. Leakage detection & target/ID exclusion
2. Missingness analysis
3. Low information filtering
4. Missing value imputation
5. Distribution transformation (skewness)
6. Scaling/normalization
7. Correlation/collinearity handling
8. Feature selection
9. Feature group policies
10. Dimensionality reduction
11. Interpretability preservation
12. Artifact tracking

**Decision Guidelines:**
- For missing values: prefer median imputation for skewed features, mean for symmetric.
- For scaling: use standard_scaler for linear models, no_scaling for tree models, robust_scaler for descriptor-heavy data.
- For correlation: use 0.95 as default Pearson threshold; prefer keeping interpretable features.
- For feature selection: prefer unsupervised methods unless target-aware is explicitly safe.
- For dimensionality reduction: only recommend when n_features >> n_samples and interpretability impact is acceptable.
- For materials science: protect composition and structure feature groups for interpretability.

**FIELD VALUE DISAMBIGUATION — Do NOT confuse these similar fields:**

- `column_policies[*].action`:  keep | drop | transform | flag_for_review  (individual column actions)
- `feature_group_policies[*].policy`:  preserve | filter | transform | reduce_dimension | drop | flag_for_review  (group-level policies)

These two fields look similar but have DIFFERENT allowed values. `action` uses "keep"/"drop" for single columns. `policy` uses "preserve"/"filter"/"reduce_dimension"/"drop" for whole feature groups. Never use column-level action values in group-level policy fields.

**Output Format:**
You MUST output ONLY a valid JSON object matching the exact schema provided. No markdown, no code blocks, no other text."""


def build_preprocessing_plan_prompt(
    decision_input: Dict[str, Any],
    preprocessing_intent: Dict[str, Any] = None,
) -> Tuple[str, str]:
    """Build the system prompt and user message for PreprocessingPlan generation."""

    # Get available FP capabilities
    available_caps = get_available_fp_capabilities()
    caps_for_prompt = [
        {
            "capability_id": c.capability_id,
            "display_name": c.display_name,
            "capability_group": c.capability_group,
            "operation_type": c.operation_type,
            "supported_feature_types": c.supported_feature_types,
            "requires_target": c.requires_target,
            "fit_scope": c.fit_scope,
            "allowed_pipeline_positions": c.allowed_pipeline_positions,
            "parameters_schema": c.parameters_schema,
            "default_parameters": c.default_parameters,
            "risk_notes": c.risk_notes,
            "fallback_capability_ids": c.fallback_capability_ids,
        }
        for c in available_caps
    ]

    # Capability groups summary
    capability_groups_summary = {
        k: len([c for c in available_caps if c.capability_group == k])
        for k in CAPABILITY_GROUPS
    }

    # Registry snapshot
    snapshot = get_registry_snapshot_fp()

    user_message_parts = [
        "## Feature Preprocessing Decision Input",
        json.dumps(decision_input, indent=2, ensure_ascii=False),
        "",
        "## Preprocessing Intent (Reference Only)",
        json.dumps(preprocessing_intent or {}, indent=2, ensure_ascii=False),
        "",
        "## Feature Preprocessing Capability Registry",
        f"### Available Capabilities by Group: {json.dumps(capability_groups_summary)}",
        f"### Total Available: {snapshot['available_count']}",
        "### Full Available Capabilities List",
        json.dumps(caps_for_prompt, indent=2, ensure_ascii=False),
        "",
        "## Capability Groups",
        json.dumps(CAPABILITY_GROUPS, indent=2, ensure_ascii=False),
        "",
        "## Output JSON Schema",
        "You MUST output a single JSON object strictly following this schema:",
        json.dumps(PREPROCESSING_PLAN_SCHEMA, indent=2),
        "",
        "REMEMBER:",
        "1. Output ONLY the JSON object. No markdown, no code blocks.",
        "2. Use ONLY capability_id from the Capability Registry.",
        "3. Every operation MUST have complete decision_rationale.",
        "4. fit_scope MUST be fold_only for all fit-type operations.",
        "5. Target-aware selection is disabled by default.",
        "6. Follow the operational sequence order.",
    ]

    user_message = "\n".join(user_message_parts)
    return SYSTEM_PROMPT, user_message
