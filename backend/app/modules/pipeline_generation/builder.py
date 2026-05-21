import logging
import uuid
from datetime import datetime
from app.modules.pipeline_generation.schemas import (
    PipelineGenerationResponse,
    PipelineBundle,
    PipelineValidationResult,
)
from app.modules.pipeline_generation.enums import PipelineGenerationStatus, GenerationMode

logger = logging.getLogger(__name__)


def build_pipeline_bundle(
    bundle_id: str,
    context: dict,
    pipeline_specs: list,
    trial_plan,
) -> PipelineBundle:
    specs = [s if isinstance(s, dict) else s.model_dump() for s in pipeline_specs]
    eval_plan = context.get("evaluation_plan", {})
    validation_plan = context.get("validation_plan", {})
    hpo_plan = context.get("hpo_plan", {})

    return PipelineBundle(
        bundle_id=bundle_id,
        task_id=context.get("task_id", ""),
        model_search_context_id=context.get("model_search_context_id", ""),
        task_type=context.get("task_type"),
        target_column=context.get("target_column"),
        feature_columns=context.get("feature_columns", []),
        primary_metric=context.get("primary_metric"),
        metric_direction=eval_plan.get("metric_direction", "minimize") if isinstance(eval_plan, dict) else "minimize",
        model_ready_matrix_path=context.get("model_ready_matrix_path"),
        preprocessor_artifact_path=context.get("preprocessor_artifact_path"),
        pipeline_specs=[
            s if isinstance(s, dict) else s.model_dump()
            for s in pipeline_specs
        ],
        validation_plan=validation_plan if isinstance(validation_plan, dict) else {},
        evaluation_plan=eval_plan if isinstance(eval_plan, dict) else {},
        hpo_plan=hpo_plan if isinstance(hpo_plan, dict) else {},
        execution_policy={"mode": "sequential", "stop_on_failure": True},
        created_by="pipeline_generation_module",
    )


def build_pipeline_generation_response(
    pg_id: str,
    context: dict,
    pipeline_bundle,
    pipeline_specs: list,
    trial_plan,
    component_binding_result,
    artifact_manifest,
    validation_result,
    safety_check_result,
    llm_advisory_review,
    execution_input,
    use_llm_reviewer: bool,
    warnings: list,
    errors: list,
) -> PipelineGenerationResponse:
    specs = pipeline_specs
    n_baseline = sum(
        1 for s in specs
        if (s.pipeline_role if hasattr(s, "pipeline_role") else s.get("pipeline_role")) == "baseline"
    )
    n_hpo = sum(
        1 for s in specs
        if (s.hpo_enabled if hasattr(s, "hpo_enabled") else s.get("hpo_enabled"))
    )

    if errors:
        status = PipelineGenerationStatus.FAILED
    elif warnings:
        status = PipelineGenerationStatus.GENERATED_WITH_WARNING
    else:
        status = PipelineGenerationStatus.GENERATED

    generation_mode = (
        GenerationMode.SYSTEM_TEMPLATE_WITH_LLM_REVIEW
        if use_llm_reviewer
        else GenerationMode.SYSTEM_TEMPLATE_BASED
    )

    ready = execution_input.ready_for_execution if execution_input else False

    return PipelineGenerationResponse(
        pipeline_generation_id=pg_id,
        task_id=context.get("task_id"),
        model_search_context_id=context.get("model_search_context_id"),
        feature_preprocessing_id=context.get("feature_preprocessing_id"),
        status=status,
        generation_mode=generation_mode,
        n_pipeline_specs=len(specs),
        n_baseline_specs=n_baseline,
        n_hpo_specs=n_hpo,
        pipeline_bundle=pipeline_bundle,
        pipeline_specs=[s if isinstance(s, dict) else s.model_dump() for s in specs],
        trial_plan=trial_plan.model_dump() if trial_plan and hasattr(trial_plan, "model_dump") else trial_plan,
        component_binding_result=component_binding_result.model_dump() if component_binding_result and hasattr(component_binding_result, "model_dump") else component_binding_result,
        artifact_manifest=artifact_manifest.model_dump() if artifact_manifest and hasattr(artifact_manifest, "model_dump") else artifact_manifest,
        pipeline_validation_result=validation_result.model_dump() if validation_result and hasattr(validation_result, "model_dump") else validation_result,
        safety_check_result=safety_check_result.model_dump() if safety_check_result and hasattr(safety_check_result, "model_dump") else safety_check_result,
        llm_advisory_review=llm_advisory_review.model_dump() if llm_advisory_review and hasattr(llm_advisory_review, "model_dump") else llm_advisory_review,
        execution_input=execution_input.model_dump() if execution_input and hasattr(execution_input, "model_dump") else execution_input,
        ready_for_execution=ready,
        warnings=warnings,
        error_message="; ".join(errors) if errors else None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
