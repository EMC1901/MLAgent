import logging
from typing import Dict, Any, List
from app.modules.iteration_decision.schemas import EvidenceItem
from app.modules.iteration_decision.enums import EvidenceType

logger = logging.getLogger(__name__)


def extract_materials_evidence(upstream: Dict[str, Any], metrics: Dict[str, Any]) -> List[EvidenceItem]:
    items: List[EvidenceItem] = []

    # Task interpretation for materials context
    ti = upstream.get("task_interpretation", {}).get("interpretation_json") or {}
    if ti:
        target_property = ti.get("prediction_target") or ti.get("target_property") or ""
        material_system = ti.get("material_system") or ti.get("materials_system") or ""
        task_type = ti.get("task_type") or ""
        if target_property:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.MATERIALS_CONSTRAINT,
                source_module="task_interpretation",
                source_field="prediction_target",
                value=target_property,
                interpretation=f"Target materials property: {target_property}. Physical constraints may apply.",
            ))
        if material_system:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.MATERIALS_CONSTRAINT,
                source_module="task_interpretation",
                source_field="material_system",
                value=material_system,
                interpretation=f"Material system under study: {material_system}.",
            ))

    # Dataset profile for chemical space coverage
    dp = upstream.get("dataset_profile", {}).get("profile_json") or {}
    if dp:
        n_samples = dp.get("n_samples") or dp.get("row_count")
        if n_samples:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.DATA_PROFILE,
                source_module="dataset_profile",
                source_field="n_samples",
                value=n_samples,
                interpretation=f"Dataset size: {n_samples} samples. Small datasets limit model generalization in materials applications.",
            ))

    # Feature evidence
    fe = upstream.get("feature_engineering", {}).get("feature_json") or {}
    fp = upstream.get("feature_preprocessing", {}).get("preprocessing_json") or {}

    n_features = fe.get("n_features_generated") or fe.get("n_features")
    if n_features:
        items.append(EvidenceItem(
            evidence_type=EvidenceType.FEATURE_PROFILE,
            source_module="feature_engineering",
            source_field="n_features",
            value=n_features,
            interpretation=f"Number of features generated. For materials properties, ensure features encode physically meaningful quantities.",
        ))

    if fp:
        n_final = fp.get("n_final_features")
        n_dropped = fp.get("n_features_dropped")
        n_initial = fp.get("n_initial_features")
        if n_final is not None:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.FEATURE_PROFILE,
                source_module="feature_preprocessing",
                source_field="n_final_features",
                value=n_final,
                interpretation="Final feature count after preprocessing.",
            ))
        if n_dropped is not None:
            items.append(EvidenceItem(
                evidence_type=EvidenceType.FEATURE_PROFILE,
                source_module="feature_preprocessing",
                source_field="n_features_dropped",
                value=n_dropped,
                interpretation=f"Features dropped during preprocessing. Check if materials-relevant features were removed.",
            ))

    # Workflow plan for feature strategy
    wp = upstream.get("workflow_plan", {}).get("plan_json") or {}
    if wp:
        f_strategy = wp.get("feature_strategy") or {}
        if f_strategy:
            actions = f_strategy.get("selected_feature_actions") or []
            if actions:
                action_names = [a.get("capability_id", a.get("action_id", "?")) for a in actions[:5]]
                items.append(EvidenceItem(
                    evidence_type=EvidenceType.FEATURE_PROFILE,
                    source_module="workflow_planning",
                    source_field="feature_strategy",
                    value=action_names,
                    interpretation="Feature engineering actions executed. Gaps here directly limit materials property prediction.",
                ))

    logger.info("Materials evidence — %d items extracted", len(items))
    return items
