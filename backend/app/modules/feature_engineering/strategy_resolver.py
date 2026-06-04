"""
Feature strategy resolver — consumes the Registry to determine which featurizers
to execute, with full alias resolution and backwards compatibility for old
workflow plans that use 'recommended_featurizers'.
"""
import logging
from app.shared.registry.featurizer_registry import (
    resolve,
    resolve_to_available,
    get_default_fallback,
    get_available_featurizers,
    resolve_featurizers_from_capability_actions,
)
from app.modules.feature_engineering.schemas import ResolvedFeatureStrategy

logger = logging.getLogger(__name__)


def resolve_feature_strategy(feature_context: dict, input_modality: str) -> ResolvedFeatureStrategy:
    """Resolve the feature strategy using the Featurizer Registry.

    Priority:
      0. feature_strategy.selected_feature_actions (capability-aware, resolved via mapping)
      1. feature_strategy.executable_featurizers
      2. feature_strategy.recommended_featurizers (legacy, resolved via Registry aliases)
      3. Registry fallback (highest-priority available featurizer for this modality)
    """
    feature_strategy = feature_context.get("feature_strategy") or {}

    feature_type = feature_strategy.get("feature_type")
    executable = feature_strategy.get("executable_featurizers")
    recommended = feature_strategy.get("recommended_featurizers")
    semantic = feature_strategy.get("semantic_featurizers", [])
    unsupported_future = feature_strategy.get("unsupported_future_featurizers", [])

    scaling_required = feature_strategy.get("feature_scaling_required", False)
    selection_required = feature_strategy.get("feature_selection_required", False)
    structure_required = feature_strategy.get("requires_structure_features", False)

    selected = []
    resolution_log = []
    warnings = []

    # ---- Priority 0: selected_feature_actions (capability-aware) ----
    capability_actions = feature_strategy.get("selected_feature_actions") or []
    capability_resolutions = []

    if isinstance(capability_actions, list) and len(capability_actions) > 0:
        capability_resolutions = resolve_featurizers_from_capability_actions(
            capability_actions, input_modality
        )
        for cr in capability_resolutions:
            if cr["status"] == "resolved" and cr["featurizer_id"] not in selected:
                selected.append(cr["featurizer_id"])
                resolution_log.append({
                    "input": cr["capability_id"],
                    "resolved_to": cr["featurizer_id"],
                    "matched_by": "capability_action",
                    "status": "available",
                    "action_id": cr["action_id"],
                })
            elif cr["status"] == "unavailable":
                warnings.append(
                    f"Capability '{cr['capability_id']}' (action '{cr['action_id']}') "
                    f"mapped to featurizer '{cr['featurizer_id']}' but it is not available "
                    f"(check dependencies)."
                )
            elif cr["status"] == "no_implementation":
                warnings.append(
                    f"Capability '{cr['capability_id']}' (action '{cr['action_id']}') "
                    f"has no executable featurizer implementation."
                )

    # ---- Priority 1: executable_featurizers ----
    if not selected:
        if executable is not None and isinstance(executable, list) and len(executable) > 0:
            for name in executable:
                result = resolve_to_available(name, input_modality)
                resolution_log.append({
                    "input": name,
                    "resolved_to": result.resolved_id,
                    "matched_by": result.matched_by,
                    "status": result.status,
                })

                if result.status == "available":
                    if result.resolved_id not in selected:
                        selected.append(result.resolved_id)
                else:
                    warnings.append(
                        f"Featurizer '{name}' resolved to '{result.resolved_id}' "
                        f"(status={result.status}) — not executable."
                    )

    # ---- Priority 2: legacy recommended_featurizers ----
    if not selected:
        if recommended is not None and isinstance(recommended, list) and len(recommended) > 0:
            warnings.append(
                "Using legacy 'recommended_featurizers' field. "
                "Workflow Plan should be updated to use 'executable_featurizers'."
            )
            for name in recommended:
                result = resolve(name)
                resolution_log.append({
                    "input": name,
                    "resolved_to": result.resolved_id,
                    "matched_by": result.matched_by,
                    "status": result.status,
                })

                if result.status == "available":
                    # Also check modality compatibility
                    spec_resolved = resolve_to_available(name, input_modality)
                    if spec_resolved.status == "available":
                        if result.resolved_id not in selected:
                            selected.append(result.resolved_id)
                    else:
                        warnings.append(
                            f"Featurizer '{name}' resolved to '{result.resolved_id}' "
                            f"but does not support input modality '{input_modality}'."
                        )
                elif result.resolved_id:
                    warnings.append(
                        f"Featurizer '{name}' resolved to '{result.resolved_id}' "
                        f"but has status '{result.status}'."
                    )
                else:
                    warnings.append(
                        f"Featurizer '{name}' not found in Registry."
                    )

    # ---- Priority 3: Registry fallback ----
    if not selected:
        fallback_result = get_default_fallback(input_modality)
        if fallback_result.fallback_featurizer_id:
            selected = [fallback_result.fallback_featurizer_id]
            resolution_log.append({
                "input": "(fallback)",
                "resolved_to": fallback_result.fallback_featurizer_id,
                "matched_by": "fallback",
                "status": "available",
            })
            warnings.append(
                f"No executable featurizers found. Using Registry fallback: "
                f"'{fallback_result.fallback_featurizer_id}'. {fallback_result.reason}"
            )
        else:
            warnings.append(
                f"No featurizer available for input modality '{input_modality}'."
            )

    # Collect unsupported featurizers for reporting
    unsupported = list(unsupported_future)
    for entry in resolution_log:
        if entry.get("status") not in ("available", None) and entry.get("resolved_to"):
            if entry["resolved_to"] not in unsupported:
                unsupported.append(entry["input"])

    for w in warnings:
        logger.info("Strategy resolver: %s", w)

    return ResolvedFeatureStrategy(
        feature_type=feature_type,
        input_modality=input_modality,
        selected_featurizers=selected,
        semantic_featurizers=list(semantic),
        unsupported_featurizers=unsupported,
        fallback_featurizers=[],
        resolution_log=resolution_log,
        scaling_required=scaling_required,
        feature_selection_required=selection_required,
        structure_features_required=structure_required,
    )
