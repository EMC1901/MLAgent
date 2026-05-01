import uuid
from datetime import datetime
from typing import Dict, Any


def build_interpretation(
    task_id: str,
    llm_output: Dict[str, Any],
    llm_request: Dict[str, Any],
    llm_response_raw: str,
) -> Dict[str, Any]:
    interpretation_id = f"interp_{uuid.uuid4().hex[:8]}"
    now = datetime.now()

    ambiguities = llm_output.get("ambiguities", [])
    warnings = llm_output.get("warnings", [])

    if ambiguities or warnings:
        status = "interpreted_with_warning"
    else:
        status = "interpreted"

    interpretation = {
        "interpretation_id": interpretation_id,
        "task_id": task_id,
        "status": status,
        "interpreted_task_type": llm_output.get("interpreted_task_type"),
        "interpreted_input_modality": llm_output.get("interpreted_input_modality"),
        "interpreted_material_domain": llm_output.get("interpreted_material_domain"),
        "interpreted_prediction_target": llm_output.get("interpreted_prediction_target"),
        "modeling_intent": llm_output.get("modeling_intent"),
        "dataset_intent": llm_output.get("dataset_intent"),
        "planning_hint": llm_output.get("planning_hint"),
        "constraint_interpretation": llm_output.get("constraint_interpretation"),
        "recommended_defaults": llm_output.get("recommended_defaults"),
        "ambiguities": ambiguities,
        "warnings": warnings,
        "llm_reasoning_summary": llm_output.get("llm_reasoning_summary"),
        "confidence_score": llm_output.get("confidence_score"),
        "llm_request_json": llm_request,
        "llm_response_json": {"raw": llm_response_raw},
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }

    return interpretation
