from typing import Any, Dict, Optional

from sqlmodel import Session

from app.modules.final_output.schemas import WorkflowTraceSummary
from app.modules.feature_engineering.repository import FeatureEngineeringRepository
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.modules.interpretability_analysis.repository import (
    InterpretabilityAnalysisRepository,
)
from app.modules.iteration_decision.repository import IterationDecisionRepository
from app.modules.metric_evaluation.repository import MetricEvaluationRepository
from app.modules.model_search_context.repository import ModelSearchContextRepository
from app.modules.pipeline_execution.repository import PipelineExecutionRepository
from app.modules.pipeline_generation.repository import PipelineGenerationRepository
from app.modules.task_specification.repository import TaskSpecificationRepository


_MODULE_ORDER = [
    "01_task_specification",
    "02_dataset_profile",
    "03_workflow_plan",
    "04_automated_feature_engineering",
    "05_ai_guided_data_preprocessing",
    "06_model_search_plan",
    "07_executable_pipeline_generation",
    "08_pipeline_execution_and_training",
    "09_metric_evaluation",
    "10_iteration_decision",
    "11_interpretability_analysis",
    "04_model_ready_feature_summary",
    "05_candidate_model_plan",
    "06_hpo_plan",
    "07_pipeline_specs",
    "08_training_evaluation_results",
    "09_interpretability_analysis",
    "10_final_output_package",
]


def build_paper_evidence_package(
    session: Session,
    task_id: str,
    workflow_trace: WorkflowTraceSummary,
) -> Dict[str, Any]:
    modules: Dict[str, Any] = {}
    included_modules = [
        "01_task_specification",
        "02_dataset_profile",
        "03_workflow_plan",
        "04_automated_feature_engineering",
        "05_ai_guided_data_preprocessing",
        "06_model_search_plan",
        "07_executable_pipeline_generation",
        "08_pipeline_execution_and_training",
        "09_metric_evaluation",
        "10_iteration_decision",
        "11_interpretability_analysis",
    ]

    modules["01_task_specification"] = _safe_build_evidence_module(
        "01_task_specification",
        _build_task_specification_evidence,
        session=session,
        task_id=task_id,
        workflow_trace=workflow_trace,
    )
    modules["02_dataset_profile"] = _safe_build_evidence_module(
        "02_dataset_profile",
        _build_dataset_profile_evidence,
        workflow_trace,
    )
    modules["03_workflow_plan"] = _safe_build_evidence_module(
        "03_workflow_plan",
        _build_workflow_plan_evidence,
        workflow_trace,
    )
    modules["04_automated_feature_engineering"] = _safe_build_evidence_module(
        "04_automated_feature_engineering",
        _build_automated_feature_engineering_evidence,
        session=session,
        task_id=task_id,
    )
    modules["05_ai_guided_data_preprocessing"] = _safe_build_evidence_module(
        "05_ai_guided_data_preprocessing",
        _build_ai_guided_data_preprocessing_evidence,
        session=session,
        task_id=task_id,
    )
    modules["06_model_search_plan"] = _safe_build_evidence_module(
        "06_model_search_plan",
        _build_model_search_plan_evidence,
        session=session,
        task_id=task_id,
    )
    modules["07_executable_pipeline_generation"] = _safe_build_evidence_module(
        "07_executable_pipeline_generation",
        _build_executable_pipeline_generation_evidence,
        session=session,
        task_id=task_id,
    )
    modules["08_pipeline_execution_and_training"] = _safe_build_evidence_module(
        "08_pipeline_execution_and_training",
        _build_pipeline_execution_and_training_evidence,
        session=session,
        task_id=task_id,
    )
    modules["09_metric_evaluation"] = _safe_build_evidence_module(
        "09_metric_evaluation",
        _build_metric_evaluation_evidence,
        session=session,
        task_id=task_id,
    )
    modules["10_iteration_decision"] = _safe_build_evidence_module(
        "10_iteration_decision",
        _build_iteration_decision_evidence,
        session=session,
        task_id=task_id,
    )
    modules["11_interpretability_analysis"] = _safe_build_evidence_module(
        "11_interpretability_analysis",
        _build_interpretability_analysis_evidence,
        session=session,
        task_id=task_id,
    )

    return {
        "document_type": "paper_evidence_package",
        "purpose": (
            "Condensed system-operation evidence for journal paper writing. "
            "This file extracts paper-relevant mechanisms from full module JSON "
            "outputs while removing raw prompts, schemas, timestamps, and other "
            "low-value audit details."
        ),
        "task_id": task_id,
        "generation_scope": {
            "included_modules": included_modules,
            "pending_modules": [m for m in _MODULE_ORDER if m not in included_modules],
        },
        "modules": modules,
    }


def _safe_build_evidence_module(
    module_key: str,
    builder,
    *args: Any,
    **kwargs: Any,
) -> Dict[str, Any]:
    try:
        return builder(*args, **kwargs)
    except Exception as exc:
        return {
            "module_name": module_key,
            "status": "failed",
            "error": str(exc),
            "note": (
                "This module failed during paper-evidence summarization. "
                "Other modules remain available in the evidence package."
            ),
        }


def _build_task_specification_evidence(
    session: Session,
    task_id: str,
    workflow_trace: WorkflowTraceSummary,
) -> Dict[str, Any]:
    task_spec = TaskSpecificationRepository().get_by_id(session, task_id)
    task_spec_json = task_spec.task_spec_json if task_spec and task_spec.task_spec_json else {}

    trace_artifacts = workflow_trace.workflow_trace_artifacts or {}
    task_trace = trace_artifacts.get("task_specification") or {}
    interpretation = task_trace.get("interpretation_detail") or {}

    planning_hint = _pick_dict(interpretation.get("planning_hint"))
    dataset_intent = _pick_dict(interpretation.get("dataset_intent"))
    recommended_defaults = _pick_dict(interpretation.get("recommended_defaults"))

    return {
        "module_name": "Task Specification and Semantic Interpretation",
        "role_in_system": (
            "Convert user-provided materials machine learning task descriptions "
            "into validated and semantically interpreted machine-readable task context."
        ),
        "source_traceability": {
            "raw_task_source": "task_specification.task_spec_json",
            "semantic_interpretation_source": (
                "workflow_trace.workflow_trace_artifacts.task_specification.interpretation_detail"
            ),
            "rule_implementation_source": "app.modules.task_specification.normalizer/validator",
            "llm_schema_source": "app.modules.task_interpretation.prompt_builder",
        },
        "input_summary": _build_input_summary(task_spec, task_spec_json),
        "rule_based_validation": {
            "normalization": {
                "fields": ["task_type", "input_type", "evaluation_metric", "user_priority"],
                "purpose": (
                    "Map user-facing terms into canonical internal labels before "
                    "validation and downstream planning."
                ),
            },
            "required_field_checks": [
                "prediction_target",
                "task_type",
                "dataset_description",
                "input_type",
                "target_column",
            ],
            "compatibility_checks": [
                "task_type_vs_evaluation_metric",
                "input_type_vs_dataset_description",
            ],
            "supported_task_metric_pairs": {
                "regression": ["MAE", "RMSE", "R2"],
                "classification": ["Accuracy", "F1", "ROC-AUC"],
            },
            "unsupported_cases": [
                "ranking task type is currently rejected",
                "ranking metrics Spearman, NDCG, and Top-k recall are currently rejected",
            ],
            "validation_status_fields": {
                "status": getattr(task_spec, "status", None),
                "missing_fields": task_spec_json.get("missing_fields", []),
                "validation_messages": task_spec_json.get("validation_messages", []),
            },
        },
        "llm_output_constraints": {
            "schema_constrained_json": True,
            "forbidden_outputs": [
                "markdown",
                "code",
                "complete ML workflow plan",
                "specific model selection",
                "hyperparameter selection",
                "assumptions that real data has already been loaded",
            ],
            "required_risk_fields": ["ambiguities", "warnings", "confidence_score"],
        },
        "llm_semantic_interpretation": _build_llm_semantic_interpretation(
            task_trace=task_trace,
            interpretation=interpretation,
        ),
        "downstream_signals": {
            "task_family": planning_hint.get("task_family"),
            "input_representation": planning_hint.get("input_representation"),
            "requires_feature_engineering": planning_hint.get("requires_feature_engineering"),
            "requires_model_interpretability": planning_hint.get("requires_model_interpretability"),
            "suggested_metric_direction": planning_hint.get("suggested_metric_direction"),
            "expected_input_columns": dataset_intent.get("expected_input_columns", []),
            "expected_target_column": dataset_intent.get("expected_target_column"),
            "evaluation_metric": recommended_defaults.get("evaluation_metric"),
            "validation_strategy": recommended_defaults.get("validation_strategy"),
        },
        "paper_relevance": {
            "methodological_value": (
                "Hybrid rule-based and LLM-based task understanding for materials "
                "machine learning automation."
            ),
            "innovation_point": (
                "The system makes task intent, domain constraints, ambiguity, and "
                "risk explicit before workflow planning."
            ),
            "why_this_module_matters": (
                "Downstream modules receive a unified task context instead of raw "
                "user text, enabling automatic dataset profiling, workflow planning, "
                "feature decisions, model search, and interpretability choices to be "
                "conditioned on explicit materials-domain semantics."
            ),
        },
        "excluded_from_evidence": [
            "llm_request_json",
            "llm_response_json.raw",
            "complete output schema",
            "raw prompt text",
            "created_at",
            "updated_at",
            "random interpretation identifiers",
        ],
    }


def _build_dataset_profile_evidence(workflow_trace: WorkflowTraceSummary) -> Dict[str, Any]:
    trace_artifacts = workflow_trace.workflow_trace_artifacts or {}
    dataset_trace = trace_artifacts.get("dataset_profile") or {}
    profile = dataset_trace.get("profile_detail") or {}

    dataset_source = _pick_dict(profile.get("dataset_source"))
    dataset_schema = _pick_dict(profile.get("dataset_schema"))
    modality_check = _pick_dict(profile.get("modality_check"))
    target_profile = _pick_dict(profile.get("target_profile"))
    data_quality = _pick_dict(profile.get("data_quality"))
    profiling_summary = _pick_dict(profile.get("profiling_summary"))
    workflow_planning_input = _pick_dict(profile.get("workflow_planning_input"))
    preview = _pick_dict(profile.get("preview"))

    return {
        "module_name": "Dataset Profiling and Data Readiness Assessment",
        "role_in_system": (
            "Validate that the actual dataset is loadable, schema-compatible, "
            "modality-consistent, and usable for downstream machine learning "
            "workflow planning."
        ),
        "source_traceability": {
            "profile_source": (
                "workflow_trace.workflow_trace_artifacts.dataset_profile.profile_detail"
            ),
            "context_source": "app.modules.dataset_profile.context_builder",
            "source_resolution_source": "app.modules.dataset_profile.source_resolver",
            "checker_sources": [
                "app.modules.dataset_profile.checkers.schema_checker",
                "app.modules.dataset_profile.checkers.modality_checker",
                "app.modules.dataset_profile.checkers.quality_checker",
                "app.modules.dataset_profile.checkers.target_checker",
            ],
        },
        "source_resolution": {
            "source_type": _first_present(
                dataset_source.get("source_type"),
                dataset_trace.get("source_type"),
            ),
            "dataset_reference": dataset_source.get("dataset_reference"),
            "loader": dataset_source.get("loader"),
            "loaded_from": dataset_source.get("loaded_from"),
            "file_name": dataset_source.get("file_name"),
        },
        "dataset_schema_summary": {
            "n_samples": _first_present(
                dataset_schema.get("n_samples"),
                dataset_trace.get("n_samples"),
            ),
            "n_columns": _first_present(
                dataset_schema.get("n_columns"),
                dataset_trace.get("n_columns"),
            ),
            "input_columns": dataset_schema.get("input_columns", []),
            "target_column": _first_present(
                dataset_schema.get("target_column"),
                dataset_trace.get("target_column"),
            ),
            "columns": _summarize_columns(dataset_schema.get("columns", [])),
            "preview_metadata": {
                "columns": preview.get("columns", []),
                "total_rows": preview.get("total_rows"),
                "preview_rows_excluded": len(preview.get("rows", []) or []),
            },
        },
        "diagnostic_methods": {
            "schema_validation": [
                "target column existence",
                "expected input column existence",
                "duplicate column names",
                "fully-null columns",
            ],
            "modality_checking": [
                "expected vs detected input modality",
                "composition pattern validation",
                "numeric descriptor detection",
                "structure/text/mixed heuristic detection",
            ],
            "data_quality_checks": [
                "missing values",
                "target missingness",
                "duplicate rows",
                "duplicate input samples",
                "empty strings",
                "constant columns",
                "high-missing-rate columns",
                "small sample warning",
            ],
            "target_profiling": {
                "regression": [
                    "numeric range",
                    "mean",
                    "median",
                    "standard deviation",
                    "skewness",
                    "IQR-based outlier count",
                ],
                "classification": [
                    "class count",
                    "class distribution",
                    "majority class ratio",
                    "minority class count",
                    "imbalance flag",
                ],
            },
        },
        "modality_consistency": {
            "expected_input_modality": modality_check.get("expected_input_modality"),
            "detected_input_modality": modality_check.get("detected_input_modality"),
            "is_consistent": modality_check.get("is_consistent"),
            "messages": modality_check.get("messages", []),
        },
        "target_profile_summary": _pick_keys(
            target_profile,
            [
                "target_column",
                "task_type",
                "dtype",
                "missing_count",
                "missing_ratio",
                "min",
                "max",
                "mean",
                "median",
                "std",
                "skewness",
                "outlier_count",
                "class_count",
                "class_distribution",
                "majority_class_ratio",
                "minority_class_count",
                "is_imbalanced",
            ],
        ),
        "data_quality_summary": {
            "missing_values": data_quality.get("missing_values", {}),
            "duplicates": data_quality.get("duplicates", {}),
            "invalid_rows": _summarize_invalid_rows(data_quality.get("invalid_rows", {})),
            "warnings": data_quality.get("warnings", []),
            "errors": data_quality.get("errors", []),
        },
        "profiling_summary": _pick_keys(
            profiling_summary,
            [
                "is_loadable",
                "is_usable_for_ml",
                "sample_size_level",
                "quality_level",
                "main_issues",
                "recommended_next_step",
            ],
        ),
        "workflow_planning_signals": _pick_keys(
            workflow_planning_input,
            [
                "input_modality",
                "task_type",
                "target_column",
                "input_columns",
                "n_samples",
                "n_columns",
                "n_features_raw",
                "sample_size_level",
                "has_missing_values",
                "has_duplicates",
                "requires_cleaning",
                "requires_target_transformation_check",
                "target_distribution",
                "quality_level",
                "is_usable_for_ml",
            ],
        ),
        "paper_relevance": {
            "methodological_value": (
                "Data readiness assessment conditioned on the task semantics "
                "created by the task interpretation module."
            ),
            "innovation_point": (
                "The system converts dataset diagnostics into explicit "
                "workflow-planning constraints instead of treating profiling as "
                "a passive descriptive report."
            ),
            "why_this_module_matters": (
                "It prevents blind workflow generation by checking whether the "
                "actual data source, schema, modality, target, and quality are "
                "consistent with the intended materials machine learning task."
            ),
        },
        "excluded_from_evidence": [
            "preview.rows",
            "raw structure strings",
            "file_path",
            "created_at",
            "updated_at",
            "random dataset profile identifiers",
        ],
    }


def _build_workflow_plan_evidence(workflow_trace: WorkflowTraceSummary) -> Dict[str, Any]:
    trace_artifacts = workflow_trace.workflow_trace_artifacts or {}
    workflow_trace_data = trace_artifacts.get("workflow_plan") or {}
    plan = workflow_trace_data.get("plan_detail") or {}

    task_summary = _pick_dict(plan.get("task_summary"))
    data_strategy = _pick_dict(plan.get("data_strategy"))
    feature_strategy = _first_non_empty_dict(
        plan.get("feature_strategy"),
        workflow_trace_data.get("feature_strategy"),
    )
    model_strategy = _first_non_empty_dict(
        plan.get("model_strategy"),
        workflow_trace_data.get("model_strategy"),
    )
    preprocessing_intent = _first_non_empty_dict(
        plan.get("preprocessing_intent"),
        workflow_trace_data.get("preprocessing_intent"),
    )
    workflow_rationale = _first_non_empty_dict(
        plan.get("workflow_rationale"),
        workflow_trace_data.get("workflow_rationale"),
    )

    return {
        "module_name": "AI-guided Workflow Planning and Strategy Generation",
        "role_in_system": (
            "Generate a complete, constrained, auditable machine learning workflow "
            "plan from task semantics, dataset diagnostics, and available "
            "feature-engineering capabilities."
        ),
        "source_traceability": {
            "plan_source": "workflow_trace.workflow_trace_artifacts.workflow_plan.plan_detail",
            "context_source": "app.modules.workflow_planning.context_builder",
            "prompt_source": "app.modules.workflow_planning.prompt_builder",
            "validation_source": "app.modules.workflow_planning.validator",
            "registry_sources": [
                "app.shared.registry.fe_capability_registry",
                "app.shared.registry.featurizer_registry",
            ],
        },
        "upstream_readiness_gates": {
            "task_specification_status": ["valid", "valid_with_warning"],
            "task_interpretation_status": [
                "interpreted",
                "interpreted_with_warning",
            ],
            "dataset_profile_status": ["profiled", "profiled_with_warning"],
            "requires_dataset_usable_for_ml": True,
            "requires_workflow_planning_input": True,
        },
        "planning_constraints": {
            "planning_mode": _first_present(
                plan.get("planning_mode"),
                workflow_trace_data.get("planning_mode"),
                "llm_guided",
            ),
            "schema_constrained_json": True,
            "registry_constrained_feature_actions": True,
            "requires_complete_workflow_plan": True,
            "forbidden_outputs": [
                "executable code",
                "pseudocode",
                "fabricated training results",
                "fabricated metric values",
                "claims that models have already been trained",
                "modification of upstream task interpretation or dataset profile",
            ],
            "feature_action_constraints": [
                "selected capability_id values must exist in the FE Capability Registry",
                "required or recommended capabilities must be executable or available",
                "selected feature actions require complete decision_rationale",
                "rejected feature actions require explicit rejection reasons",
            ],
            "model_action_constraints": [
                "baseline_models must contain exactly one model family",
                "selected model actions require complete decision_rationale",
                "rejected model actions require explicit rejection reasons",
            ],
            "preprocessing_boundary": (
                "Only high-level preprocessing intent is allowed here; final "
                "column-level preprocessing decisions are deferred to the Feature "
                "Preprocessing module after Feature Engineering output exists."
            ),
        },
        "plan_summary": {
            "status": _first_present(plan.get("status"), workflow_trace_data.get("status")),
            "task_type": _first_present(
                task_summary.get("task_type"),
                workflow_trace_data.get("task_type"),
            ),
            "primary_metric": _first_present(
                _pick_dict(plan.get("evaluation_strategy")).get("primary_metric"),
                workflow_trace_data.get("primary_metric"),
            ),
            "feature_type": _first_present(
                feature_strategy.get("feature_type"),
                workflow_trace_data.get("feature_type"),
            ),
            "validation_strategy": _first_present(
                _pick_dict(plan.get("validation_strategy")).get("split_strategy"),
                workflow_trace_data.get("validation_strategy"),
            ),
            "hpo_enabled": _first_present(
                _pick_dict(plan.get("hpo_strategy")).get("enabled"),
                workflow_trace_data.get("hpo_enabled"),
            ),
            "interpretability_enabled": _first_present(
                _pick_dict(plan.get("interpretability_strategy")).get("enabled"),
                workflow_trace_data.get("interpretability_enabled"),
            ),
            "confidence_score": plan.get("confidence_score"),
            "fe_registry_snapshot_version": plan.get("fe_registry_snapshot_version"),
        },
        "task_summary": _pick_keys(
            task_summary,
            [
                "task_type",
                "input_modality",
                "prediction_target",
                "material_domain",
                "primary_goal",
            ],
        ),
        "data_strategy": _pick_keys(
            data_strategy,
            [
                "input_columns",
                "target_column",
                "required_cleaning_steps",
                "target_handling",
                "duplicate_handling",
                "missing_value_strategy",
            ],
        ),
        "feature_strategy_summary": {
            "strategy_id": feature_strategy.get("strategy_id"),
            "strategy_version": feature_strategy.get("strategy_version"),
            "feature_type": feature_strategy.get("feature_type"),
            "executable_featurizers": feature_strategy.get("executable_featurizers", []),
            "semantic_featurizers": feature_strategy.get("semantic_featurizers", []),
            "recommended_featurizers": feature_strategy.get("recommended_featurizers", []),
            "unsupported_future_featurizers": feature_strategy.get(
                "unsupported_future_featurizers",
                [],
            ),
            "requires_structure_features": feature_strategy.get("requires_structure_features"),
            "feature_selection_required": feature_strategy.get("feature_selection_required"),
            "feature_scaling_required": feature_strategy.get("feature_scaling_required"),
            "input_modality_assessment": feature_strategy.get("input_modality_assessment"),
            "fallback_strategy": feature_strategy.get("fallback_strategy"),
            "feature_group_expectations": feature_strategy.get(
                "feature_group_expectations",
                [],
            ),
        },
        "selected_feature_actions": _summarize_feature_actions(
            feature_strategy.get("selected_feature_actions", [])
        ),
        "rejected_feature_actions": _summarize_rejected_feature_actions(
            feature_strategy.get("rejected_feature_actions", [])
        ),
        "model_strategy_summary": {
            "candidate_model_families": model_strategy.get("candidate_model_families", []),
            "baseline_models": model_strategy.get("baseline_models", []),
            "preferred_model_bias": model_strategy.get("preferred_model_bias"),
            "excluded_model_families": model_strategy.get("excluded_model_families", []),
            "model_selection_rationale_summary": model_strategy.get(
                "model_selection_rationale_summary"
            ),
        },
        "selected_model_actions": _summarize_model_actions(
            model_strategy.get("selected_model_actions", [])
        ),
        "rejected_model_actions": _summarize_rejected_model_actions(
            model_strategy.get("rejected_model_actions", [])
        ),
        "preprocessing_intent": _pick_keys(
            preprocessing_intent,
            [
                "intent_id",
                "high_level_goals",
                "risks_to_check_after_feature_engineering",
                "non_final_notes",
            ],
        ),
        "validation_evaluation_hpo": {
            "validation_strategy": _pick_dict(plan.get("validation_strategy")),
            "evaluation_strategy": _pick_dict(plan.get("evaluation_strategy")),
            "hpo_strategy": _pick_dict(plan.get("hpo_strategy")),
        },
        "interpretability_strategy": _pick_dict(plan.get("interpretability_strategy")),
        "pipeline_generation_input": _pick_dict(plan.get("pipeline_generation_input")),
        "workflow_rationale": {
            "overall_reasoning_summary": workflow_rationale.get(
                "overall_reasoning_summary"
            ),
            "key_assumptions": workflow_rationale.get("key_assumptions", []),
            "known_risks": workflow_rationale.get("known_risks", []),
            "planning_warnings": plan.get("planning_warnings", []),
            "planning_assumptions": plan.get("planning_assumptions", []),
            "llm_reasoning_summary": plan.get("llm_reasoning_summary"),
        },
        "paper_relevance": {
            "methodological_value": (
                "Schema- and registry-constrained LLM planning that converts "
                "upstream task semantics and dataset diagnostics into a complete "
                "AutoML workflow strategy."
            ),
            "innovation_point": (
                "The module records not only selected strategies, but also "
                "explicit evidence, materials-science rationale, risks, rejected "
                "alternatives, and fallback actions."
            ),
            "why_this_module_matters": (
                "It turns LLM reasoning into a structured, auditable, and "
                "downstream-executable plan while preventing code generation, "
                "unsupported feature capabilities, invalid baselines, and "
                "fabricated performance claims."
            ),
        },
        "excluded_from_evidence": [
            "llm_request",
            "llm_response",
            "raw prompt text",
            "full output schema",
            "full FE registry prompt",
            "created_at",
            "updated_at",
            "random workflow plan identifiers",
        ],
    }


def _build_automated_feature_engineering_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    feature_engineering = FeatureEngineeringRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Automated Feature Engineering and Feature Matrix Construction",
        "role_in_system": (
            "Translate the workflow plan's feature strategy into executable "
            "featurizer actions, construct a model-ready feature matrix, assess "
            "feature quality, and expose structured inputs for preprocessing and "
            "pipeline generation."
        ),
        "source_traceability": {
            "record_source": "feature_engineering table latest row by task_id",
            "full_json_source": "feature_engineering.feature_json",
            "side_json_sources": [
                "feature_engineering.feature_groups_json",
                "feature_engineering.quality_profile_json",
                "feature_engineering.execution_report_json",
                "feature_engineering.provenance_json",
                "feature_engineering.preprocessing_decision_input_json",
            ],
            "implementation_sources": [
                "app.modules.feature_engineering.context_builder",
                "app.modules.feature_engineering.strategy_resolver",
                "app.modules.feature_engineering.featurizers.featurizer_router",
                "app.modules.feature_engineering.feature_matrix_builder",
                "app.modules.feature_engineering.checkers.feature_quality_checker",
                "app.modules.feature_engineering.artifact_manager",
                "app.modules.feature_engineering.builder",
            ],
        },
        "upstream_readiness_gates": {
            "task_specification_status": ["valid", "valid_with_warning"],
            "task_interpretation_status": [
                "interpreted",
                "interpreted_with_warning",
            ],
            "dataset_profile_status": ["profiled", "profiled_with_warning"],
            "workflow_plan_status": ["planned", "planned_with_warning"],
            "requires_dataset_usable_for_ml": True,
            "requires_feature_strategy": True,
        },
    }

    if not feature_engineering:
        return {
            **base,
            "status": "missing",
            "note": (
                "No FeatureEngineering record was found for this task_id. "
                "Automated feature engineering evidence can be generated after "
                "the Feature Engineering module has run."
            ),
            "paper_relevance": _feature_engineering_paper_relevance(),
            "excluded_from_evidence": _feature_engineering_exclusions(),
        }

    feature_json = _pick_dict(getattr(feature_engineering, "feature_json", None))
    feature_generation = _pick_dict(feature_json.get("feature_generation"))
    feature_matrix = _first_non_empty_dict(
        feature_json.get("feature_matrix"),
        {
            "artifact_id": getattr(feature_engineering, "artifact_id", None),
            "file_path": getattr(feature_engineering, "artifact_path", None),
            "n_samples": getattr(feature_engineering, "n_samples", None),
            "n_features": getattr(feature_engineering, "n_features", None),
            "target_column": getattr(feature_engineering, "target_column", None),
        },
    )
    feature_schema = _pick_dict(feature_json.get("feature_schema"))
    feature_quality = _pick_dict(feature_json.get("feature_quality"))
    feature_groups = _first_non_empty_list(
        getattr(feature_engineering, "feature_groups_json", None),
        feature_json.get("feature_groups"),
    )
    quality_profile = _first_non_empty_dict(
        getattr(feature_engineering, "quality_profile_json", None),
        feature_json.get("feature_quality_profile"),
    )
    execution_report = _first_non_empty_dict(
        getattr(feature_engineering, "execution_report_json", None),
        feature_json.get("execution_report"),
    )
    provenance = _first_non_empty_dict(
        getattr(feature_engineering, "provenance_json", None),
        feature_json.get("feature_provenance"),
    )
    preprocessing_decision_input = _first_non_empty_dict(
        getattr(feature_engineering, "preprocessing_decision_input_json", None),
        feature_json.get("feature_preprocessing_decision_input"),
    )
    preprocessing_requirements = _pick_dict(
        feature_json.get("preprocessing_requirements")
    )
    downstream_input = _pick_dict(feature_json.get("downstream_input"))

    return {
        **base,
        "status": getattr(feature_engineering, "status", None),
        "execution_summary": {
            "feature_engineering_record_present": True,
            "input_modality": _first_present(
                getattr(feature_engineering, "input_modality", None),
                feature_json.get("input_modality"),
            ),
            "feature_type": _first_present(
                getattr(feature_engineering, "feature_type", None),
                feature_json.get("feature_type"),
            ),
            "executed_feature_strategy_id": _first_present(
                getattr(feature_engineering, "executed_feature_strategy_id", None),
                feature_json.get("executed_feature_strategy_id"),
            ),
            "is_ready_for_pipeline": _first_present(
                getattr(feature_engineering, "is_ready_for_pipeline", None),
                downstream_input.get("ready_for_pipeline_generation"),
            ),
            "warnings": feature_json.get("warnings", []),
            "errors": _first_present(
                feature_json.get("errors"),
                [getattr(feature_engineering, "error_message", None)]
                if getattr(feature_engineering, "error_message", None)
                else [],
            ),
        },
        "strategy_resolution": {
            "resolution_policy": [
                "Use workflow_plan.feature_strategy.selected_feature_actions when registry-backed actions are available.",
                "Otherwise use explicit executable_featurizers from the workflow plan.",
                "Otherwise use legacy recommended_featurizers when present.",
                "Otherwise fall back to registry-driven defaults for the detected modality.",
            ],
            "selected_featurizers": feature_generation.get("selected_featurizers", []),
            "semantic_featurizers": feature_generation.get("semantic_featurizers", []),
            "fallback_featurizers": feature_generation.get("fallback_featurizers", []),
            "skipped_featurizers": feature_generation.get("skipped_featurizers", []),
            "unsupported_future_featurizers": feature_generation.get(
                "unsupported_future_featurizers",
                [],
            ),
        },
        "feature_generation_summary": {
            "executed_featurizer_count": len(
                feature_generation.get("executed_featurizers", []) or []
            ),
            "total_generated_feature_count": sum(
                item.get("n_features_generated") or 0
                for item in feature_generation.get("executed_featurizers", []) or []
                if isinstance(item, dict)
            ),
            "total_failed_sample_count": sum(
                item.get("failed_sample_count") or 0
                for item in feature_generation.get("executed_featurizers", []) or []
                if isinstance(item, dict)
            ),
            "executed_featurizers": _summarize_executed_featurizers(
                feature_generation.get("executed_featurizers", [])
            ),
        },
        "feature_matrix_construction": {
            "construction_policy": [
                "Normalize featurizer outputs into a tabular feature matrix.",
                "Sanitize generated column names for downstream pipeline compatibility.",
                "Convert boolean-like columns into numeric form when possible.",
                "Drop non-numeric feature columns before model-ready output.",
                "Attach sample_id and target column metadata for traceability.",
            ],
            "matrix_summary": _pick_keys(
                feature_matrix,
                [
                    "artifact_id",
                    "storage_type",
                    "n_samples",
                    "n_features",
                    "target_column",
                    "index_column",
                ],
            ),
            "artifact_path_recorded": bool(feature_matrix.get("file_path")),
            "artifact_path_excluded": bool(feature_matrix.get("file_path")),
        },
        "feature_schema_summary": {
            "numeric_feature_count": feature_schema.get("numeric_feature_count"),
            "categorical_feature_count": feature_schema.get(
                "categorical_feature_count"
            ),
            "constant_feature_count": feature_schema.get("constant_feature_count"),
            "all_missing_feature_count": feature_schema.get(
                "all_missing_feature_count"
            ),
            "feature_columns": _summarize_feature_columns(
                feature_schema.get("feature_columns", [])
            ),
            "feature_groups": _summarize_feature_groups(
                feature_schema.get("feature_groups", [])
            ),
        },
        "feature_groups_summary": _summarize_feature_groups(feature_groups),
        "feature_quality_checks": {
            "implemented_checks": [
                "empty matrix",
                "minimum generated feature count",
                "high dimensionality",
                "duplicate feature names",
                "missing values",
                "all-missing features",
                "constant and near-constant features",
                "all-zero features",
                "non-numeric features",
                "infinite values",
                "high missing-ratio features",
                "feature-group-level quality",
            ],
            "quality_summary": {
                "is_valid_feature_matrix": feature_quality.get(
                    "is_valid_feature_matrix"
                ),
                "missing_values": _pick_dict(feature_quality.get("missing_values")),
                "invalid_feature_count": len(
                    feature_quality.get("invalid_features", []) or []
                ),
                "dropped_feature_count": len(
                    feature_quality.get("dropped_features", []) or []
                ),
                "failed_sample_count": len(
                    feature_quality.get("failed_samples", []) or []
                ),
                "constant_feature_count": len(
                    feature_quality.get("constant_features", []) or []
                ),
                "all_missing_feature_count": len(
                    feature_quality.get("all_missing_features", []) or []
                ),
                "warnings": feature_quality.get("warnings", []),
                "errors": feature_quality.get("errors", []),
            },
            "quality_profile_summary": _summarize_feature_quality_profile(
                quality_profile
            ),
        },
        "execution_report": _summarize_execution_report(execution_report),
        "feature_provenance": _summarize_feature_provenance(provenance),
        "preprocessing_decision_input_summary": (
            _summarize_feature_preprocessing_decision_input(
                preprocessing_decision_input
            )
        ),
        "preprocessing_requirements": _pick_keys(
            preprocessing_requirements,
            [
                "scaling_required",
                "imputation_required",
                "feature_selection_required",
            ],
        ),
        "downstream_interface": {
            "feature_matrix_artifact_id": downstream_input.get(
                "feature_matrix_artifact_id"
            ),
            "target_column": downstream_input.get("target_column"),
            "task_type": downstream_input.get("task_type"),
            "primary_metric": downstream_input.get("primary_metric"),
            "scaling_required": downstream_input.get("scaling_required"),
            "imputation_required": downstream_input.get("imputation_required"),
            "feature_selection_required": downstream_input.get(
                "feature_selection_required"
            ),
            "ready_for_pipeline_generation": downstream_input.get(
                "ready_for_pipeline_generation"
            ),
            "feature_columns": _summarize_feature_columns(
                downstream_input.get("feature_columns", [])
            ),
            "feature_groups": _summarize_feature_groups(
                downstream_input.get("feature_groups", [])
            ),
            "feature_matrix_path_recorded": bool(
                downstream_input.get("feature_matrix_path")
            ),
            "feature_matrix_path_excluded": bool(
                downstream_input.get("feature_matrix_path")
            ),
        },
        "paper_relevance": _feature_engineering_paper_relevance(),
        "excluded_from_evidence": _feature_engineering_exclusions(),
    }


def _build_ai_guided_data_preprocessing_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    preprocessing = FeaturePreprocessingRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "AI-guided Data Preprocessing and Fold-safe Model-ready Feature Construction",
        "role_in_system": (
            "Convert the feature-engineering output matrix into a model-ready "
            "feature representation through a registry-constrained LLM "
            "preprocessing plan, leakage-aware validation, global-safe "
            "execution, and fold-level preprocessing specifications for "
            "cross-validation."
        ),
        "source_traceability": {
            "record_source": "feature_preprocessing table latest row by task_id",
            "full_json_source": "feature_preprocessing.preprocessing_json",
            "side_json_sources": [
                "feature_preprocessing.preprocessing_plan_json",
                "feature_preprocessing.execution_report_json",
                "feature_preprocessing.removed_features_json",
                "feature_preprocessing.feature_lineage_json",
                "feature_preprocessing.explainability_report_json",
                "feature_preprocessing.provenance_json",
            ],
            "implementation_sources": [
                "app.modules.feature_preprocessing.context_builder",
                "app.modules.feature_preprocessing.llm_planner",
                "app.modules.feature_preprocessing.plan_validator",
                "app.modules.feature_preprocessing.plan_executor",
                "app.modules.feature_preprocessing.fold_pipeline_builder",
                "app.modules.feature_preprocessing.preprocessing_pipeline_builder",
                "app.modules.feature_preprocessing.artifact_manager",
            ],
        },
        "upstream_readiness_gates": {
            "task_specification_status": ["valid", "valid_with_warning"],
            "task_interpretation_status": [
                "interpreted",
                "interpreted_with_warning",
            ],
            "dataset_profile_status": ["profiled", "profiled_with_warning"],
            "workflow_plan_status": ["planned", "planned_with_warning"],
            "feature_engineering_status": ["completed", "completed_with_warning"],
            "requires_feature_engineering_artifact_path": True,
        },
    }

    if not preprocessing:
        return {
            **base,
            "status": "missing",
            "note": (
                "No FeaturePreprocessing record was found for this task_id. "
                "AI-guided data preprocessing evidence can be generated after "
                "the Feature Preprocessing module has run."
            ),
            "paper_relevance": _data_preprocessing_paper_relevance(),
            "excluded_from_evidence": _data_preprocessing_exclusions(),
        }

    preprocessing_json = _pick_dict(getattr(preprocessing, "preprocessing_json", None))
    preprocessing_plan = _first_non_empty_dict(
        getattr(preprocessing, "preprocessing_plan_json", None),
        preprocessing_json.get("preprocessing_plan"),
    )
    execution_report = _first_non_empty_dict(
        getattr(preprocessing, "execution_report_json", None),
        preprocessing_json.get("execution_report"),
    )
    removed_features = _extract_removed_features(
        _first_non_empty_dict(
            getattr(preprocessing, "removed_features_json", None),
            preprocessing_json.get("removed_features"),
        )
    )
    lineage_json = _first_non_empty_dict(
        getattr(preprocessing, "feature_lineage_json", None),
        preprocessing_json.get("feature_lineage"),
    )
    explainability_report = _first_non_empty_dict(
        getattr(preprocessing, "explainability_report_json", None),
        preprocessing_json.get("explainability_preservation_report"),
    )
    provenance = _first_non_empty_dict(
        getattr(preprocessing, "provenance_json", None),
        preprocessing_json.get("preprocessing_provenance"),
    )
    validation_summary = _pick_dict(preprocessing_json.get("validation_summary"))
    preprocessing_execution = _pick_dict(
        preprocessing_json.get("preprocessing_execution")
    )
    model_search_input = _pick_dict(preprocessing_json.get("model_search_input"))

    return {
        **base,
        "status": getattr(preprocessing, "status", None),
        "execution_summary": {
            "feature_preprocessing_record_present": True,
            "n_samples": _first_present(
                getattr(preprocessing, "n_samples", None),
                validation_summary.get("n_samples"),
            ),
            "n_raw_features": _first_present(
                getattr(preprocessing, "n_raw_features", None),
                validation_summary.get("n_raw_features"),
            ),
            "n_valid_features": _first_present(
                getattr(preprocessing, "n_valid_features", None),
                validation_summary.get("n_valid_features_before_preprocessing"),
            ),
            "n_final_features": _first_present(
                getattr(preprocessing, "n_final_features", None),
                validation_summary.get("n_features_after_preprocessing"),
            ),
            "n_dropped_features": _first_present(
                getattr(preprocessing, "n_dropped_features", None),
                validation_summary.get("n_dropped_features"),
                len(removed_features),
            ),
            "target_column": _first_present(
                getattr(preprocessing, "target_column", None),
                validation_summary.get("target_column"),
                model_search_input.get("target_column"),
            ),
            "is_ready_for_model_search": _first_present(
                getattr(preprocessing, "is_ready_for_model_search", None),
                model_search_input.get("ready_for_model_search"),
                validation_summary.get("is_model_ready"),
            ),
            "warnings": preprocessing_json.get("warnings", []),
            "errors": _first_present(
                preprocessing_json.get("errors"),
                [getattr(preprocessing, "error_message", None)]
                if getattr(preprocessing, "error_message", None)
                else [],
            ),
        },
        "llm_guided_preprocessing_plan": _summarize_preprocessing_plan(
            preprocessing_plan
        ),
        "planning_constraints_and_validation": {
            "schema_constrained_json": True,
            "registry_constrained_operations": True,
            "capability_registry_source": "app.shared.registry.fp_capability_registry",
            "hard_constraints": [
                "Use only capability_id values from the Feature Preprocessing Capability Registry.",
                "Use only capabilities with status='available'.",
                "Do not generate Python, SQL, or executable code.",
                "Every operation must include decision_rationale.",
                "operation.execution_scope must respect the capability fit_scope.",
                "target_column must be excluded from feature preprocessing.",
                "ID columns must be excluded or flagged.",
                "target-aware selection is disabled by default.",
            ],
            "operation_order_policy": [
                "leakage detection and target/ID exclusion",
                "missingness analysis",
                "low information filtering",
                "missing value imputation",
                "distribution transformation",
                "scaling or normalization",
                "correlation and collinearity handling",
                "feature selection",
                "feature group policies",
                "dimensionality reduction",
                "interpretability preservation",
                "artifact tracking",
            ],
            "auto_repair_rules": [
                "repair column action values accidentally used as feature-group policies",
                "repair feature-group policy values accidentally used as column actions",
                "replace null list fields with empty lists",
                "replace null parameter objects with empty dictionaries",
                "replace null nested model objects with empty dictionaries",
            ],
        },
        "fold_safe_execution_design": {
            "leakage_prevention": _pick_dict(
                _pick_dict(preprocessing_plan.get("global_policy")).get(
                    "leakage_prevention"
                )
            ),
            "execution_policy": [
                "dataset_profile_only operations may run in the global preprocessing phase",
                "fold_only operations are deferred and fit inside each CV fold",
                "imputation, scaling, transformation, feature selection, and dimensionality reduction must avoid full-data fitting for CV evaluation",
                "deferred operations are serialized into FoldPipelineSpec for Pipeline Execution",
            ],
            "fold_safe_deferred_summary": _pick_dict(
                preprocessing_execution.get("fold_safe_deferred")
            ),
        },
        "execution_report": _summarize_preprocessing_execution_report(
            execution_report
        ),
        "removed_features_summary": _summarize_removed_features(removed_features),
        "feature_lineage_and_explainability": {
            "feature_lineage_summary": _summarize_feature_lineage(
                _pick_dict(lineage_json.get("feature_lineage_map"))
            ),
            "feature_group_lineage_summary": _summarize_feature_group_lineage(
                _pick_dict(lineage_json.get("feature_group_lineage_map"))
            ),
            "explainability_preservation_report": _pick_keys(
                explainability_report,
                [
                    "total_original_features",
                    "total_retained_features",
                    "total_interpretable_features",
                    "total_reduced_features",
                    "interpretability_score",
                    "notes",
                ],
            ),
        },
        "model_ready_artifacts_and_downstream_interface": {
            "model_ready_artifact": {
                "artifact_id": _first_present(
                    getattr(preprocessing, "model_ready_artifact_id", None),
                    model_search_input.get("model_ready_artifact_id"),
                ),
                "path_recorded": bool(
                    _first_present(
                        getattr(preprocessing, "model_ready_artifact_path", None),
                        model_search_input.get("model_ready_matrix_path"),
                    )
                ),
                "path_excluded": bool(
                    _first_present(
                        getattr(preprocessing, "model_ready_artifact_path", None),
                        model_search_input.get("model_ready_matrix_path"),
                    )
                ),
            },
            "preprocessor_artifact": {
                "artifact_id": _first_present(
                    getattr(preprocessing, "preprocessor_artifact_id", None),
                    model_search_input.get("preprocessing_pipeline_artifact_id"),
                ),
                "path_recorded": bool(
                    getattr(preprocessing, "preprocessor_artifact_path", None)
                ),
                "path_excluded": bool(
                    getattr(preprocessing, "preprocessor_artifact_path", None)
                ),
            },
            "model_search_input": {
                "target_column": model_search_input.get("target_column"),
                "task_type": model_search_input.get("task_type"),
                "primary_metric": model_search_input.get("primary_metric"),
                "ready_for_model_search": model_search_input.get(
                    "ready_for_model_search"
                ),
                "feature_columns": _summarize_feature_columns(
                    model_search_input.get("feature_columns", [])
                ),
                "model_strategy": _pick_dict(model_search_input.get("model_strategy")),
                "validation_strategy": _pick_dict(
                    model_search_input.get("validation_strategy")
                ),
                "evaluation_strategy": _pick_dict(
                    model_search_input.get("evaluation_strategy")
                ),
                "hpo_strategy": _pick_dict(model_search_input.get("hpo_strategy")),
            },
        },
        "preprocessing_provenance": _summarize_preprocessing_provenance(
            provenance,
            getattr(preprocessing, "registry_snapshot_version", None),
        ),
        "paper_relevance": _data_preprocessing_paper_relevance(),
        "excluded_from_evidence": _data_preprocessing_exclusions(),
    }


def _build_model_search_plan_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    model_search_context = ModelSearchContextRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Model Search Planning and Strategy Adjustment",
        "role_in_system": (
            "Convert the model-ready dataset and workflow-level strategy into "
            "a validated model search plan containing candidate models, HPO "
            "budget allocation, search spaces, validation design, evaluation "
            "metrics, and pipeline-generation inputs."
        ),
        "source_traceability": {
            "record_source": "model_search_context table latest row by task_id",
            "full_json_source": "model_search_context.context_json",
            "llm_json_sources_excluded": [
                "model_search_context.llm_request_json",
                "model_search_context.llm_response_json",
            ],
            "implementation_sources": [
                "app.modules.model_search_context.context_builder",
                "app.modules.model_search_context.dataset_profile_analyzer",
                "app.modules.model_search_context.feature_group_analyzer",
                "app.modules.model_search_context.preprocessing_analyzer",
                "app.modules.model_search_context.llm_context_builder",
                "app.modules.model_search_context.llm_strategy_advisor",
                "app.modules.model_search_context.llm_advice_validator",
                "app.modules.model_search_context.strategy_merger",
                "app.modules.model_search_context.candidate_model_selector",
                "app.modules.model_search_context.search_space_builder",
                "app.modules.model_search_context.builder",
                "app.shared.registry.model_registry",
                "app.shared.registry.hpo_registry",
            ],
        },
        "upstream_readiness_gates": {
            "task_specification_status": ["valid", "valid_with_warning"],
            "task_interpretation_status": [
                "interpreted",
                "interpreted_with_warning",
            ],
            "dataset_profile_status": ["profiled", "profiled_with_warning"],
            "workflow_plan_status": ["planned", "planned_with_warning"],
            "feature_engineering_status": ["completed", "completed_with_warning"],
            "feature_preprocessing_status": [
                "preprocessed",
                "preprocessed_with_warning",
                "success",
            ],
            "requires_ready_for_model_search": True,
        },
    }

    if not model_search_context:
        return {
            **base,
            "status": "missing",
            "note": (
                "No ModelSearchContext record was found for this task_id. "
                "Model search plan evidence can be generated after the Model "
                "Search Context module has run."
            ),
            "paper_relevance": _model_search_plan_paper_relevance(),
            "excluded_from_evidence": _model_search_plan_exclusions(),
        }

    context_json = _pick_dict(getattr(model_search_context, "context_json", None))
    dataset_profile = _pick_dict(context_json.get("dataset_effective_profile"))
    feature_group_summary = _pick_dict(context_json.get("feature_group_summary"))
    preprocessing_summary = _pick_dict(context_json.get("preprocessing_summary"))
    llm_advice = _pick_dict(context_json.get("llm_strategy_advice"))
    system_validation = _pick_dict(context_json.get("system_validation_result"))
    strategy_adjustment = _pick_dict(context_json.get("strategy_adjustment"))
    model_search_input = _pick_dict(context_json.get("model_search_context_input"))
    candidate_model_plan = _pick_dict(context_json.get("candidate_model_plan"))
    hpo_plan = _pick_dict(context_json.get("hpo_plan"))
    search_space_plan = _pick_dict(context_json.get("search_space_plan"))
    validation_plan = _pick_dict(context_json.get("validation_plan"))
    evaluation_plan = _pick_dict(context_json.get("evaluation_plan"))
    pipeline_input = _pick_dict(context_json.get("pipeline_generation_input"))
    strategy_changes = context_json.get("strategy_changes", [])

    return {
        **base,
        "status": getattr(model_search_context, "status", None),
        "execution_summary": {
            "model_search_context_record_present": True,
            "update_mode": _first_present(
                getattr(model_search_context, "update_mode", None),
                context_json.get("update_mode"),
            ),
            "task_type": _first_present(
                getattr(model_search_context, "task_type", None),
                model_search_input.get("task_type"),
                dataset_profile.get("task_type"),
            ),
            "target_column": _first_present(
                getattr(model_search_context, "target_column", None),
                model_search_input.get("target_column"),
                dataset_profile.get("target_column"),
            ),
            "primary_metric": _first_present(
                getattr(model_search_context, "primary_metric", None),
                model_search_input.get("primary_metric"),
                evaluation_plan.get("primary_metric"),
            ),
            "n_samples": _first_present(
                getattr(model_search_context, "n_samples", None),
                dataset_profile.get("n_samples"),
            ),
            "n_final_features": _first_present(
                getattr(model_search_context, "n_final_features", None),
                dataset_profile.get("n_final_features"),
            ),
            "n_candidate_models": _first_present(
                getattr(model_search_context, "n_candidate_models", None),
                _count_candidate_models(candidate_model_plan),
            ),
            "hpo_enabled": _first_present(
                getattr(model_search_context, "hpo_enabled", None),
                hpo_plan.get("enabled"),
            ),
            "hpo_method": _first_present(
                getattr(model_search_context, "hpo_method", None),
                hpo_plan.get("search_method"),
            ),
            "max_total_trials": _first_present(
                getattr(model_search_context, "max_total_trials", None),
                hpo_plan.get("max_total_trials"),
            ),
            "llm_used": getattr(model_search_context, "llm_used", None),
            "llm_confidence_score": _first_present(
                getattr(model_search_context, "llm_confidence_score", None),
                context_json.get("confidence_score"),
                llm_advice.get("confidence_score"),
            ),
            "ready_for_pipeline_generation": _first_present(
                getattr(model_search_context, "ready_for_pipeline_generation", None),
                pipeline_input.get("ready_for_pipeline_generation"),
                model_search_input.get("ready_for_pipeline_generation"),
            ),
            "warnings": context_json.get("warnings", []),
            "errors": _first_present(
                context_json.get("errors"),
                [getattr(model_search_context, "error_message", None)]
                if getattr(model_search_context, "error_message", None)
                else [],
            ),
        },
        "effective_dataset_profile": {
            **_pick_keys(
                dataset_profile,
                [
                    "n_samples",
                    "n_raw_features",
                    "n_final_features",
                    "n_dropped_features",
                    "feature_reduction_ratio",
                    "target_column",
                    "task_type",
                ],
            ),
            "derived_flags": {
                "is_small_sample": (
                    dataset_profile.get("n_samples", 0) < 200
                    if dataset_profile.get("n_samples") is not None
                    else None
                ),
                "is_low_feature": (
                    dataset_profile.get("n_final_features", 0) < 20
                    if dataset_profile.get("n_final_features") is not None
                    else None
                ),
                "is_high_reduction": (
                    dataset_profile.get("feature_reduction_ratio", 0) > 0.8
                    if dataset_profile.get("feature_reduction_ratio") is not None
                    else None
                ),
            },
        },
        "feature_and_preprocessing_signals": {
            "feature_group_summary": _pick_keys(
                feature_group_summary,
                [
                    "retained_groups",
                    "dropped_groups",
                    "partially_retained_groups",
                    "low_effective_feature_warning",
                ],
            ),
            "preprocessing_summary": _pick_keys(
                preprocessing_summary,
                [
                    "imputation_executed",
                    "scaling_executed",
                    "feature_selection_executed",
                    "categorical_encoding_executed",
                    "preprocessing_pipeline_artifact_id",
                    "imputation_execution_mode",
                    "scaling_execution_mode",
                    "feature_selection_execution_mode",
                    "fold_safe_deferred",
                ],
            ),
        },
        "llm_strategy_advice_summary": _summarize_model_search_llm_advice(
            llm_advice
        ),
        "llm_advice_validation": {
            "system_validation_result": _pick_keys(
                system_validation,
                ["is_valid", "rejected_suggestions", "fallback_applied"],
            ),
            "validation_rules": [
                "model families must exist in the Model Registry",
                "HPO methods must exist in the HPO Registry",
                "baseline_models must contain exactly one baseline",
                "max_trials is clamped by system configuration",
                "split_strategy must be a supported validation strategy",
                "search_space_width must be narrow, moderate, or wide",
                "model display names may be resolved to registry family keys",
            ],
        },
        "strategy_adjustment": {
            "adjustment_flags": _pick_keys(
                strategy_adjustment,
                [
                    "model_strategy_adjusted",
                    "hpo_strategy_adjusted",
                    "validation_strategy_adjusted",
                    "evaluation_strategy_adjusted",
                    "adjustment_reasons",
                ],
            ),
            "strategy_change_summary": context_json.get("strategy_change_summary"),
            "strategy_changes": _summarize_strategy_changes(strategy_changes),
        },
        "candidate_model_plan": _summarize_candidate_model_plan(
            candidate_model_plan
        ),
        "hpo_plan": _summarize_model_search_hpo_plan(hpo_plan),
        "search_space_plan": _summarize_search_space_plan(search_space_plan),
        "validation_and_evaluation_plan": {
            "validation_plan": _pick_keys(
                validation_plan,
                [
                    "split_strategy",
                    "n_splits",
                    "random_state",
                    "shuffle",
                    "stratification_required",
                    "benchmark_split",
                ],
            ),
            "evaluation_plan": _pick_keys(
                evaluation_plan,
                [
                    "primary_metric",
                    "metric_direction",
                    "secondary_metrics",
                    "scorer_id",
                ],
            ),
        },
        "pipeline_generation_interface": {
            "ready_for_pipeline_generation": pipeline_input.get(
                "ready_for_pipeline_generation"
            ),
            "target_column": pipeline_input.get("target_column"),
            "feature_columns": _summarize_feature_columns(
                pipeline_input.get("feature_columns", [])
            ),
            "model_ready_matrix_path_recorded": bool(
                pipeline_input.get("model_ready_matrix_path")
                or model_search_input.get("model_ready_matrix_path")
            ),
            "model_ready_matrix_path_excluded": bool(
                pipeline_input.get("model_ready_matrix_path")
                or model_search_input.get("model_ready_matrix_path")
            ),
            "preprocessing_pipeline_artifact_id": _first_present(
                pipeline_input.get("preprocessing_pipeline_artifact_id"),
                model_search_input.get("preprocessing_pipeline_artifact_id"),
            ),
            "contains_candidate_model_plan": bool(
                pipeline_input.get("candidate_model_plan")
            ),
            "contains_hpo_plan": bool(pipeline_input.get("hpo_plan")),
            "contains_search_space_plan": bool(
                pipeline_input.get("search_space_plan")
            ),
            "contains_validation_plan": bool(pipeline_input.get("validation_plan")),
            "contains_evaluation_plan": bool(pipeline_input.get("evaluation_plan")),
        },
        "paper_relevance": _model_search_plan_paper_relevance(),
        "excluded_from_evidence": _model_search_plan_exclusions(),
    }


def _build_executable_pipeline_generation_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    pipeline_generation = PipelineGenerationRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Executable Pipeline Specification Generation",
        "role_in_system": (
            "Transform the model search plan into declarative, registry-bound, "
            "validated, safety-checked pipeline specifications and execution "
            "input for the downstream Pipeline Execution module."
        ),
        "source_traceability": {
            "record_source": "pipeline_generation table latest row by task_id",
            "full_json_source": "pipeline_generation.pipeline_json",
            "execution_input_source": "pipeline_generation.execution_input_json",
            "llm_json_sources_excluded": [
                "pipeline_generation.llm_request_json",
                "pipeline_generation.llm_response_json",
            ],
            "implementation_sources": [
                "app.modules.pipeline_generation.context_builder",
                "app.modules.pipeline_generation.artifact_resolver",
                "app.modules.pipeline_generation.component_binder",
                "app.modules.pipeline_generation.pipeline_spec_builder",
                "app.modules.pipeline_generation.trial_plan_builder",
                "app.modules.pipeline_generation.pipeline_validator",
                "app.modules.pipeline_generation.safety_checker",
                "app.modules.pipeline_generation.llm_review_prompt_builder",
                "app.modules.pipeline_generation.llm_review_validator",
                "app.modules.pipeline_generation.llm_review_normalizer",
                "app.modules.pipeline_generation.execution_input_builder",
                "app.modules.pipeline_generation.builder",
            ],
        },
        "upstream_readiness_gates": {
            "model_search_context_status": ["updated", "updated_with_warning"],
            "requires_ready_for_pipeline_generation": True,
            "requires_pipeline_generation_input": True,
            "requires_model_ready_matrix_path": True,
            "feature_preprocessing_artifact_optional_but_supported": True,
        },
    }

    if not pipeline_generation:
        return {
            **base,
            "status": "missing",
            "note": (
                "No PipelineGeneration record was found for this task_id. "
                "Executable pipeline generation evidence can be generated after "
                "the Pipeline Generation module has run."
            ),
            "paper_relevance": _pipeline_generation_paper_relevance(),
            "excluded_from_evidence": _pipeline_generation_exclusions(),
        }

    pipeline_json = _pick_dict(getattr(pipeline_generation, "pipeline_json", None))
    execution_input = _first_non_empty_dict(
        getattr(pipeline_generation, "execution_input_json", None),
        pipeline_json.get("execution_input"),
    )
    pipeline_bundle = _pick_dict(pipeline_json.get("pipeline_bundle"))
    pipeline_specs = _first_non_empty_list(
        pipeline_json.get("pipeline_specs"),
        pipeline_bundle.get("pipeline_specs"),
        execution_input.get("pipeline_specs"),
    )
    trial_plan = _first_non_empty_dict(
        pipeline_json.get("trial_plan"),
        pipeline_bundle.get("trial_plan"),
        execution_input.get("trial_plan"),
    )
    component_binding = _pick_dict(pipeline_json.get("component_binding_result"))
    artifact_manifest = _pick_dict(pipeline_json.get("artifact_manifest"))
    validation_result = _pick_dict(pipeline_json.get("pipeline_validation_result"))
    safety_result = _pick_dict(pipeline_json.get("safety_check_result"))
    llm_review = _pick_dict(pipeline_json.get("llm_advisory_review"))

    return {
        **base,
        "status": getattr(pipeline_generation, "status", None),
        "execution_summary": {
            "pipeline_generation_record_present": True,
            "generation_mode": _first_present(
                getattr(pipeline_generation, "generation_mode", None),
                pipeline_json.get("generation_mode"),
            ),
            "task_type": _first_present(
                getattr(pipeline_generation, "task_type", None),
                pipeline_bundle.get("task_type"),
                execution_input.get("task_type"),
            ),
            "target_column": _first_present(
                getattr(pipeline_generation, "target_column", None),
                pipeline_bundle.get("target_column"),
                execution_input.get("target_column"),
            ),
            "primary_metric": _first_present(
                getattr(pipeline_generation, "primary_metric", None),
                pipeline_bundle.get("primary_metric"),
                _pick_dict(pipeline_bundle.get("evaluation_plan")).get("primary_metric"),
                _pick_dict(execution_input.get("evaluation_plan")).get("primary_metric"),
            ),
            "n_pipeline_specs": _first_present(
                getattr(pipeline_generation, "n_pipeline_specs", None),
                pipeline_json.get("n_pipeline_specs"),
                len(pipeline_specs),
            ),
            "n_baseline_specs": _first_present(
                getattr(pipeline_generation, "n_baseline_specs", None),
                pipeline_json.get("n_baseline_specs"),
                _count_pipeline_specs_by_role(pipeline_specs, "baseline"),
            ),
            "n_hpo_specs": _first_present(
                getattr(pipeline_generation, "n_hpo_specs", None),
                pipeline_json.get("n_hpo_specs"),
                _count_hpo_pipeline_specs(pipeline_specs),
            ),
            "hpo_enabled": _first_present(
                getattr(pipeline_generation, "hpo_enabled", None),
                trial_plan.get("hpo_enabled"),
                _pick_dict(pipeline_bundle.get("hpo_plan")).get("enabled"),
            ),
            "ready_for_execution": _first_present(
                getattr(pipeline_generation, "ready_for_execution", None),
                pipeline_json.get("ready_for_execution"),
                execution_input.get("ready_for_execution"),
            ),
            "llm_review_used": getattr(pipeline_generation, "llm_review_used", None),
            "llm_confidence_score": getattr(
                pipeline_generation,
                "llm_confidence_score",
                None,
            ),
            "warnings": pipeline_json.get("warnings", []),
            "error_message": _first_present(
                getattr(pipeline_generation, "error_message", None),
                pipeline_json.get("error_message"),
            ),
        },
        "artifact_resolution": _summarize_pipeline_artifact_manifest(
            artifact_manifest
        ),
        "component_binding": _summarize_component_binding(component_binding),
        "pipeline_spec_generation": {
            "spec_counts": {
                "total": len(pipeline_specs),
                "baseline": _count_pipeline_specs_by_role(
                    pipeline_specs,
                    "baseline",
                ),
                "hpo_candidate": _count_pipeline_specs_by_role(
                    pipeline_specs,
                    "hpo_candidate",
                ),
                "candidate": _count_pipeline_specs_by_role(
                    pipeline_specs,
                    "candidate",
                ),
                "hpo_enabled": _count_hpo_pipeline_specs(pipeline_specs),
            },
            "pipeline_specs": _summarize_pipeline_specs(pipeline_specs),
            "generation_policy": [
                "baseline models are generated as single-run non-HPO specs",
                "candidate models with HPO enabled receive search_space_ref and search_space",
                "each spec binds registered model metadata, artifact references, validation plan, evaluation plan, and safety constraints",
                "execution_ready is true only when the model is registered and required data fields/artifacts are present",
            ],
        },
        "trial_plan": _summarize_pipeline_trial_plan(trial_plan),
        "pipeline_validation": _pick_keys(
            validation_result,
            [
                "is_valid",
                "structure_valid",
                "registry_valid",
                "artifact_valid",
                "task_type_compatible",
                "search_space_valid",
                "trial_valid",
                "data_fields_valid",
                "execution_input_valid",
                "errors",
                "warnings",
            ],
        ),
        "safety_check": _summarize_pipeline_safety_check(safety_result),
        "llm_advisory_review": _summarize_pipeline_llm_review(llm_review),
        "execution_input": _summarize_pipeline_execution_input(execution_input),
        "paper_relevance": _pipeline_generation_paper_relevance(),
        "excluded_from_evidence": _pipeline_generation_exclusions(),
    }


def _build_pipeline_execution_and_training_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    pipeline_execution = PipelineExecutionRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Pipeline Execution and Controlled Model Training",
        "role_in_system": (
            "Consume the validated execution input from Pipeline Generation, "
            "load the model-ready matrix, create validation splits, expand "
            "pipeline specifications into trials, execute controlled fold-level "
            "training, persist artifacts, and produce the structured handoff "
            "for Metric Evaluation."
        ),
        "source_traceability": {
            "record_source": "pipeline_execution table latest row by task_id",
            "full_json_source": "pipeline_execution.execution_json",
            "metric_handoff_source": "pipeline_execution.metric_evaluation_input_json",
            "runtime_log_source": "pipeline_execution.runtime_log_json",
            "implementation_sources": [
                "app.modules.pipeline_execution.context_builder",
                "app.modules.pipeline_execution.execution_input_loader",
                "app.modules.pipeline_execution.data_matrix_loader",
                "app.modules.pipeline_execution.validation_splitter",
                "app.modules.pipeline_execution.execution_planner",
                "app.modules.pipeline_execution.controlled_executor",
                "app.modules.pipeline_execution.trial_runner",
                "app.modules.pipeline_execution.fold_runner",
                "app.modules.pipeline_execution.fold_preprocessor",
                "app.modules.pipeline_execution.model_factory",
                "app.modules.pipeline_execution.hpo_trial_generator",
                "app.modules.pipeline_execution.metric_input_builder",
                "app.modules.pipeline_execution.training_artifact_manager",
                "app.modules.pipeline_execution.runtime_monitor",
                "app.modules.pipeline_execution.execution_state_tracker",
            ],
        },
        "upstream_readiness_gates": {
            "pipeline_generation_status": [
                "generated",
                "generated_with_warning",
            ],
            "requires_pipeline_generation_ready_for_execution": True,
            "requires_execution_input_json": True,
            "requires_non_empty_pipeline_specs": True,
            "requires_each_pipeline_spec_execution_ready": True,
        },
    }

    if not pipeline_execution:
        return {
            **base,
            "status": "missing",
            "note": (
                "No PipelineExecution record was found for this task_id. "
                "Pipeline execution and training evidence can be generated "
                "after the Pipeline Execution module has run."
            ),
            "paper_relevance": _pipeline_execution_paper_relevance(),
            "excluded_from_evidence": _pipeline_execution_exclusions(),
        }

    execution_json = _pick_dict(getattr(pipeline_execution, "execution_json", None))
    metric_input = _first_non_empty_dict(
        getattr(pipeline_execution, "metric_evaluation_input_json", None),
        execution_json.get("metric_evaluation_input"),
    )
    runtime_log = _pick_dict(getattr(pipeline_execution, "runtime_log_json", None))
    execution_summary = _pick_dict(execution_json.get("execution_summary"))
    pipeline_runs = execution_json.get("pipeline_run_results", [])
    trial_results = execution_json.get("trial_results", [])
    artifact_manifest = _pick_dict(execution_json.get("training_artifact_manifest"))
    runtime_environment = _first_non_empty_dict(
        execution_json.get("runtime_environment"),
        runtime_log.get("environment"),
    )

    return {
        **base,
        "status": getattr(pipeline_execution, "status", None),
        "execution_summary": {
            "pipeline_execution_record_present": True,
            "execution_mode": _first_present(
                getattr(pipeline_execution, "execution_mode", None),
                execution_json.get("execution_mode"),
                execution_summary.get("execution_mode"),
            ),
            "task_type": _first_present(
                getattr(pipeline_execution, "task_type", None),
                metric_input.get("task_type"),
            ),
            "target_column": _first_present(
                getattr(pipeline_execution, "target_column", None),
                metric_input.get("target_column"),
            ),
            "primary_metric": _first_present(
                getattr(pipeline_execution, "primary_metric", None),
                metric_input.get("primary_metric"),
            ),
            "n_pipeline_specs": _first_present(
                getattr(pipeline_execution, "n_pipeline_specs", None),
                execution_json.get("n_pipeline_specs"),
                execution_summary.get("n_pipeline_specs"),
            ),
            "n_trials_planned": _first_present(
                getattr(pipeline_execution, "n_trials_planned", None),
                execution_json.get("n_trials_planned"),
                execution_summary.get("n_trials_planned"),
            ),
            "n_trials_completed": _first_present(
                getattr(pipeline_execution, "n_trials_completed", None),
                execution_json.get("n_trials_completed"),
                execution_summary.get("n_trials_completed"),
            ),
            "n_trials_failed": _first_present(
                getattr(pipeline_execution, "n_trials_failed", None),
                execution_json.get("n_trials_failed"),
                execution_summary.get("n_trials_failed"),
            ),
            "n_models_trained": _first_present(
                getattr(pipeline_execution, "n_models_trained", None),
                execution_json.get("n_models_trained"),
                execution_summary.get("n_models_trained"),
            ),
            "duration_seconds": _first_present(
                execution_json.get("duration_seconds"),
                execution_summary.get("duration_seconds"),
                runtime_log.get("duration_seconds"),
            ),
            "ready_for_metric_evaluation": _first_present(
                getattr(pipeline_execution, "ready_for_metric_evaluation", None),
                execution_json.get("ready_for_metric_evaluation"),
                metric_input.get("ready_for_metric_evaluation"),
            ),
            "warnings": execution_json.get("warnings", []),
            "error_message": _first_present(
                getattr(pipeline_execution, "error_message", None),
                execution_json.get("error_message"),
                runtime_log.get("error_message"),
            ),
        },
        "execution_input_validation": {
            "required_fields": [
                "pipeline_generation_id",
                "task_id",
                "pipeline_specs",
                "validation_plan.split_strategy",
                "evaluation_plan.primary_metric",
                "feature_columns",
                "target_column",
                "trial_plan",
                "ready_for_execution",
            ],
            "per_spec_requirements": [
                "pipeline_spec_id",
                "model_id",
                "execution_ready=true",
            ],
            "metric_direction_handling": (
                "If metric_direction is missing but primary_metric exists, "
                "the service infers direction from the Metric Registry."
            ),
        },
        "data_loading_and_validation": {
            "model_ready_matrix_path_recorded": bool(
                metric_input.get("model_ready_matrix_path")
            ),
            "model_ready_matrix_path_excluded": bool(
                metric_input.get("model_ready_matrix_path")
            ),
            "path_safety_checks": [
                "model-ready matrix path must be non-empty",
                "parent-directory traversal is rejected",
                "model-ready matrix must exist",
                "only parquet input is accepted",
            ],
            "data_checks": [
                "feature columns must exist in the loaded matrix",
                "target column must exist",
                "target column must not contain NaN values",
                "X and y sample counts must match",
                "data matrix must contain at least one sample",
            ],
            "feature_columns": _summarize_feature_columns(
                metric_input.get("feature_columns", [])
            ),
        },
        "fold_safe_preprocessing_execution": {
            "design": [
                "optional fold_pipeline_spec is loaded next to the model-ready matrix",
                "fold-level preprocessing is fit on X_train only inside each fold",
                "the fitted fold preprocessor transforms X_val after train-only fitting",
                "this prevents validation fold statistics from leaking into preprocessing",
            ],
            "supported_fold_operations": [
                "imputation",
                "scaling",
                "distribution transforms",
                "feature selection",
                "PCA",
                "truncated SVD",
                "missing indicators",
            ],
            "fold_pipeline_spec_path_recorded": bool(
                metric_input.get("fold_pipeline_spec_path")
            ),
            "fold_pipeline_spec_path_excluded": bool(
                metric_input.get("fold_pipeline_spec_path")
            ),
            "evidence_from_trial_results": _summarize_fold_preprocessing_evidence(
                trial_results
            ),
        },
        "validation_split_plan": {
            "validation_plan": _pick_dict(metric_input.get("validation_plan")),
            "supported_strategies": [
                "train_test_split",
                "holdout",
                "k_fold_cross_validation",
                "k_fold",
                "stratified_k_fold",
                "repeated_cv",
                "repeated_k_fold",
            ],
            "actual_fold_summary": _summarize_actual_folds(trial_results),
            "train_validation_indices_excluded": True,
        },
        "execution_plan_expansion": {
            "expansion_rules": [
                "baseline specs expand to exactly one fixed-parameter trial",
                "fixed-parameter candidates expand to one trial",
                "HPO candidates expand to multiple trials from search_space and trial allocation",
                "max_trials_override can only reduce trial count",
                "execution_ready=false specs are skipped",
            ],
            "hpo_generation_methods": [
                "random_search",
                "grid_search",
                "bayesian_optimization via Optuna TPE when available",
                "Latin Hypercube Sampling fallback for bayesian_optimization",
                "Optuna TPE for optuna_tpe and successive_halving when available",
            ],
            "trial_type_counts": _count_by_key(
                [t for t in trial_results if isinstance(t, dict)],
                "trial_type",
            ),
            "trial_model_counts": _count_by_key(
                [t for t in trial_results if isinstance(t, dict)],
                "model_id",
            ),
        },
        "controlled_training_execution": {
            "execution_policy": [
                "controlled_executor is the only training entry point",
                "sequential mode runs one trial at a time",
                "limited_parallel mode uses ThreadPoolExecutor with bounded workers",
                "fold execution may run in parallel within sequential trial mode",
                "fail_fast stops after first failed trial when enabled",
                "max_runtime_seconds cooperatively skips remaining trials",
                "per-fold model.fit timeout marks the fold failed",
            ],
            "pipeline_run_results": _summarize_pipeline_run_results(pipeline_runs),
            "trial_results_summary": _summarize_training_trial_results(trial_results),
        },
        "safe_model_instantiation": {
            "model_factory_policy": [
                "models are instantiated only through explicit registry-backed factory mappings",
                "dynamic imports, eval, and user-supplied class names are not used",
                "task_type compatibility is checked before instantiation",
                "missing optional dependencies fail as controlled model-instantiation errors",
                "xgboost and lightgbm are optional explicit try-import mappings",
            ],
        },
        "artifact_management": _summarize_training_artifact_manifest(
            artifact_manifest
        ),
        "runtime_environment_and_logs": {
            "runtime_environment": _pick_keys(
                runtime_environment,
                [
                    "python_version",
                    "platform",
                    "scikit_learn_version",
                    "pandas_version",
                    "numpy_version",
                    "joblib_version",
                ],
            ),
            "runtime_log_summary": _summarize_runtime_log(runtime_log),
        },
        "metric_evaluation_handoff": _summarize_metric_evaluation_handoff(
            metric_input
        ),
        "paper_relevance": _pipeline_execution_paper_relevance(),
        "excluded_from_evidence": _pipeline_execution_exclusions(),
    }


def _build_metric_evaluation_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    metric_evaluation = MetricEvaluationRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Metric Evaluation and Model Ranking",
        "role_in_system": (
            "Consume the structured handoff from Pipeline Execution, reload "
            "prediction artifacts, compute task-appropriate fold metrics, "
            "aggregate trial and model performance, rank models, compare "
            "against baselines, validate metric consistency, and prepare the "
            "structured input for Result Diagnosis."
        ),
        "source_traceability": {
            "record_source": "metric_evaluation table latest row by task_id",
            "full_json_source": "metric_evaluation.evaluation_json",
            "metric_summary_source": "metric_evaluation.metric_summary_json",
            "model_ranking_source": "metric_evaluation.model_ranking_json",
            "diagnosis_handoff_source": (
                "metric_evaluation.result_diagnosis_input_json"
            ),
            "implementation_sources": [
                "app.modules.metric_evaluation.context_builder",
                "app.modules.metric_evaluation.metric_input_loader",
                "app.modules.metric_evaluation.prediction_artifact_loader",
                "app.modules.metric_evaluation.fold_metric_evaluator",
                "app.modules.metric_evaluation.metric_calculator",
                "app.modules.metric_evaluation.trial_metric_aggregator",
                "app.modules.metric_evaluation.pipeline_metric_aggregator",
                "app.modules.metric_evaluation.model_ranker",
                "app.modules.metric_evaluation.baseline_comparator",
                "app.modules.metric_evaluation.metric_validator",
                "app.modules.metric_evaluation.result_diagnosis_input_builder",
            ],
        },
        "upstream_readiness_gates": {
            "pipeline_execution_status": [
                "completed",
                "completed_with_warning",
                "partially_failed",
            ],
            "requires_pipeline_execution_ready_for_metric_evaluation": True,
            "requires_metric_evaluation_input_json": True,
            "requires_completed_trial": True,
            "requires_prediction_artifact": True,
        },
    }

    if not metric_evaluation:
        return {
            **base,
            "status": "missing",
            "note": (
                "No MetricEvaluation record was found for this task_id. "
                "Metric evaluation evidence can be generated after the Metric "
                "Evaluation module has run."
            ),
            "paper_relevance": _metric_evaluation_paper_relevance(),
            "excluded_from_evidence": _metric_evaluation_exclusions(),
        }

    evaluation_json = _pick_dict(getattr(metric_evaluation, "evaluation_json", None))
    result_diagnosis_input = _first_non_empty_dict(
        getattr(metric_evaluation, "result_diagnosis_input_json", None),
        evaluation_json.get("result_diagnosis_input"),
    )
    metric_summary = _first_non_empty_dict(
        getattr(metric_evaluation, "metric_summary_json", None),
        evaluation_json.get("metric_summary"),
        result_diagnosis_input.get("metric_summary"),
    )
    model_ranking = _first_non_empty_list(
        getattr(metric_evaluation, "model_ranking_json", None),
        evaluation_json.get("model_ranking"),
        result_diagnosis_input.get("model_ranking"),
    )
    trial_results = evaluation_json.get("trial_metric_results", [])
    pipeline_results = evaluation_json.get("pipeline_metric_results", [])
    fold_results = evaluation_json.get("fold_metric_results", [])
    baseline_comparison = _first_non_empty_dict(
        evaluation_json.get("baseline_comparison"),
        result_diagnosis_input.get("baseline_comparison"),
    )
    metric_validation = _pick_dict(evaluation_json.get("metric_validation_result"))
    artifact_manifest = _pick_dict(evaluation_json.get("evaluation_artifact_manifest"))

    return {
        **base,
        "status": getattr(metric_evaluation, "status", None),
        "evaluation_summary": {
            "metric_evaluation_record_present": True,
            "task_type": _first_present(
                getattr(metric_evaluation, "task_type", None),
                evaluation_json.get("task_type"),
                result_diagnosis_input.get("task_type"),
            ),
            "target_column": getattr(metric_evaluation, "target_column", None),
            "primary_metric": _first_present(
                getattr(metric_evaluation, "primary_metric", None),
                evaluation_json.get("primary_metric"),
                metric_summary.get("primary_metric"),
            ),
            "metric_direction": _first_present(
                getattr(metric_evaluation, "metric_direction", None),
                evaluation_json.get("metric_direction"),
                metric_summary.get("metric_direction"),
            ),
            "n_trials_evaluated": _first_present(
                getattr(metric_evaluation, "n_trials_evaluated", None),
                evaluation_json.get("n_trials_evaluated"),
            ),
            "n_trials_failed": _first_present(
                getattr(metric_evaluation, "n_trials_failed", None),
                evaluation_json.get("n_trials_failed"),
            ),
            "n_models_evaluated": _first_present(
                getattr(metric_evaluation, "n_models_evaluated", None),
                evaluation_json.get("n_models_evaluated"),
            ),
            "best_trial_id": getattr(metric_evaluation, "best_trial_id", None),
            "best_model_id": getattr(metric_evaluation, "best_model_id", None),
            "best_pipeline_spec_id": getattr(
                metric_evaluation,
                "best_pipeline_spec_id",
                None,
            ),
            "best_primary_metric_value": getattr(
                metric_evaluation,
                "best_primary_metric_value",
                None,
            ),
            "ready_for_result_diagnosis": _first_present(
                getattr(metric_evaluation, "ready_for_result_diagnosis", None),
                evaluation_json.get("ready_for_result_diagnosis"),
                result_diagnosis_input.get("ready_for_result_diagnosis"),
            ),
            "warnings": evaluation_json.get("warnings", []),
            "error_message": _first_present(
                getattr(metric_evaluation, "error_message", None),
                evaluation_json.get("error_message"),
            ),
        },
        "metric_input_validation": {
            "required_input_fields": [
                "task_type",
                "target_column",
                "primary_metric",
                "metric_direction",
                "evaluation_plan",
                "trial_results",
                "prediction_artifacts",
            ],
            "accepted_task_types": ["regression", "classification"],
            "accepted_metric_directions": ["minimize", "maximize"],
            "requires_non_empty_trial_results": True,
            "requires_at_least_one_completed_trial": True,
            "requires_non_empty_prediction_artifacts": True,
            "metric_direction_cross_checked_against_registry": True,
            "artifact_paths_excluded": True,
        },
        "metric_computation_protocol": {
            "supported_regression_metrics": ["MAE", "MSE", "RMSE", "R2", "MAPE"],
            "supported_classification_metrics": [
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
                "ROC_AUC",
            ],
            "default_regression_metrics": ["MAE", "MSE", "RMSE", "R2"],
            "default_classification_metrics": [
                "Accuracy",
                "Precision",
                "Recall",
                "F1",
            ],
            "metric_name_normalization": (
                "Hyphenated metric names such as ROC-AUC are canonicalized "
                "to underscore form before registry lookup and calculation."
            ),
            "direction_correction": (
                "If persisted metric_direction contradicts the registry "
                "direction for the primary metric, the service overrides it "
                "before ranking."
            ),
            "calculation_granularity": [
                "prediction artifact",
                "fold",
                "trial",
                "pipeline/model",
            ],
        },
        "fold_level_metric_evaluation": _summarize_fold_metric_results(
            fold_results
        ),
        "trial_level_aggregation": _summarize_trial_metric_results(
            trial_results
        ),
        "pipeline_model_aggregation": _summarize_pipeline_metric_results(
            pipeline_results
        ),
        "model_ranking_and_best_selection": {
            "ranking_policy": [
                "minimize metrics are sorted ascending",
                "maximize metrics are sorted descending",
                "primary_metric_std is used as the secondary stability tie-breaker",
                "best trial determines best_model_id and best_pipeline_spec_id",
            ],
            "metric_summary": _pick_keys(
                metric_summary,
                [
                    "primary_metric",
                    "metric_direction",
                    "best_metric_value",
                    "worst_metric_value",
                    "mean_metric_value",
                    "std_metric_value",
                    "n_trials_contributing",
                    "n_models_contributing",
                ],
            ),
            "ranking": _summarize_model_ranking(model_ranking),
        },
        "baseline_comparison": _summarize_baseline_comparison(
            baseline_comparison
        ),
        "metric_validation": _summarize_metric_validation(metric_validation),
        "result_diagnosis_handoff": _summarize_result_diagnosis_handoff(
            result_diagnosis_input
        ),
        "artifact_management": {
            "evaluation_artifact_dir_recorded": bool(
                getattr(metric_evaluation, "evaluation_artifact_dir", None)
            ),
            "evaluation_artifact_dir_excluded": bool(
                getattr(metric_evaluation, "evaluation_artifact_dir", None)
            ),
            "manifest_saved": bool(artifact_manifest.get("manifest_path")),
            "metric_results_saved": bool(
                artifact_manifest.get("metric_results_path")
            ),
            "fold_metrics_saved": bool(artifact_manifest.get("fold_metrics_path")),
            "trial_metrics_saved": bool(
                artifact_manifest.get("trial_metrics_path")
            ),
            "pipeline_metrics_saved": bool(
                artifact_manifest.get("pipeline_metrics_path")
            ),
            "model_ranking_saved": bool(
                artifact_manifest.get("model_ranking_path")
            ),
            "baseline_comparison_saved": bool(
                artifact_manifest.get("baseline_comparison_path")
            ),
            "result_diagnosis_input_saved": bool(
                artifact_manifest.get("result_diagnosis_input_path")
            ),
            "artifact_paths_excluded": True,
        },
        "paper_relevance": _metric_evaluation_paper_relevance(),
        "excluded_from_evidence": _metric_evaluation_exclusions(),
    }


def _build_iteration_decision_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    iteration_decision = IterationDecisionRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Iteration Decision and Closed-Loop Workflow Control",
        "role_in_system": (
            "Consume Metric Evaluation outputs, upstream module context, and "
            "iteration history to decide whether the AutoML workflow should "
            "iterate or stop. When iteration is selected, the module converts "
            "diagnostic reasoning into a concrete rerun plan and revised "
            "workflow guidance."
        ),
        "source_traceability": {
            "record_source": "iteration_decision table latest row by task_id",
            "reasoning_source": "iteration_decision.reasoning_json",
            "evidence_source": "iteration_decision.evidence_json",
            "system_checks_source": "iteration_decision.system_checks_json",
            "iterate_plan_source": "iteration_decision.iteration_plan_json",
            "revised_workflow_plan_source": (
                "iteration_decision.revised_workflow_plan_json"
            ),
            "rerun_plan_source": "iteration_decision.iteration_rerun_plan_json",
            "stop_rationale_source": "iteration_decision.stop_rationale_json",
            "validation_source": "iteration_decision.validation_result_json",
            "implementation_sources": [
                "app.modules.iteration_decision.context.metrics_context",
                "app.modules.iteration_decision.context.upstream_context",
                "app.modules.iteration_decision.context.history_context",
                "app.modules.iteration_decision.evidence.ml_evidence",
                "app.modules.iteration_decision.evidence.materials_evidence",
                "app.modules.iteration_decision.evidence.workflow_evidence",
                "app.modules.iteration_decision.evidence.history_evidence",
                "app.modules.iteration_decision.rules.ml_rules",
                "app.modules.iteration_decision.rules.materials_rules",
                "app.modules.iteration_decision.rules.guard_rules",
                "app.modules.iteration_decision.llm.prompt_builder",
                "app.modules.iteration_decision.llm.decision_validator",
                "app.modules.iteration_decision.llm.decision_normalizer",
                "app.modules.iteration_decision.plan.iteration_plan_builder",
                "app.modules.iteration_decision.plan.conflict_detector",
                "app.modules.iteration_decision.plan.plan_validator",
            ],
        },
        "upstream_readiness_gates": {
            "metric_evaluation_status": [
                "evaluated",
                "evaluated_with_warning",
                "partially_evaluated",
            ],
            "requires_metric_evaluation_record": True,
            "requires_result_diagnosis_input_json": True,
            "uses_all_available_upstream_module_context": True,
            "uses_iteration_history_when_available": True,
        },
    }

    if not iteration_decision:
        return {
            **base,
            "status": "missing",
            "note": (
                "No IterationDecision record was found for this task_id. "
                "Iteration decision evidence can be generated after the "
                "Iteration Decision module has run."
            ),
            "paper_relevance": _iteration_decision_paper_relevance(),
            "excluded_from_evidence": _iteration_decision_exclusions(),
        }

    reasoning = _pick_dict(getattr(iteration_decision, "reasoning_json", None))
    evidence_bundle = _pick_dict(getattr(iteration_decision, "evidence_json", None))
    system_checks = _pick_dict(
        getattr(iteration_decision, "system_checks_json", None)
    )
    iteration_plan = _pick_dict(
        getattr(iteration_decision, "iteration_plan_json", None)
    )
    revised_plan = _pick_dict(
        getattr(iteration_decision, "revised_workflow_plan_json", None)
    )
    rerun_plan = _pick_dict(
        getattr(iteration_decision, "iteration_rerun_plan_json", None)
    )
    stop_rationale = _pick_dict(
        getattr(iteration_decision, "stop_rationale_json", None)
    )
    validation_result = _pick_dict(
        getattr(iteration_decision, "validation_result_json", None)
    )
    llm_request = _pick_dict(getattr(iteration_decision, "llm_request_json", None))
    llm_response = _pick_dict(getattr(iteration_decision, "llm_response_json", None))
    decision = getattr(iteration_decision, "decision", None)

    return {
        **base,
        "status": getattr(iteration_decision, "status", None),
        "decision_summary": {
            "iteration_decision_record_present": True,
            "iteration_index": getattr(iteration_decision, "iteration_index", None),
            "decision": decision,
            "decision_confidence": getattr(
                iteration_decision,
                "decision_confidence",
                None,
            ),
            "metric_evaluation_id_recorded": bool(
                getattr(iteration_decision, "metric_evaluation_id", None)
            ),
            "metric_evaluation_id_excluded": bool(
                getattr(iteration_decision, "metric_evaluation_id", None)
            ),
            "pipeline_execution_id_recorded": bool(
                getattr(iteration_decision, "pipeline_execution_id", None)
            ),
            "pipeline_execution_id_excluded": bool(
                getattr(iteration_decision, "pipeline_execution_id", None)
            ),
            "rerun_from_stage": getattr(
                iteration_decision,
                "rerun_from_stage",
                None,
            ),
            "ready_for_iteration": getattr(
                iteration_decision,
                "ready_for_iteration",
                None,
            ),
            "error_message": getattr(iteration_decision, "error_message", None),
        },
        "context_gathering": {
            "metrics_context_fields": [
                "metric_evaluation_id",
                "pipeline_execution_id",
                "primary_metric",
                "metric_direction",
                "best_model_id",
                "best_trial_id",
                "best_pipeline_spec_id",
                "best_primary_metric_value",
                "metric_summary_json",
                "model_ranking_json",
                "result_diagnosis_input_json",
            ],
            "upstream_context_modules": [
                "task_specification",
                "task_interpretation",
                "dataset_profile",
                "workflow_plan",
                "feature_engineering",
                "feature_preprocessing",
                "model_search_context",
                "pipeline_generation",
                "pipeline_execution",
            ],
            "history_context_fields": [
                "n_iterations_completed",
                "previous_decisions",
                "best_metric_so_far",
                "best_model_so_far",
                "metric_trend",
                "repeated_root_causes",
                "tried_model_families",
                "total_failed_trials",
                "total_trials",
                "runtime_cost_summary",
            ],
            "full_context_excluded": True,
        },
        "evidence_extraction": _summarize_iteration_evidence_bundle(
            evidence_bundle
        ),
        "system_rule_checks": _summarize_iteration_system_checks(system_checks),
        "llm_decision_protocol": {
            "single_llm_call_after_rule_context": True,
            "allowed_decisions": ["iterate", "stop"],
            "required_reasoning_sections": [
                "task_completion",
                "performance_assessment",
                "gap_analysis",
                "root_cause",
                "improvement_potential",
                "final_reasoning_summary",
            ],
            "required_output_structure": [
                "decision",
                "reasoning",
                "evidence_basis",
                "iteration_plan_or_stop_rationale",
                "confidence",
            ],
            "security_constraints": [
                "valid JSON only",
                "no executable code",
                "no import statements",
                "no training scripts",
                "no shell commands",
                "no SQL",
                "no model.fit or Pipeline code",
            ],
            "validation_and_fallback": {
                "parse_response": True,
                "validate_decision_schema": True,
                "normalize_stage_aliases": True,
                "rule_based_fallback_when_invalid": True,
                "llm_request_recorded": bool(llm_request),
                "llm_request_text_excluded": bool(llm_request),
                "llm_response_recorded": bool(llm_response),
                "llm_response_text_excluded": bool(llm_response),
                "validation_result": _pick_keys(
                    validation_result,
                    ["is_valid", "issues"],
                ),
            },
        },
        "decision_reasoning": _summarize_iteration_reasoning(reasoning),
        "iterate_path": _summarize_iteration_iterate_path(
            iteration_plan=iteration_plan,
            revised_plan=revised_plan,
            rerun_plan=rerun_plan,
            active=(decision == "iterate"),
        ),
        "stop_path": _summarize_iteration_stop_path(
            stop_rationale=stop_rationale,
            active=(decision == "stop"),
        ),
        "plan_validation_and_conflict_control": {
            "llm_decision_validation": _pick_keys(
                validation_result,
                ["is_valid", "issues"],
            ),
            "iteration_plan_validation_rules": [
                "rerun_from_stage must be one of the valid target stages",
                "iterate decisions should include at least one stage change",
                "each stage change should include description and rationale",
                "iteration plans should specify a stop condition",
            ],
            "revised_workflow_plan_validation_rules": [
                "revised plan must exist for iterate decisions",
                "changed_sections should be present",
                "llm_reasoning_summary should be present",
            ],
            "rerun_plan_validation_rules": [
                "rerun_from_stage must be valid",
                "rerun_stages should be non-empty",
                "expected_improvement_targets should be non-empty",
            ],
            "conflict_detection_rules": [
                "conflicting feature expansion and feature reduction actions",
                "conflicting HPO increase and budget reduction actions",
                "conflicting model addition and model reduction actions",
                "stage changes before rerun_from_stage that would not take effect",
            ],
            "ready_for_iteration": getattr(
                iteration_decision,
                "ready_for_iteration",
                None,
            ),
        },
        "artifact_and_traceability": {
            "artifact_dir_recorded": bool(
                getattr(iteration_decision, "artifact_dir", None)
            ),
            "artifact_dir_excluded": bool(
                getattr(iteration_decision, "artifact_dir", None)
            ),
            "decision_result_saved_by_artifact_manager": bool(decision),
            "context_artifact_saved_when_available": bool(llm_request),
            "evidence_artifact_saved": bool(evidence_bundle),
            "system_checks_artifact_saved": bool(system_checks),
            "llm_request_artifact_saved": bool(llm_request),
            "llm_response_artifact_saved": bool(llm_response),
            "iteration_plan_artifact_saved": bool(iteration_plan),
            "revised_workflow_plan_artifact_saved": bool(revised_plan),
            "stop_output_artifact_saved": bool(stop_rationale),
            "artifact_paths_excluded": True,
        },
        "paper_relevance": _iteration_decision_paper_relevance(),
        "excluded_from_evidence": _iteration_decision_exclusions(),
    }


def _build_interpretability_analysis_evidence(
    session: Session,
    task_id: str,
) -> Dict[str, Any]:
    interpretability = InterpretabilityAnalysisRepository().get_latest_by_task_id(
        session,
        task_id,
    )

    base = {
        "module_name": "Interpretability Analysis and Materials Insight Generation",
        "role_in_system": (
            "Analyze the final selected model from Metric Evaluation, combine "
            "model artifacts, prediction artifacts, feature lineage, and "
            "materials context, then produce interpretable model-behavior "
            "evidence and a structured handoff for Final Output."
        ),
        "source_traceability": {
            "record_source": (
                "interpretability_analysis table latest row by task_id"
            ),
            "method_plan_source": "interpretability_analysis.methods_used_json",
            "global_feature_importance_source": (
                "interpretability_analysis.global_feature_importance_json"
            ),
            "shap_source": "interpretability_analysis.shap_summary_json",
            "material_insight_source": (
                "interpretability_analysis.material_insight_summary_json"
            ),
            "final_output_handoff_source": (
                "interpretability_analysis.final_output_input_json"
            ),
            "implementation_sources": [
                "app.modules.interpretability_analysis.context_builder",
                "app.modules.interpretability_analysis.interpretability_input_loader",
                "app.modules.interpretability_analysis.interpretability_method_selector",
                "app.modules.interpretability_analysis.coefficient_importance_analyzer",
                "app.modules.interpretability_analysis.native_importance_analyzer",
                "app.modules.interpretability_analysis.permutation_importance_analyzer",
                "app.modules.interpretability_analysis.shap_analyzer",
                "app.modules.interpretability_analysis.local_explanation_builder",
                "app.modules.interpretability_analysis.high_error_sample_analyzer",
                "app.modules.interpretability_analysis.feature_group_analyzer",
                "app.modules.interpretability_analysis.cross_method_consensus",
                "app.modules.interpretability_analysis.partial_dependence_analyzer",
                "app.modules.interpretability_analysis.residual_analyzer",
                "app.modules.interpretability_analysis.correlation_analyzer",
                "app.modules.interpretability_analysis.physics_constraint_checker",
                "app.modules.interpretability_analysis.llm_interpretability_prompt_builder",
                "app.modules.interpretability_analysis.llm_interpretability_validator",
                "app.modules.interpretability_analysis.final_output_input_builder",
            ],
        },
        "upstream_readiness_gates": {
            "metric_evaluation_status": [
                "evaluated",
                "evaluated_with_warning",
                "partially_evaluated",
            ],
            "requires_best_model_id": True,
            "requires_best_trial_id": True,
            "requires_model_artifact_when_building_final_output_input": True,
            "uses_pipeline_execution_prediction_artifacts": True,
            "uses_feature_preprocessing_lineage_when_available": True,
        },
    }

    if not interpretability:
        return {
            **base,
            "status": "missing",
            "note": (
                "No InterpretabilityAnalysis record was found for this task_id. "
                "Interpretability evidence can be generated after the "
                "Interpretability Analysis module has run."
            ),
            "paper_relevance": _interpretability_analysis_paper_relevance(),
            "excluded_from_evidence": _interpretability_analysis_exclusions(),
        }

    methods_used = _pick_dict(getattr(interpretability, "methods_used_json", None))
    global_importance = _extract_items(
        getattr(interpretability, "global_feature_importance_json", None)
    )
    permutation_importance = _extract_items(
        getattr(interpretability, "permutation_importance_json", None)
    )
    shap_summary = _pick_dict(getattr(interpretability, "shap_summary_json", None))
    local_explanations = _extract_items(
        getattr(interpretability, "local_explanations_json", None)
    )
    high_error_samples = _extract_items(
        getattr(interpretability, "high_error_sample_analysis_json", None)
    )
    consensus = _pick_dict(
        getattr(interpretability, "cross_method_consensus_json", None)
    )
    partial_dependence = _pick_dict(
        getattr(interpretability, "partial_dependence_json", None)
    )
    residual_analysis = _pick_dict(
        getattr(interpretability, "residual_analysis_json", None)
    )
    correlation_analysis = _pick_dict(
        getattr(interpretability, "correlation_analysis_json", None)
    )
    physics_check = _pick_dict(
        getattr(interpretability, "physics_constraint_check_json", None)
    )
    material_insight = _pick_dict(
        getattr(interpretability, "material_insight_summary_json", None)
    )
    llm_summary = _pick_dict(getattr(interpretability, "llm_summary_json", None))
    final_output_input = _pick_dict(
        getattr(interpretability, "final_output_input_json", None)
    )
    artifact_manifest = _pick_dict(
        getattr(interpretability, "artifact_manifest_json", None)
    )
    llm_request = _pick_dict(getattr(interpretability, "llm_request_json", None))
    llm_response = _pick_dict(getattr(interpretability, "llm_response_json", None))

    return {
        **base,
        "status": getattr(interpretability, "status", None),
        "analysis_summary": {
            "interpretability_record_present": True,
            "analysis_profile": getattr(interpretability, "analysis_profile", None),
            "final_model_id": getattr(interpretability, "final_model_id", None),
            "final_model_family": getattr(
                interpretability,
                "final_model_family",
                None,
            ),
            "final_trial_id": getattr(interpretability, "final_trial_id", None),
            "metric_evaluation_id_recorded": bool(
                getattr(interpretability, "metric_evaluation_id", None)
            ),
            "metric_evaluation_id_excluded": bool(
                getattr(interpretability, "metric_evaluation_id", None)
            ),
            "pipeline_execution_id_recorded": bool(
                getattr(interpretability, "pipeline_execution_id", None)
            ),
            "pipeline_execution_id_excluded": bool(
                getattr(interpretability, "pipeline_execution_id", None)
            ),
            "ready_for_final_output": getattr(
                interpretability,
                "ready_for_final_output",
                None,
            ),
            "llm_used": getattr(interpretability, "llm_used", None),
            "llm_confidence_level": getattr(
                interpretability,
                "llm_confidence_level",
                None,
            ),
            "error_message": getattr(interpretability, "error_message", None),
        },
        "readiness_and_input_context": {
            "input_fields_loaded": [
                "model_artifact_path",
                "model_ready_matrix_path",
                "prediction_artifact_paths",
                "feature_columns",
                "feature_lineage",
                "metric_summary",
                "model_ranking",
                "task/material/domain context",
                "stop_rationale when Iteration Decision stopped",
            ],
            "artifact_path_policy": [
                "model and prediction artifact paths are used for computation",
                "local paths are excluded from the paper evidence package",
                "feature matrix values are not included",
            ],
            "path_presence_from_final_output_input": {
                "model_artifact_path_recorded": bool(
                    final_output_input.get("model_artifact_path")
                ),
                "model_artifact_path_excluded": bool(
                    final_output_input.get("model_artifact_path")
                ),
                "prediction_artifact_count": len(
                    _as_list(final_output_input.get("prediction_artifact_paths"))
                ),
                "prediction_artifact_paths_excluded": True,
            },
            "metric_summary": _pick_dict(final_output_input.get("metric_summary")),
            "selection_summary": _pick_dict(
                final_output_input.get("selection_summary")
            ),
        },
        "method_selection": {
            "methods": methods_used.get("methods", []),
            "statuses": _pick_dict(methods_used.get("statuses")),
            "selection_policy": [
                "linear models use coefficient, permutation, and linear SHAP when enabled",
                "tree models use native importance, permutation, and tree SHAP when enabled",
                "kernel or distance-based models default to permutation; full profile may use sampling SHAP",
                "baseline or dummy models skip formal interpretability analysis",
                "permutation importance is used as a fallback when other importance methods fail",
            ],
        },
        "global_feature_importance": _summarize_global_feature_importance(
            global_importance
        ),
        "permutation_importance": _summarize_permutation_importance(
            permutation_importance
        ),
        "shap_analysis": _summarize_shap_analysis(shap_summary),
        "cross_method_consensus": _summarize_cross_method_consensus(consensus),
        "feature_group_and_material_insight": {
            "feature_group_summary": _summarize_feature_group_from_importance(
                global_importance
            ),
            "material_insight_summary": _summarize_material_insight(
                material_insight
            ),
            "llm_interpretability_summary": _summarize_llm_interpretability_summary(
                llm_summary
            ),
        },
        "local_and_high_error_explanations": {
            "local_explanations": _summarize_local_explanations(
                local_explanations
            ),
            "high_error_sample_analysis": _summarize_high_error_samples(
                high_error_samples
            ),
        },
        "residual_and_systematic_error_analysis": _summarize_residual_analysis(
            residual_analysis
        ),
        "correlation_and_pdp": {
            "correlation_analysis": _summarize_correlation_analysis(
                correlation_analysis
            ),
            "partial_dependence": _summarize_partial_dependence(
                partial_dependence
            ),
        },
        "physics_constraint_check": _summarize_physics_constraint_check(
            physics_check
        ),
        "llm_summary_protocol": {
            "llm_used": getattr(interpretability, "llm_used", None),
            "llm_request_recorded": bool(llm_request),
            "llm_request_text_excluded": bool(llm_request),
            "llm_response_recorded": bool(llm_response),
            "llm_response_text_excluded": bool(llm_response),
            "constraints": [
                "LLM summarizes numerical interpretability results only",
                "LLM must not modify feature importance values",
                "LLM must not modify SHAP values",
                "LLM must not modify predictions",
                "LLM must not claim causal mechanisms unless supported",
                "LLM must not output executable code, shell, or SQL",
                "LLM must not suggest model retraining or feature modifications",
                "all interpretations must be framed as hypotheses or model associations",
            ],
            "validation_checks": [
                "dangerous code pattern scan",
                "forbidden field scan",
                "confidence level validation",
                "evidence strength normalization",
                "fallback limitations when output is unparseable",
            ],
        },
        "final_output_handoff": _summarize_interpretability_final_output_input(
            final_output_input
        ),
        "artifact_management": _summarize_interpretability_artifact_manifest(
            artifact_manifest
        ),
        "paper_relevance": _interpretability_analysis_paper_relevance(),
        "excluded_from_evidence": _interpretability_analysis_exclusions(),
    }


def _build_input_summary(task_spec: Optional[Any], task_spec_json: Dict[str, Any]) -> Dict[str, Any]:
    if not task_spec:
        return {
            "status": "missing",
            "note": "TaskSpecification record was not found for this task_id.",
        }

    return {
        "task_name": getattr(task_spec, "task_name", None),
        "task_description_excerpt": _truncate(task_spec_json.get("task_description"), 1200),
        "material_system": task_spec_json.get("material_system"),
        "task_type": getattr(task_spec, "task_type", None),
        "prediction_target": getattr(task_spec, "prediction_target", None),
        "target_column": getattr(task_spec, "target_column", None),
        "evaluation_metric": getattr(task_spec, "evaluation_metric", None),
        "dataset_description_excerpt": _truncate(getattr(task_spec, "dataset_description", None), 1000),
        "input_type": getattr(task_spec, "input_type", None),
        "user_priority": task_spec_json.get("user_priority", []),
        "constraints": task_spec_json.get("constraints", []),
        "status": getattr(task_spec, "status", None),
        "missing_fields": task_spec_json.get("missing_fields", []),
        "validation_messages": task_spec_json.get("validation_messages", []),
    }


def _build_llm_semantic_interpretation(
    task_trace: Dict[str, Any],
    interpretation: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "status": interpretation.get("status") or task_trace.get("status"),
        "interpreted_task_type": _first_present(
            interpretation.get("interpreted_task_type"),
            task_trace.get("interpreted_task_type"),
        ),
        "interpreted_input_modality": _first_present(
            interpretation.get("interpreted_input_modality"),
            task_trace.get("interpreted_input_modality"),
        ),
        "interpreted_material_domain": _first_present(
            interpretation.get("interpreted_material_domain"),
            task_trace.get("interpreted_material_domain"),
        ),
        "interpreted_prediction_target": _pick_dict(
            interpretation.get("interpreted_prediction_target")
        ),
        "modeling_intent": _pick_dict(interpretation.get("modeling_intent")),
        "dataset_intent": _pick_dict(interpretation.get("dataset_intent")),
        "planning_hint": _pick_dict(interpretation.get("planning_hint")),
        "constraint_interpretation": _pick_dict(
            interpretation.get("constraint_interpretation")
        ),
        "recommended_defaults": _pick_dict(interpretation.get("recommended_defaults")),
        "ambiguities": interpretation.get("ambiguities", []),
        "warnings": interpretation.get("warnings", []),
        "llm_reasoning_summary": interpretation.get("llm_reasoning_summary"),
        "confidence_score": _first_present(
            interpretation.get("confidence_score"),
            task_trace.get("confidence_score"),
        ),
    }


def _pick_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _pick_keys(source: Dict[str, Any], keys: list) -> Dict[str, Any]:
    return {key: source.get(key) for key in keys if key in source}


def _first_non_empty_dict(*values: Any) -> Dict[str, Any]:
    for value in values:
        if isinstance(value, dict) and value:
            return value
    return {}


def _first_non_empty_list(*values: Any) -> list:
    for value in values:
        if isinstance(value, list) and value:
            return value
    return []


def _summarize_feature_actions(actions: Any) -> list:
    if not isinstance(actions, list):
        return []
    summarized = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        summarized.append(
            _pick_keys(
                action,
                [
                    "action_id",
                    "capability_id",
                    "priority",
                    "input_columns",
                    "parameters",
                    "output_feature_group",
                    "decision_rationale",
                ],
            )
        )
    return summarized


def _summarize_rejected_feature_actions(actions: Any) -> list:
    if not isinstance(actions, list):
        return []
    summarized = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        summarized.append(_pick_keys(action, ["capability_id", "reason", "evidence"]))
    return summarized


def _summarize_model_actions(actions: Any) -> list:
    if not isinstance(actions, list):
        return []
    summarized = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        summarized.append(
            _pick_keys(
                action,
                ["action_id", "model_family", "priority", "decision_rationale"],
            )
        )
    return summarized


def _summarize_rejected_model_actions(actions: Any) -> list:
    if not isinstance(actions, list):
        return []
    summarized = []
    for action in actions:
        if not isinstance(action, dict):
            continue
        summarized.append(_pick_keys(action, ["model_family", "reason", "evidence"]))
    return summarized


def _summarize_columns(columns: Any, max_columns: int = 50) -> Dict[str, Any]:
    if not isinstance(columns, list):
        return {
            "items": [],
            "total_columns_described": 0,
            "omitted_columns": 0,
        }

    summarized = []
    for col in columns[:max_columns]:
        if not isinstance(col, dict):
            continue
        summarized.append(
            _pick_keys(
                col,
                ["name", "role", "dtype", "missing_count", "missing_ratio"],
            )
        )

    return {
        "items": summarized,
        "total_columns_described": len(columns),
        "omitted_columns": max(len(columns) - len(summarized), 0),
    }


def _summarize_feature_columns(columns: Any, max_columns: int = 50) -> Dict[str, Any]:
    if not isinstance(columns, list):
        return {
            "sample": [],
            "total_feature_columns": 0,
            "omitted_feature_columns": 0,
        }

    sample = [str(col) for col in columns[:max_columns]]
    return {
        "sample": sample,
        "total_feature_columns": len(columns),
        "omitted_feature_columns": max(len(columns) - len(sample), 0),
    }


def _summarize_executed_featurizers(featurizers: Any) -> list:
    if not isinstance(featurizers, list):
        return []

    summarized = []
    for featurizer in featurizers:
        if not isinstance(featurizer, dict):
            continue
        summarized.append(
            _pick_keys(
                featurizer,
                [
                    "name",
                    "display_name",
                    "status",
                    "n_features_generated",
                    "failed_sample_count",
                    "execution_time_ms",
                    "dependency_versions",
                ],
            )
        )
    return summarized


def _summarize_feature_groups(
    groups: Any,
    max_groups: int = 30,
    max_feature_names: int = 20,
) -> Dict[str, Any]:
    if not isinstance(groups, list):
        return {
            "items": [],
            "total_feature_groups": 0,
            "omitted_feature_groups": 0,
        }

    summarized = []
    for group in groups[:max_groups]:
        if not isinstance(group, dict):
            continue
        feature_names = group.get("feature_names", [])
        item = _pick_keys(
            group,
            [
                "group_id",
                "source_action_id",
                "capability_id",
                "feature_family",
                "feature_count",
                "semantic_description",
            ],
        )
        item["feature_names"] = _summarize_feature_columns(
            feature_names,
            max_feature_names,
        )
        summarized.append(item)

    return {
        "items": summarized,
        "total_feature_groups": len(groups),
        "omitted_feature_groups": max(len(groups) - len(summarized), 0),
    }


def _summarize_feature_quality_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    per_feature_summary = profile.get("per_feature_summary", [])
    if not isinstance(per_feature_summary, list):
        per_feature_summary = []

    return {
        "global_summary": _pick_dict(profile.get("global_summary")),
        "per_group_summary": profile.get("per_group_summary", []),
        "quality_warnings": _summarize_quality_warnings(
            profile.get("quality_warnings", [])
        ),
        "per_feature_summary_omitted": True,
        "per_feature_summary_count": len(per_feature_summary),
    }


def _summarize_quality_warnings(warnings: Any, max_features: int = 20) -> list:
    if not isinstance(warnings, list):
        return []

    summarized = []
    for warning in warnings:
        if not isinstance(warning, dict):
            continue
        item = _pick_keys(warning, ["warning_type", "severity", "message"])
        item["affected_features"] = _summarize_feature_columns(
            warning.get("affected_features", []),
            max_features,
        )
        summarized.append(item)
    return summarized


def _summarize_execution_report(report: Dict[str, Any]) -> Dict[str, Any]:
    action_results = report.get("action_results", [])
    if not isinstance(action_results, list):
        action_results = []

    summarized = []
    for action in action_results:
        if not isinstance(action, dict):
            continue
        summarized.append(
            _pick_keys(
                action,
                [
                    "action_id",
                    "capability_id",
                    "status",
                    "generated_feature_count",
                    "warnings",
                    "error_message",
                    "fallback_action_id",
                ],
            )
        )

    return {
        "action_results": summarized,
        "action_result_count": len(action_results),
    }


def _summarize_feature_provenance(provenance: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "registry_snapshot_version": provenance.get("registry_snapshot_version"),
        "input_artifact_hash_recorded": bool(provenance.get("input_artifact_hash")),
        "featurizer_versions": provenance.get("featurizer_versions", {}),
        "dependency_versions": provenance.get("dependency_versions", {}),
        "created_at_excluded": bool(provenance.get("created_at")),
    }


def _summarize_feature_preprocessing_decision_input(
    decision_input: Dict[str, Any],
) -> Dict[str, Any]:
    feature_matrix_context = _pick_dict(decision_input.get("feature_matrix_context"))

    return {
        "task_context": _pick_dict(decision_input.get("task_context")),
        "dataset_context": _pick_dict(decision_input.get("dataset_context")),
        "workflow_context": _pick_dict(decision_input.get("workflow_context")),
        "feature_matrix_context": {
            **_pick_keys(
                feature_matrix_context,
                [
                    "n_samples",
                    "n_features",
                    "feature_groups",
                    "numeric_feature_count",
                    "categorical_feature_count",
                    "constant_feature_count",
                    "all_missing_feature_count",
                    "has_missing_values",
                    "missing_value_ratio",
                    "is_valid_feature_matrix",
                    "quality_warnings",
                ],
            ),
            "feature_columns": _summarize_feature_columns(
                feature_matrix_context.get("feature_columns", [])
            ),
        },
        "execution_context": _pick_dict(decision_input.get("execution_context")),
        "known_preprocessing_risks": decision_input.get(
            "known_preprocessing_risks",
            [],
        ),
    }


def _feature_engineering_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Automated conversion of an LLM-generated feature strategy into a "
            "validated, persisted, model-ready feature matrix."
        ),
        "innovation_point": (
            "The module links high-level planning decisions to executable "
            "featurizer actions, quality diagnostics, feature provenance, and "
            "downstream preprocessing requirements."
        ),
        "why_this_module_matters": (
            "It bridges AI-guided workflow design and conventional ML pipeline "
            "execution by making feature generation auditable, quality-aware, "
            "and reusable by later preprocessing, modeling, HPO, and "
            "interpretability modules."
        ),
    }


def _feature_engineering_exclusions() -> list:
    return [
        "preview_json.rows",
        "raw feature matrix values",
        "artifact file contents",
        "artifact_path and feature_matrix_path",
        "full feature column list when too long",
        "full per-feature quality summary",
        "created_at",
        "updated_at",
        "random feature engineering identifiers unless needed for traceability",
    ]


def _summarize_preprocessing_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    global_policy = _pick_dict(plan.get("global_policy"))

    return {
        "plan_version": plan.get("plan_version"),
        "global_policy": {
            "leakage_prevention": _pick_dict(
                global_policy.get("leakage_prevention")
            ),
            "variant_strategy": _pick_dict(global_policy.get("variant_strategy")),
        },
        "capability_groups_used": plan.get("capability_groups_used", []),
        "column_policies": _summarize_column_policies(
            plan.get("column_policies", [])
        ),
        "feature_group_policies": _summarize_feature_group_policies(
            plan.get("feature_group_policies", [])
        ),
        "operation_sequence": _summarize_preprocessing_operations(
            plan.get("operation_sequence", [])
        ),
        "model_family_specific_notes": plan.get("model_family_specific_notes", []),
        "rejected_operations": _summarize_rejected_preprocessing_operations(
            plan.get("rejected_operations", [])
        ),
        "warnings_for_downstream": plan.get("warnings_for_downstream", []),
    }


def _summarize_column_policies(
    policies: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(policies, list):
        return {
            "items": [],
            "action_counts": {},
            "total_column_policies": 0,
            "omitted_column_policies": 0,
        }

    action_counts: Dict[str, int] = {}
    summarized = []
    for policy in policies:
        if not isinstance(policy, dict):
            continue
        action = policy.get("action") or "unknown"
        action_counts[action] = action_counts.get(action, 0) + 1
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(
                    policy,
                    ["column_name", "action", "reason", "evidence", "risk"],
                )
            )

    return {
        "items": summarized,
        "action_counts": action_counts,
        "total_column_policies": len(policies),
        "omitted_column_policies": max(len(policies) - len(summarized), 0),
    }


def _summarize_feature_group_policies(
    policies: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(policies, list):
        return {
            "items": [],
            "policy_counts": {},
            "total_feature_group_policies": 0,
            "omitted_feature_group_policies": 0,
        }

    policy_counts: Dict[str, int] = {}
    summarized = []
    for policy in policies:
        if not isinstance(policy, dict):
            continue
        policy_name = policy.get("policy") or "unknown"
        policy_counts[policy_name] = policy_counts.get(policy_name, 0) + 1
        if len(summarized) < max_items:
            summarized.append(
                {
                    **_pick_keys(policy, ["feature_group", "policy"]),
                    "operations": _summarize_preprocessing_operations(
                        policy.get("operations", []),
                        max_items=10,
                    ),
                }
            )

    return {
        "items": summarized,
        "policy_counts": policy_counts,
        "total_feature_group_policies": len(policies),
        "omitted_feature_group_policies": max(len(policies) - len(summarized), 0),
    }


def _summarize_preprocessing_operations(
    operations: Any,
    max_items: int = 50,
) -> Dict[str, Any]:
    if not isinstance(operations, list):
        return {
            "items": [],
            "capability_counts": {},
            "execution_scope_counts": {},
            "total_operations": 0,
            "omitted_operations": 0,
        }

    capability_counts: Dict[str, int] = {}
    execution_scope_counts: Dict[str, int] = {}
    summarized = []

    for operation in operations:
        if not isinstance(operation, dict):
            continue
        capability_id = operation.get("capability_id") or "unknown"
        scope = operation.get("execution_scope") or "unknown"
        capability_counts[capability_id] = capability_counts.get(capability_id, 0) + 1
        execution_scope_counts[scope] = execution_scope_counts.get(scope, 0) + 1

        if len(summarized) < max_items:
            summarized.append(
                {
                    **_pick_keys(
                        operation,
                        [
                            "step_order",
                            "operation_id",
                            "capability_id",
                            "target_feature_groups",
                            "target_columns",
                            "parameters",
                            "execution_scope",
                        ],
                    ),
                    "decision_rationale": _pick_keys(
                        _pick_dict(operation.get("decision_rationale")),
                        ["reason", "evidence", "expected_benefit", "risk", "fallback"],
                    ),
                }
            )

    return {
        "items": summarized,
        "capability_counts": capability_counts,
        "execution_scope_counts": execution_scope_counts,
        "total_operations": len(operations),
        "omitted_operations": max(len(operations) - len(summarized), 0),
    }


def _summarize_rejected_preprocessing_operations(
    operations: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(operations, list):
        return {
            "items": [],
            "total_rejected_operations": 0,
            "omitted_rejected_operations": 0,
        }

    summarized = []
    for operation in operations[:max_items]:
        if not isinstance(operation, dict):
            continue
        summarized.append(
            _pick_keys(operation, ["capability_id", "reason", "evidence"])
        )

    return {
        "items": summarized,
        "total_rejected_operations": len(operations),
        "omitted_rejected_operations": max(len(operations) - len(summarized), 0),
    }


def _summarize_preprocessing_execution_report(report: Dict[str, Any]) -> Dict[str, Any]:
    operation_results = report.get("operation_results", [])
    if not isinstance(operation_results, list):
        operation_results = []

    status_counts: Dict[str, int] = {}
    capability_group_counts: Dict[str, int] = {}
    summarized = []

    for operation in operation_results:
        if not isinstance(operation, dict):
            continue
        status = operation.get("status") or "unknown"
        group = operation.get("capability_group") or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        capability_group_counts[group] = capability_group_counts.get(group, 0) + 1
        summarized.append(
            {
                **_pick_keys(
                    operation,
                    [
                        "operation_id",
                        "capability_id",
                        "capability_group",
                        "status",
                        "warnings",
                        "error_message",
                    ],
                ),
                "affected_features": _summarize_feature_columns(
                    operation.get("affected_features", []),
                    max_columns=20,
                ),
                "removed_features": _summarize_feature_columns(
                    operation.get("removed_features", []),
                    max_columns=20,
                ),
            }
        )

    return {
        "operation_results": summarized,
        "operation_result_count": len(operation_results),
        "status_counts": status_counts,
        "capability_group_counts": capability_group_counts,
    }


def _extract_removed_features(value: Any) -> list:
    if isinstance(value, list):
        return value
    if not isinstance(value, dict):
        return []
    removed = value.get("removed_features")
    if isinstance(removed, list):
        return removed
    return []


def _summarize_removed_features(
    removed_features: Any,
    max_examples: int = 20,
) -> Dict[str, Any]:
    if not isinstance(removed_features, list):
        return {
            "examples": [],
            "reason_counts": {},
            "capability_counts": {},
            "total_removed_features": 0,
            "omitted_removed_feature_examples": 0,
        }

    reason_counts: Dict[str, int] = {}
    capability_counts: Dict[str, int] = {}
    examples = []

    for removed in removed_features:
        if not isinstance(removed, dict):
            continue
        reason = removed.get("reason") or "unknown"
        capability = _extract_capability_from_evidence(removed.get("evidence"))
        reason_counts[reason] = reason_counts.get(reason, 0) + 1
        capability_counts[capability] = capability_counts.get(capability, 0) + 1
        if len(examples) < max_examples:
            examples.append(
                _pick_keys(
                    removed,
                    ["feature_name", "reason", "evidence", "source_feature_group"],
                )
            )

    return {
        "examples": examples,
        "reason_counts": reason_counts,
        "capability_counts": capability_counts,
        "total_removed_features": len(removed_features),
        "omitted_removed_feature_examples": max(
            len(removed_features) - len(examples),
            0,
        ),
    }


def _extract_capability_from_evidence(evidence: Any) -> str:
    if not evidence:
        return "unknown"
    text = str(evidence)
    marker = "capability="
    if marker not in text:
        return "unknown"
    after = text.split(marker, 1)[1]
    return after.split(";", 1)[0].strip() or "unknown"


def _summarize_feature_lineage(lineage_map: Dict[str, Any]) -> Dict[str, Any]:
    entries = [value for value in lineage_map.values() if isinstance(value, dict)]

    def _count(flag: str) -> int:
        return sum(1 for entry in entries if entry.get(flag))

    removed_entries = [entry for entry in entries if entry.get("removed")]
    return {
        "lineage_entry_count": len(entries),
        "imputed_count": _count("imputed"),
        "scaled_count": _count("scaled"),
        "transformed_count": _count("transformed"),
        "selected_count": _count("selected"),
        "reduced_count": _count("reduced"),
        "interpretable_count": _count("is_interpretable"),
        "removed_count": len(removed_entries),
        "removed_reason_counts": _count_by_key(removed_entries, "removal_reason"),
    }


def _summarize_feature_group_lineage(
    lineage_map: Dict[str, Any],
    max_items: int = 30,
) -> Dict[str, Any]:
    entries = [value for value in lineage_map.values() if isinstance(value, dict)]
    summarized = []
    for entry in entries[:max_items]:
        summarized.append(
            _pick_keys(
                entry,
                [
                    "group_name",
                    "group_status",
                    "original_feature_count",
                    "retained_feature_count",
                    "removed_feature_count",
                    "operations_applied",
                ],
            )
        )

    return {
        "items": summarized,
        "status_counts": _count_by_key(entries, "group_status"),
        "total_feature_groups": len(entries),
        "omitted_feature_groups": max(len(entries) - len(summarized), 0),
    }


def _count_by_key(items: list, key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        value = item.get(key) or "unknown"
        counts[str(value)] = counts.get(str(value), 0) + 1
    return counts


def _summarize_preprocessing_provenance(
    provenance: Dict[str, Any],
    registry_snapshot_version: Optional[str],
) -> Dict[str, Any]:
    parameter_snapshot = _pick_dict(provenance.get("operation_parameter_snapshot"))
    fitted_statistics = _pick_dict(provenance.get("fitted_statistics_summary"))

    return {
        "registry_snapshot_version": _first_present(
            registry_snapshot_version,
            provenance.get("registry_snapshot_version"),
        ),
        "input_feature_artifact_hash_recorded": bool(
            provenance.get("input_feature_artifact_hash")
        ),
        "output_artifact_hash_recorded": bool(provenance.get("output_artifact_hash")),
        "operation_parameter_snapshot": {
            "operation_ids": list(parameter_snapshot.keys()),
            "operation_count": len(parameter_snapshot),
        },
        "fitted_statistics_summary": {
            "statistic_keys": list(fitted_statistics.keys())[:50],
            "statistic_key_count": len(fitted_statistics),
            "full_fitted_statistics_omitted": True,
        },
        "dependency_versions": provenance.get("dependency_versions", {}),
        "random_seed": provenance.get("random_seed"),
        "created_at_excluded": bool(provenance.get("created_at")),
    }


def _data_preprocessing_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Registry-constrained LLM preprocessing planning with explicit "
            "validation, leakage prevention, feature lineage, and fold-safe "
            "handoff to model training."
        ),
        "innovation_point": (
            "The module separates global-safe preprocessing decisions from "
            "fold-only transformer fitting, converting an AI plan into a "
            "validated FoldPipelineSpec instead of fitting transformations on "
            "the full dataset."
        ),
        "why_this_module_matters": (
            "It turns feature-engineering output into a reproducible, "
            "model-search-ready artifact while preserving traceability of "
            "removed, transformed, imputed, scaled, and reduced features."
        ),
    }


def _data_preprocessing_exclusions() -> list:
    return [
        "raw LLM prompt",
        "raw LLM response",
        "full preprocessing JSON schema",
        "preview_json.rows",
        "model-ready matrix values",
        "full feature column list when too long",
        "full removed feature list",
        "full feature_lineage_map",
        "model_ready_artifact_path and preprocessor_artifact_path",
        "full fitted statistics",
        "created_at",
        "updated_at",
        "random preprocessing identifiers",
    ]


def _summarize_model_search_llm_advice(advice: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "candidate_model_families": advice.get("candidate_model_families", []),
        "baseline_models": advice.get("baseline_models", []),
        "preferred_model_bias": advice.get("preferred_model_bias"),
        "hpo_search_method": advice.get("hpo_search_method"),
        "hpo_budget_level": advice.get("hpo_budget_level"),
        "max_trials": advice.get("max_trials"),
        "validation_split_strategy": advice.get("validation_split_strategy"),
        "n_splits": advice.get("n_splits"),
        "adjustment_reasons": advice.get("adjustment_reasons", []),
        "risk_notes": advice.get("risk_notes", []),
        "confidence_score": advice.get("confidence_score"),
    }


def _summarize_strategy_changes(
    changes: Any,
    max_items: int = 40,
) -> Dict[str, Any]:
    if not isinstance(changes, list):
        return {
            "items": [],
            "strategy_area_counts": {},
            "change_type_counts": {},
            "total_strategy_changes": 0,
            "omitted_strategy_changes": 0,
        }

    strategy_area_counts: Dict[str, int] = {}
    change_type_counts: Dict[str, int] = {}
    summarized = []

    for change in changes:
        if not isinstance(change, dict):
            continue
        area = change.get("strategy_area") or "unknown"
        change_type = change.get("change_type") or "unknown"
        strategy_area_counts[area] = strategy_area_counts.get(area, 0) + 1
        change_type_counts[change_type] = change_type_counts.get(change_type, 0) + 1
        if len(summarized) < max_items:
            summarized.append(
                {
                    "strategy_area": area,
                    "field_path": change.get("field_path"),
                    "change_type": change_type,
                    "original_value": _compact_strategy_value(
                        change.get("original_value")
                    ),
                    "updated_value": _compact_strategy_value(
                        change.get("updated_value")
                    ),
                    "decision_rationale": _pick_keys(
                        _pick_dict(change.get("decision_rationale")),
                        ["reason", "evidence", "expected_benefit", "risk", "fallback"],
                    ),
                }
            )

    return {
        "items": summarized,
        "strategy_area_counts": strategy_area_counts,
        "change_type_counts": change_type_counts,
        "total_strategy_changes": len(changes),
        "omitted_strategy_changes": max(len(changes) - len(summarized), 0),
    }


def _compact_strategy_value(value: Any) -> Any:
    if isinstance(value, list):
        if all(not isinstance(item, (dict, list)) for item in value):
            return {
                "items": value[:30],
                "total_items": len(value),
                "omitted_items": max(len(value) - 30, 0),
            }
        summarized = []
        for item in value[:15]:
            if isinstance(item, dict):
                summarized.append(
                    _pick_keys(
                        item,
                        [
                            "model_id",
                            "model_family",
                            "priority",
                            "hpo_enabled",
                            "reason",
                            "capability_id",
                            "field_path",
                            "change_type",
                        ],
                    )
                )
            else:
                summarized.append(str(item))
        return {
            "items": summarized,
            "total_items": len(value),
            "omitted_items": max(len(value) - len(summarized), 0),
        }
    if isinstance(value, dict):
        keys = list(value.keys())
        compact = {}
        for key in keys[:20]:
            item = value.get(key)
            if isinstance(item, (dict, list)):
                compact[key] = _compact_strategy_value(item)
            else:
                compact[key] = item
        if len(keys) > len(compact):
            compact["_omitted_keys"] = len(keys) - len(compact)
        return compact
    return value


def _summarize_candidate_model_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    baseline_models = plan.get("baseline_models", [])
    candidate_models = plan.get("candidate_models", [])
    excluded_models = plan.get("excluded_models", [])

    return {
        "baseline_models": _summarize_model_plan_items(
            baseline_models,
            ["model_id", "role", "hpo_enabled"],
        ),
        "candidate_models": _summarize_model_plan_items(
            candidate_models,
            ["model_id", "model_family", "priority", "hpo_enabled", "reason"],
        ),
        "excluded_models": _summarize_model_plan_items(
            excluded_models,
            ["model_id", "reason"],
        ),
        "counts": {
            "n_baseline_models": len(baseline_models)
            if isinstance(baseline_models, list)
            else 0,
            "n_candidate_models": len(candidate_models)
            if isinstance(candidate_models, list)
            else 0,
            "n_excluded_models": len(excluded_models)
            if isinstance(excluded_models, list)
            else 0,
        },
        "single_baseline_rule": True,
    }


def _summarize_model_plan_items(
    items: Any,
    keys: list,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {"items": [], "total_items": 0, "omitted_items": 0}

    summarized = []
    for item in items[:max_items]:
        if not isinstance(item, dict):
            continue
        summarized.append(_pick_keys(item, keys))

    return {
        "items": summarized,
        "total_items": len(items),
        "omitted_items": max(len(items) - len(summarized), 0),
    }


def _count_candidate_models(plan: Dict[str, Any]) -> int:
    baseline_models = plan.get("baseline_models", [])
    candidate_models = plan.get("candidate_models", [])
    hpo_baselines = [
        item
        for item in baseline_models
        if isinstance(item, dict) and item.get("hpo_enabled")
    ] if isinstance(baseline_models, list) else []
    return (
        (len(candidate_models) if isinstance(candidate_models, list) else 0)
        + len(hpo_baselines)
    )


def _summarize_model_search_hpo_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    trial_allocation = plan.get("trial_allocation", [])
    return {
        "enabled": plan.get("enabled"),
        "search_method": plan.get("search_method"),
        "budget_level": plan.get("budget_level"),
        "max_total_trials": plan.get("max_total_trials"),
        "max_parallel_trials": plan.get("max_parallel_trials"),
        "early_stopping": plan.get("early_stopping"),
        "fallback_method": plan.get("fallback_method"),
        "trial_allocation": _summarize_trial_allocation(trial_allocation),
    }


def _summarize_trial_allocation(
    allocations: Any,
    max_items: int = 40,
) -> Dict[str, Any]:
    if not isinstance(allocations, list):
        return {
            "items": [],
            "total_allocated_trials": 0,
            "total_allocation_items": 0,
            "omitted_allocation_items": 0,
        }

    summarized = []
    total_trials = 0
    for allocation in allocations:
        if not isinstance(allocation, dict):
            continue
        trials = allocation.get("max_trials") or 0
        total_trials += trials
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(
                    allocation,
                    ["model_id", "max_trials", "allocation_rationale"],
                )
            )

    return {
        "items": summarized,
        "total_allocated_trials": total_trials,
        "total_allocation_items": len(allocations),
        "omitted_allocation_items": max(len(allocations) - len(summarized), 0),
    }


def _summarize_search_space_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    spaces = plan.get("spaces", [])
    if not isinstance(spaces, list):
        return {
            "spaces": [],
            "total_search_spaces": 0,
            "total_parameters": 0,
        }

    summarized = []
    total_parameters = 0
    for space in spaces:
        if not isinstance(space, dict):
            continue
        parameters = space.get("parameters", [])
        if not isinstance(parameters, list):
            parameters = []
        total_parameters += len(parameters)
        summarized.append(
            {
                "model_id": space.get("model_id"),
                "search_space_id": space.get("search_space_id"),
                "parameter_count": len(parameters),
                "parameter_names": [
                    param.get("name")
                    for param in parameters
                    if isinstance(param, dict) and param.get("name")
                ],
                "overridden_parameters": [
                    {
                        "name": param.get("name"),
                        "override_rationale": param.get("override_rationale"),
                    }
                    for param in parameters
                    if isinstance(param, dict) and param.get("override_rationale")
                ],
            }
        )

    return {
        "spaces": summarized,
        "total_search_spaces": len(spaces),
        "total_parameters": total_parameters,
        "full_parameter_ranges_omitted": True,
    }


def _model_search_plan_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Model-search planning that combines workflow-level intent, "
            "model-ready dataset diagnostics, preprocessing outcomes, LLM "
            "strategy advice, and registry-backed system validation."
        ),
        "innovation_point": (
            "The module turns LLM advice into an auditable execution plan while "
            "enforcing model registry, HPO registry, single-baseline, trial "
            "budget, validation-strategy, and search-space constraints."
        ),
        "why_this_module_matters": (
            "It creates the bridge between data preparation and executable ML "
            "pipelines by deciding which models to compare, how much tuning "
            "budget to allocate, which hyperparameter spaces to expose, and "
            "which validation and evaluation settings downstream modules must use."
        ),
    }


def _model_search_plan_exclusions() -> list:
    return [
        "llm_request_json",
        "llm_response_json.raw",
        "raw prompt text",
        "full output schema",
        "complete context_json without summarization",
        "full search space parameter ranges",
        "full feature column list when too long",
        "model_ready_matrix_path",
        "preprocessing artifact local paths",
        "created_at",
        "updated_at",
        "random model search context identifiers",
    ]


def _summarize_pipeline_artifact_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "model_ready_exists": manifest.get("model_ready_exists"),
        "preprocessor_exists": manifest.get("preprocessor_exists"),
        "n_features": manifest.get("n_features"),
        "target_column": manifest.get("target_column"),
        "is_complete": manifest.get("is_complete"),
        "feature_columns": _summarize_feature_columns(
            manifest.get("feature_columns", [])
        ),
        "model_ready_matrix_path_recorded": bool(
            manifest.get("model_ready_matrix_path")
        ),
        "model_ready_matrix_path_excluded": bool(
            manifest.get("model_ready_matrix_path")
        ),
        "preprocessor_artifact_path_recorded": bool(
            manifest.get("preprocessor_artifact_path")
        ),
        "preprocessor_artifact_path_excluded": bool(
            manifest.get("preprocessor_artifact_path")
        ),
        "path_safety_policy": [
            "paths must not contain parent-directory escapes",
            "absolute artifact paths must be under an allowed artifact root",
            "relative paths are accepted only when they do not contain '..'",
        ],
    }


def _summarize_component_binding(binding_result: Dict[str, Any]) -> Dict[str, Any]:
    bindings = binding_result.get("bindings", [])
    if not isinstance(bindings, list):
        bindings = []

    summarized = []
    for binding in bindings:
        if not isinstance(binding, dict):
            continue
        summarized.append(
            _pick_keys(
                binding,
                [
                    "model_id",
                    "model_family",
                    "model_registry_valid",
                    "hpo_method",
                    "hpo_registry_valid",
                    "validation_strategy",
                    "validation_strategy_valid",
                    "primary_metric",
                    "metric_valid",
                    "preprocessor_artifact_bound",
                    "model_ready_matrix_bound",
                ],
            )
        )

    return {
        "bindings": summarized,
        "binding_count": len(bindings),
        "all_valid": binding_result.get("all_valid"),
        "errors": binding_result.get("errors", []),
    }


def _summarize_pipeline_specs(
    specs: Any,
    max_specs: int = 40,
) -> Dict[str, Any]:
    if not isinstance(specs, list):
        return {
            "items": [],
            "role_counts": {},
            "total_pipeline_specs": 0,
            "omitted_pipeline_specs": 0,
        }

    role_counts: Dict[str, int] = {}
    summarized = []
    for spec in specs:
        if not isinstance(spec, dict):
            continue
        role = spec.get("pipeline_role") or "unknown"
        role_counts[role] = role_counts.get(role, 0) + 1
        if len(summarized) < max_specs:
            safety_constraints = _pick_dict(spec.get("safety_constraints"))
            search_space = _pick_dict(spec.get("search_space"))
            item = _pick_keys(
                spec,
                [
                    "pipeline_role",
                    "model_id",
                    "model_family",
                    "model_display_name",
                    "priority",
                    "hpo_enabled",
                    "search_space_ref",
                    "validation_plan_ref",
                    "evaluation_plan_ref",
                    "component_bindings",
                    "execution_ready",
                    "warnings",
                ],
            )
            item["safety_constraints"] = _pick_keys(
                safety_constraints,
                [
                    "max_runtime_seconds",
                    "max_memory_mb",
                    "allow_unregistered_components",
                    "allow_dynamic_code",
                    "allow_network_access",
                ],
            )
            item["artifact_refs"] = {
                "input_artifact_ref_recorded": bool(spec.get("input_artifact_ref")),
                "input_artifact_ref_excluded": bool(spec.get("input_artifact_ref")),
                "preprocessor_artifact_ref_recorded": bool(
                    spec.get("preprocessor_artifact_ref")
                ),
                "preprocessor_artifact_ref_excluded": bool(
                    spec.get("preprocessor_artifact_ref")
                ),
            }
            item["search_space_summary"] = {
                "search_space_id": search_space.get("search_space_id"),
                "parameter_count": len(search_space.get("parameters", []) or []),
                "parameter_names": [
                    param.get("name")
                    for param in search_space.get("parameters", []) or []
                    if isinstance(param, dict) and param.get("name")
                ],
                "full_parameter_ranges_omitted": True,
            }
            summarized.append(item)

    return {
        "items": summarized,
        "role_counts": role_counts,
        "total_pipeline_specs": len(specs),
        "omitted_pipeline_specs": max(len(specs) - len(summarized), 0),
    }


def _count_pipeline_specs_by_role(specs: Any, role: str) -> int:
    if not isinstance(specs, list):
        return 0
    return sum(
        1
        for spec in specs
        if isinstance(spec, dict) and spec.get("pipeline_role") == role
    )


def _count_hpo_pipeline_specs(specs: Any) -> int:
    if not isinstance(specs, list):
        return 0
    return sum(
        1
        for spec in specs
        if isinstance(spec, dict) and bool(spec.get("hpo_enabled"))
    )


def _summarize_pipeline_trial_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    allocation = plan.get("trial_allocation", [])
    return {
        "hpo_enabled": plan.get("hpo_enabled"),
        "search_method": plan.get("search_method"),
        "max_total_trials": plan.get("max_total_trials"),
        "max_parallel_trials": plan.get("max_parallel_trials"),
        "trial_allocation": _summarize_pipeline_trial_allocation(allocation),
        "baseline_trial_policy": _pick_dict(plan.get("baseline_trial_policy")),
        "candidate_trial_policy": _pick_dict(plan.get("candidate_trial_policy")),
        "early_stopping_policy": _pick_dict(plan.get("early_stopping_policy")),
        "fallback_policy": _pick_dict(plan.get("fallback_policy")),
    }


def _summarize_pipeline_trial_allocation(
    allocation: Any,
    max_items: int = 40,
) -> Dict[str, Any]:
    if not isinstance(allocation, list):
        return {
            "items": [],
            "total_allocated_trials": 0,
            "total_allocation_items": 0,
            "omitted_allocation_items": 0,
        }

    summarized = []
    total_trials = 0
    role_counts: Dict[str, int] = {}
    for item in allocation:
        if not isinstance(item, dict):
            continue
        role = item.get("role") or "unknown"
        role_counts[role] = role_counts.get(role, 0) + 1
        total_trials += item.get("max_trials") or 0
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(item, ["model_id", "max_trials", "role"])
            )

    return {
        "items": summarized,
        "role_counts": role_counts,
        "total_allocated_trials": total_trials,
        "total_allocation_items": len(allocation),
        "omitted_allocation_items": max(len(allocation) - len(summarized), 0),
        "pipeline_spec_ids_excluded": True,
    }


def _summarize_pipeline_safety_check(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "is_safe": result.get("is_safe"),
        "checks": _pick_dict(result.get("checks")),
        "errors": result.get("errors", []),
        "warnings": result.get("warnings", []),
        "forbidden_content_policy": [
            "no dynamic Python code or imports",
            "no exec, eval, compile, subprocess, shell removal, or file-write patterns",
            "no direct fit, predict, transform, Pipeline, GridSearchCV, or RandomizedSearchCV code strings",
            "artifact paths must avoid parent-directory escapes",
        ],
    }


def _summarize_pipeline_llm_review(review: Dict[str, Any]) -> Dict[str, Any]:
    checklist = review.get("checklist", [])
    if not isinstance(checklist, list):
        checklist = []

    return {
        "enabled": review.get("enabled"),
        "review_status": review.get("review_status"),
        "execution_impact": review.get("execution_impact"),
        "risk_level": review.get("risk_level"),
        "confidence_level": review.get("confidence_level"),
        "checklist": _summarize_llm_review_checklist(checklist),
        "blocking_issues": _summarize_llm_review_risks(
            review.get("blocking_issues", [])
        ),
        "non_blocking_risks": _summarize_llm_review_risks(
            review.get("non_blocking_risks", [])
        ),
        "resource_warnings": review.get("resource_warnings", []),
        "future_improvement_suggestions": review.get(
            "future_improvement_suggestions",
            [],
        ),
        "normalization_notes": review.get("normalization_notes", []),
        "advisory_boundary": [
            "LLM review is non-blocking",
            "LLM review cannot approve, reject, modify, or execute pipeline specs",
            "system validation and safety checks remain authoritative",
        ],
    }


def _summarize_llm_review_checklist(
    checklist: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(checklist, list):
        return {"items": [], "status_counts": {}, "total_items": 0}

    status_counts: Dict[str, int] = {}
    items = []
    for item in checklist:
        if not isinstance(item, dict):
            continue
        status = item.get("status") or "unknown"
        status_counts[status] = status_counts.get(status, 0) + 1
        if len(items) < max_items:
            items.append(_pick_keys(item, ["dimension", "status", "comment"]))

    return {
        "items": items,
        "status_counts": status_counts,
        "total_items": len(checklist),
        "omitted_items": max(len(checklist) - len(items), 0),
    }


def _summarize_llm_review_risks(
    risks: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(risks, list):
        return {"items": [], "severity_counts": {}, "total_risks": 0}

    severity_counts: Dict[str, int] = {}
    items = []
    for risk in risks:
        if not isinstance(risk, dict):
            continue
        severity = risk.get("severity") or "unknown"
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
        if len(items) < max_items:
            items.append(
                _pick_keys(
                    risk,
                    ["category", "severity", "message", "suggested_action"],
                )
            )

    return {
        "items": items,
        "severity_counts": severity_counts,
        "total_risks": len(risks),
        "omitted_risks": max(len(risks) - len(items), 0),
    }


def _summarize_pipeline_execution_input(execution_input: Dict[str, Any]) -> Dict[str, Any]:
    pipeline_specs = execution_input.get("pipeline_specs", [])
    return {
        "ready_for_execution": execution_input.get("ready_for_execution"),
        "task_type": execution_input.get("task_type"),
        "target_column": execution_input.get("target_column"),
        "feature_columns": _summarize_feature_columns(
            execution_input.get("feature_columns", [])
        ),
        "pipeline_specs_count": len(pipeline_specs)
        if isinstance(pipeline_specs, list)
        else 0,
        "trial_plan_present": bool(execution_input.get("trial_plan")),
        "validation_plan": _pick_dict(execution_input.get("validation_plan")),
        "evaluation_plan": _pick_dict(execution_input.get("evaluation_plan")),
        "execution_constraints": _pick_dict(
            execution_input.get("execution_constraints")
        ),
        "model_ready_matrix_path_recorded": bool(
            execution_input.get("model_ready_matrix_path")
        ),
        "model_ready_matrix_path_excluded": bool(
            execution_input.get("model_ready_matrix_path")
        ),
        "preprocessor_artifact_path_recorded": bool(
            execution_input.get("preprocessor_artifact_path")
        ),
        "preprocessor_artifact_path_excluded": bool(
            execution_input.get("preprocessor_artifact_path")
        ),
        "fold_pipeline_spec_path_recorded": bool(
            execution_input.get("fold_pipeline_spec_path")
        ),
        "fold_pipeline_spec_path_excluded": bool(
            execution_input.get("fold_pipeline_spec_path")
        ),
    }


def _pipeline_generation_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Declarative pipeline-specification generation that converts "
            "model-search decisions into executable inputs without emitting "
            "dynamic training code."
        ),
        "innovation_point": (
            "The module combines artifact resolution, registry binding, "
            "pipeline bundle validation, explicit safety scanning, and "
            "non-blocking LLM advisory review before execution is allowed."
        ),
        "why_this_module_matters": (
            "It decouples AI-guided planning from model training by producing "
            "auditable, bounded execution specifications that downstream "
            "runners can consume reproducibly."
        ),
    }


def _pipeline_generation_exclusions() -> list:
    return [
        "llm_request_json",
        "llm_response_json.raw",
        "raw prompt text",
        "complete pipeline_json without summarization",
        "complete execution_input_json without summarization",
        "local artifact paths",
        "full feature column list when too long",
        "full search space parameter ranges",
        "random pipeline_generation_id",
        "random bundle_id",
        "random pipeline_spec_id",
        "random trial_plan_id",
        "created_at",
        "updated_at",
        "executable code strings",
    ]


def _summarize_fold_preprocessing_evidence(trial_results: Any) -> Dict[str, Any]:
    fold_results = _collect_fold_results(trial_results)
    return {
        "total_fold_results": len(fold_results),
        "fold_status_counts": _count_by_key(fold_results, "status"),
        "fold_failures_with_preprocessing_mentions": sum(
            1
            for fold in fold_results
            if "preprocessing" in str(fold.get("error_message", "")).lower()
        ),
        "note": (
            "Successful fold preprocessing is primarily evidenced by completed "
            "folds when a fold_pipeline_spec was present; raw fitted "
            "preprocessor objects are not serialized into the evidence package."
        ),
    }


def _summarize_actual_folds(trial_results: Any) -> Dict[str, Any]:
    fold_results = _collect_fold_results(trial_results)
    if not fold_results:
        return {
            "fold_count_observed": 0,
            "train_size_summary": {},
            "validation_size_summary": {},
        }

    train_sizes = [
        fold.get("train_size")
        for fold in fold_results
        if isinstance(fold.get("train_size"), (int, float))
    ]
    validation_sizes = [
        fold.get("validation_size")
        for fold in fold_results
        if isinstance(fold.get("validation_size"), (int, float))
    ]

    return {
        "fold_count_observed": len({fold.get("fold_index") for fold in fold_results}),
        "fold_result_count": len(fold_results),
        "train_size_summary": _numeric_summary(train_sizes),
        "validation_size_summary": _numeric_summary(validation_sizes),
    }


def _summarize_pipeline_run_results(
    pipeline_runs: Any,
    max_items: int = 40,
) -> Dict[str, Any]:
    if not isinstance(pipeline_runs, list):
        return {
            "items": [],
            "status_counts": {},
            "total_pipeline_runs": 0,
            "omitted_pipeline_runs": 0,
        }

    summarized = []
    for run in pipeline_runs:
        if not isinstance(run, dict):
            continue
        if len(summarized) < max_items:
            summarized.append(
                {
                    **_pick_keys(
                        run,
                        [
                            "pipeline_role",
                            "model_id",
                            "model_family",
                            "status",
                            "hpo_enabled",
                            "n_trials_planned",
                            "n_trials_completed",
                            "n_trials_failed",
                            "duration_seconds",
                            "warnings",
                            "error_message",
                        ],
                    ),
                    "best_trial_recorded": bool(run.get("best_trial_id")),
                    "model_artifact_count": len(
                        _as_list(run.get("model_artifact_paths"))
                    ),
                    "prediction_artifact_count": len(
                        _as_list(run.get("prediction_artifact_paths"))
                    ),
                }
            )

    return {
        "items": summarized,
        "status_counts": _count_by_key(pipeline_runs, "status"),
        "model_counts": _count_by_key(pipeline_runs, "model_id"),
        "total_pipeline_runs": len(pipeline_runs),
        "omitted_pipeline_runs": max(len(pipeline_runs) - len(summarized), 0),
        "random_pipeline_run_ids_excluded": True,
    }


def _summarize_training_trial_results(
    trial_results: Any,
    max_items: int = 50,
) -> Dict[str, Any]:
    if not isinstance(trial_results, list):
        return {
            "items": [],
            "status_counts": {},
            "trial_type_counts": {},
            "model_counts": {},
            "total_trials": 0,
            "omitted_trials": 0,
        }

    summarized = []
    error_messages = []
    for trial in trial_results:
        if not isinstance(trial, dict):
            continue
        if trial.get("error_message"):
            error_messages.append(trial)
        if len(summarized) < max_items:
            fold_results = trial.get("fold_results", [])
            if not isinstance(fold_results, list):
                fold_results = []
            summarized.append(
                {
                    **_pick_keys(
                        trial,
                        [
                            "model_id",
                            "trial_index",
                            "trial_type",
                            "status",
                            "raw_metric_values",
                            "duration_seconds",
                            "error_message",
                        ],
                    ),
                    "params": _compact_hyperparameters(trial.get("params", {})),
                    "fold_summary": _summarize_trial_folds(fold_results),
                    "prediction_artifact_count": len(
                        _as_list(trial.get("prediction_artifact_paths"))
                    ),
                    "model_artifact_count": len(
                        _as_list(trial.get("model_artifact_paths"))
                    ),
                }
            )

    return {
        "items": summarized,
        "status_counts": _count_by_key(trial_results, "status"),
        "trial_type_counts": _count_by_key(trial_results, "trial_type"),
        "model_counts": _count_by_key(trial_results, "model_id"),
        "failure_summary": _summarize_error_messages(error_messages),
        "total_trials": len(trial_results),
        "omitted_trials": max(len(trial_results) - len(summarized), 0),
        "random_trial_ids_excluded": True,
    }


def _summarize_trial_folds(fold_results: Any) -> Dict[str, Any]:
    if not isinstance(fold_results, list):
        return {"fold_count": 0, "status_counts": {}}

    durations = [
        fold.get("duration_seconds")
        for fold in fold_results
        if isinstance(fold, dict) and isinstance(fold.get("duration_seconds"), (int, float))
    ]
    return {
        "fold_count": len(fold_results),
        "status_counts": _count_by_key(fold_results, "status"),
        "duration_seconds_summary": _numeric_summary(durations),
        "raw_metric_keys": sorted(
            {
                key
                for fold in fold_results
                if isinstance(fold, dict)
                for key in _pick_dict(fold.get("raw_metric_values")).keys()
            }
        ),
        "artifact_paths_excluded": True,
        "full_tracebacks_excluded": True,
    }


def _collect_fold_results(trial_results: Any) -> list:
    if not isinstance(trial_results, list):
        return []
    folds = []
    for trial in trial_results:
        if not isinstance(trial, dict):
            continue
        fold_results = trial.get("fold_results", [])
        if isinstance(fold_results, list):
            folds.extend([fold for fold in fold_results if isinstance(fold, dict)])
    return folds


def _compact_hyperparameters(params: Any, max_items: int = 25) -> Dict[str, Any]:
    if not isinstance(params, dict):
        return {"items": {}, "parameter_count": 0}
    keys = list(params.keys())
    return {
        "items": {key: params.get(key) for key in keys[:max_items]},
        "parameter_count": len(keys),
        "omitted_parameters": max(len(keys) - max_items, 0),
    }


def _summarize_error_messages(items: list, max_examples: int = 5) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    examples = []
    for item in items:
        if not isinstance(item, dict):
            continue
        message = str(item.get("error_message") or "unknown")
        first_line = message.splitlines()[0][:160] if message else "unknown"
        counts[first_line] = counts.get(first_line, 0) + 1
        if len(examples) < max_examples:
            examples.append(
                {
                    "model_id": item.get("model_id"),
                    "status": item.get("status"),
                    "error_excerpt": first_line,
                }
            )
    return {
        "error_counts": counts,
        "examples": examples,
        "full_tracebacks_excluded": True,
    }


def _numeric_summary(values: list) -> Dict[str, Any]:
    cleaned = [value for value in values if isinstance(value, (int, float))]
    if not cleaned:
        return {"count": 0}
    return {
        "count": len(cleaned),
        "min": min(cleaned),
        "max": max(cleaned),
        "mean": round(sum(cleaned) / len(cleaned), 6),
    }


def _summarize_training_artifact_manifest(manifest: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "training_artifact_dir_recorded": bool(manifest.get("training_artifact_dir")),
        "training_artifact_dir_excluded": bool(manifest.get("training_artifact_dir")),
        "manifest_saved": bool(manifest.get("manifest_path")),
        "execution_result_saved": bool(manifest.get("execution_result_path")),
        "trial_results_saved": bool(manifest.get("trial_results_path")),
        "split_metadata_saved": bool(manifest.get("split_metadata_path")),
        "metric_evaluation_input_saved": bool(
            manifest.get("metric_evaluation_input_path")
        ),
        "log_saved": bool(manifest.get("log_path")),
        "prediction_artifact_count": len(_as_list(manifest.get("prediction_paths"))),
        "model_artifact_count": len(_as_list(manifest.get("model_paths"))),
        "artifact_paths_excluded": True,
    }


def _summarize_runtime_log(runtime_log: Dict[str, Any]) -> Dict[str, Any]:
    events = runtime_log.get("events", [])
    if not isinstance(events, list):
        events = []
    return {
        "status": runtime_log.get("status"),
        "duration_seconds": runtime_log.get("duration_seconds"),
        "warnings": runtime_log.get("warnings", []),
        "error_message": runtime_log.get("error_message"),
        "event_count": len(events),
        "event_level_counts": _count_by_key(events, "level"),
        "phase_markers_observed": _extract_runtime_phase_markers(events),
        "trial_summary": _pick_dict(runtime_log.get("trial_summary")),
        "full_event_log_excluded": True,
    }


def _extract_runtime_phase_markers(events: list, max_items: int = 20) -> list:
    markers = []
    for event in events:
        if not isinstance(event, dict):
            continue
        message = str(event.get("message", ""))
        if "[" in message and "/12]" in message:
            marker = message.split("]", 1)[0] + "]"
            if marker not in markers:
                markers.append(marker)
        if len(markers) >= max_items:
            break
    return markers


def _summarize_metric_evaluation_handoff(metric_input: Dict[str, Any]) -> Dict[str, Any]:
    trial_results = metric_input.get("trial_results", [])
    prediction_artifacts = metric_input.get("prediction_artifacts", [])
    model_artifacts = metric_input.get("model_artifacts", [])
    return {
        "ready_for_metric_evaluation": metric_input.get(
            "ready_for_metric_evaluation"
        ),
        "task_type": metric_input.get("task_type"),
        "target_column": metric_input.get("target_column"),
        "primary_metric": metric_input.get("primary_metric"),
        "metric_direction": metric_input.get("metric_direction"),
        "evaluation_plan": _pick_dict(metric_input.get("evaluation_plan")),
        "validation_plan": _pick_dict(metric_input.get("validation_plan")),
        "trial_result_count": len(trial_results) if isinstance(trial_results, list) else 0,
        "trial_status_counts": _count_by_key(
            trial_results if isinstance(trial_results, list) else [],
            "status",
        ),
        "prediction_artifact_count": len(prediction_artifacts)
        if isinstance(prediction_artifacts, list)
        else 0,
        "model_artifact_count": len(model_artifacts)
        if isinstance(model_artifacts, list)
        else 0,
        "artifact_paths_excluded": True,
        "full_trial_results_excluded": True,
    }


def _summarize_fold_metric_results(
    fold_results: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(fold_results, list):
        return {
            "items": [],
            "status_counts": {},
            "total_folds": 0,
            "omitted_folds": 0,
            "prediction_artifact_paths_excluded": True,
        }

    items = []
    metric_names = set()
    primary_values = []
    n_samples = []
    for fold in fold_results:
        if not isinstance(fold, dict):
            continue
        metrics = _pick_dict(fold.get("metrics"))
        metric_names.update(metrics.keys())
        if isinstance(fold.get("primary_metric_value"), (int, float)):
            primary_values.append(fold.get("primary_metric_value"))
        if isinstance(fold.get("n_samples"), (int, float)):
            n_samples.append(fold.get("n_samples"))
        if len(items) < max_items:
            items.append(
                {
                    "trial_id": fold.get("trial_id"),
                    "model_id": fold.get("model_id"),
                    "pipeline_spec_id": fold.get("pipeline_spec_id"),
                    "fold_index": fold.get("fold_index"),
                    "n_samples": fold.get("n_samples"),
                    "metric_names": sorted(metrics.keys()),
                    "primary_metric_value": fold.get("primary_metric_value"),
                    "status": fold.get("status"),
                    "warning_count": len(fold.get("warnings", []) or []),
                    "prediction_artifact_path_recorded": bool(
                        fold.get("prediction_artifact_path")
                    ),
                    "prediction_artifact_path_excluded": bool(
                        fold.get("prediction_artifact_path")
                    ),
                }
            )

    return {
        "items": items,
        "status_counts": _count_by_key(
            [f for f in fold_results if isinstance(f, dict)],
            "status",
        ),
        "metric_names_observed": sorted(metric_names),
        "primary_metric_value_summary": _numeric_summary(primary_values),
        "fold_sample_count_summary": _numeric_summary(n_samples),
        "total_folds": len(fold_results),
        "omitted_folds": max(len(fold_results) - len(items), 0),
        "prediction_artifact_paths_excluded": True,
        "raw_prediction_values_excluded": True,
    }


def _summarize_trial_metric_results(
    trial_results: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(trial_results, list):
        return {
            "items": [],
            "status_counts": {},
            "total_trials": 0,
            "omitted_trials": 0,
        }

    items = []
    primary_means = []
    primary_stds = []
    for trial in trial_results:
        if not isinstance(trial, dict):
            continue
        if isinstance(trial.get("primary_metric_mean"), (int, float)):
            primary_means.append(trial.get("primary_metric_mean"))
        if isinstance(trial.get("primary_metric_std"), (int, float)):
            primary_stds.append(trial.get("primary_metric_std"))
        if len(items) < max_items:
            params = _pick_dict(trial.get("params"))
            aggregated = _pick_dict(trial.get("aggregated_metrics"))
            items.append(
                {
                    "trial_id": trial.get("trial_id"),
                    "model_id": trial.get("model_id"),
                    "model_family": trial.get("model_family"),
                    "pipeline_role": trial.get("pipeline_role"),
                    "trial_type": trial.get("trial_type"),
                    "n_folds": trial.get("n_folds"),
                    "primary_metric_mean": trial.get("primary_metric_mean"),
                    "primary_metric_std": trial.get("primary_metric_std"),
                    "primary_metric_min": trial.get("primary_metric_min"),
                    "primary_metric_max": trial.get("primary_metric_max"),
                    "rank": trial.get("rank"),
                    "is_best_trial": trial.get("is_best_trial"),
                    "status": trial.get("status"),
                    "aggregated_metric_names": sorted(aggregated.keys()),
                    "parameter_names": sorted(params.keys()),
                    "full_params_excluded": bool(params),
                    "fold_metric_details_excluded": True,
                    "warning_count": len(trial.get("warnings", []) or []),
                }
            )

    dict_trials = [t for t in trial_results if isinstance(t, dict)]
    return {
        "items": items,
        "status_counts": _count_by_key(dict_trials, "status"),
        "model_counts": _count_by_key(dict_trials, "model_id"),
        "trial_type_counts": _count_by_key(dict_trials, "trial_type"),
        "pipeline_role_counts": _count_by_key(dict_trials, "pipeline_role"),
        "primary_metric_mean_summary": _numeric_summary(primary_means),
        "primary_metric_std_summary": _numeric_summary(primary_stds),
        "total_trials": len(trial_results),
        "omitted_trials": max(len(trial_results) - len(items), 0),
        "complete_fold_metrics_excluded": True,
        "complete_hyperparameters_excluded": True,
    }


def _summarize_pipeline_metric_results(
    pipeline_results: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(pipeline_results, list):
        return {
            "items": [],
            "total_pipeline_results": 0,
            "omitted_pipeline_results": 0,
        }

    items = []
    for pipeline in pipeline_results:
        if not isinstance(pipeline, dict):
            continue
        if len(items) < max_items:
            params = _pick_dict(pipeline.get("best_trial_params"))
            items.append(
                {
                    "pipeline_spec_id": pipeline.get("pipeline_spec_id"),
                    "model_id": pipeline.get("model_id"),
                    "model_family": pipeline.get("model_family"),
                    "pipeline_role": pipeline.get("pipeline_role"),
                    "n_trials_evaluated": pipeline.get("n_trials_evaluated"),
                    "best_trial_id": pipeline.get("best_trial_id"),
                    "best_primary_metric_value": pipeline.get(
                        "best_primary_metric_value"
                    ),
                    "mean_primary_metric_value": pipeline.get(
                        "mean_primary_metric_value"
                    ),
                    "std_primary_metric_value": pipeline.get(
                        "std_primary_metric_value"
                    ),
                    "rank": pipeline.get("rank"),
                    "is_best_model": pipeline.get("is_best_model"),
                    "best_trial_parameter_names": sorted(params.keys()),
                    "full_best_trial_params_excluded": bool(params),
                }
            )

    return {
        "items": items,
        "role_counts": _count_by_key(
            [p for p in pipeline_results if isinstance(p, dict)],
            "pipeline_role",
        ),
        "model_counts": _count_by_key(
            [p for p in pipeline_results if isinstance(p, dict)],
            "model_id",
        ),
        "total_pipeline_results": len(pipeline_results),
        "omitted_pipeline_results": max(len(pipeline_results) - len(items), 0),
    }


def _summarize_model_ranking(
    model_ranking: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(model_ranking, list):
        return {
            "items": [],
            "total_ranked_models": 0,
            "omitted_ranked_models": 0,
        }

    items = []
    for item in model_ranking:
        if not isinstance(item, dict):
            continue
        if len(items) < max_items:
            items.append(
                _pick_keys(
                    item,
                    [
                        "rank",
                        "model_id",
                        "model_family",
                        "pipeline_spec_id",
                        "best_trial_id",
                        "primary_metric",
                        "primary_metric_value",
                        "metric_direction",
                        "improvement_over_best_baseline",
                        "improvement_percentage",
                        "stability_score",
                        "ranking_reason",
                    ],
                )
            )

    return {
        "items": items,
        "total_ranked_models": len(model_ranking),
        "omitted_ranked_models": max(len(model_ranking) - len(items), 0),
        "full_ranking_excluded_when_large": True,
    }


def _summarize_baseline_comparison(comparison: Dict[str, Any]) -> Dict[str, Any]:
    return _pick_keys(
        comparison,
        [
            "baseline_available",
            "best_baseline_model_id",
            "best_baseline_trial_id",
            "best_baseline_metric_value",
            "best_candidate_model_id",
            "best_candidate_trial_id",
            "best_candidate_metric_value",
            "absolute_improvement",
            "relative_improvement_percentage",
            "candidate_beats_baseline",
            "comparison_notes",
        ],
    )


def _summarize_metric_validation(validation: Dict[str, Any]) -> Dict[str, Any]:
    return _pick_keys(
        validation,
        [
            "is_valid",
            "all_metrics_finite",
            "primary_metric_present",
            "ranking_consistent",
            "best_trial_in_results",
            "baseline_references_valid",
            "diagnosis_input_complete",
            "issues",
        ],
    )


def _summarize_result_diagnosis_handoff(
    result_diagnosis_input: Dict[str, Any],
) -> Dict[str, Any]:
    best_trial = _pick_dict(result_diagnosis_input.get("best_trial"))
    best_model = _pick_dict(result_diagnosis_input.get("best_model"))
    failed_summary = _pick_dict(
        result_diagnosis_input.get("failed_trials_summary")
    )
    return {
        "ready_for_result_diagnosis": result_diagnosis_input.get(
            "ready_for_result_diagnosis"
        ),
        "task_type": result_diagnosis_input.get("task_type"),
        "primary_metric": result_diagnosis_input.get("primary_metric"),
        "metric_direction": result_diagnosis_input.get("metric_direction"),
        "best_trial": _pick_keys(
            best_trial,
            [
                "trial_id",
                "model_id",
                "pipeline_spec_id",
                "primary_metric_mean",
                "primary_metric_std",
                "pipeline_role",
                "trial_type",
            ],
        ),
        "best_model": _pick_keys(
            best_model,
            ["model_id", "model_family", "rank", "primary_metric_value"],
        ),
        "ranking_item_count": len(
            _as_list(result_diagnosis_input.get("model_ranking"))
        ),
        "baseline_comparison_present": bool(
            result_diagnosis_input.get("baseline_comparison")
        ),
        "metric_summary_present": bool(
            result_diagnosis_input.get("metric_summary")
        ),
        "failed_trials_summary": {
            "n_failed_trials": failed_summary.get("n_failed_trials"),
            "n_successful_trials": failed_summary.get("n_successful_trials"),
            "failed_trial_count_listed": len(
                _as_list(failed_summary.get("failed_trial_ids"))
            ),
            "failed_trial_ids_excluded": True,
        },
        "stability_summary": _pick_dict(
            result_diagnosis_input.get("stability_summary")
        ),
        "evaluation_warnings": result_diagnosis_input.get(
            "evaluation_warnings",
            [],
        ),
    }


def _summarize_iteration_evidence_bundle(bundle: Dict[str, Any]) -> Dict[str, Any]:
    categories = [
        "ml_performance",
        "materials",
        "workflow_quality",
        "history_trends",
    ]
    return {
        "evidence_categories": {
            category: _summarize_iteration_evidence_items(
                bundle.get(category, [])
            )
            for category in categories
        },
        "total_evidence_items": sum(
            len(bundle.get(category, []) or [])
            for category in categories
            if isinstance(bundle.get(category, []), list)
        ),
        "extraction_policy": [
            "ML evidence is extracted from metric summary, baseline comparison, fold stability, ranking, and failed trial summaries",
            "materials evidence is extracted from task interpretation, dataset profile, feature engineering, and preprocessing outputs",
            "workflow-quality evidence is extracted from upstream planning and execution context when available",
            "history evidence is extracted from prior iteration decisions and prior metric evaluations",
        ],
        "full_evidence_bundle_excluded_when_large": True,
    }


def _summarize_iteration_evidence_items(
    items: Any,
    max_items: int = 12,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {
            "items": [],
            "type_counts": {},
            "source_module_counts": {},
            "total_items": 0,
            "omitted_items": 0,
        }

    summarized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(
                    item,
                    [
                        "evidence_type",
                        "source_module",
                        "source_field",
                        "value",
                        "interpretation",
                    ],
                )
            )

    dict_items = [item for item in items if isinstance(item, dict)]
    return {
        "items": summarized,
        "type_counts": _count_by_key(dict_items, "evidence_type"),
        "source_module_counts": _count_by_key(dict_items, "source_module"),
        "total_items": len(items),
        "omitted_items": max(len(items) - len(summarized), 0),
    }


def _summarize_iteration_system_checks(checks: Dict[str, Any]) -> Dict[str, Any]:
    boolean_checks = {
        key: value
        for key, value in checks.items()
        if isinstance(value, bool)
    }
    triggered = sorted(
        key for key, value in boolean_checks.items() if value is True
    )
    return {
        "triggered_checks": triggered,
        "triggered_count": len(triggered),
        "ml_rule_checks": _pick_keys(
            checks,
            [
                "weak_baseline_improvement",
                "high_fold_variance",
                "all_models_weak",
                "hpo_budget_limited",
                "candidate_underperforms_baseline",
                "unstable_best_model",
            ],
        ),
        "materials_rule_checks": _pick_keys(
            checks,
            [
                "small_sample_warning",
                "feature_count_low",
                "many_features_dropped",
                "physics_constraint_violated",
                "feature_materials_relevance_low",
                "chemical_space_coverage_low",
            ],
        ),
        "guard_rule_checks": _pick_keys(
            checks,
            [
                "max_iterations_reached",
                "no_improvement_trend",
                "repeated_root_cause",
            ],
        ),
        "additional_checks": _pick_dict(checks.get("additional_checks")),
        "warnings": checks.get("warnings", []),
        "rule_thresholds": {
            "weak_improvement_threshold": 0.05,
            "high_cv_threshold": 0.15,
            "high_fold_std_threshold": 0.10,
            "limited_hpo_successful_trial_threshold": 10,
            "small_sample_threshold": 200,
            "low_feature_threshold": 10,
            "high_dropped_feature_ratio": 0.50,
        },
        "materials_physics_constraints_checked": [
            "band_gap >= 0",
            "formation_energy <= 0",
            "bulk_modulus >= 0",
            "shear_modulus >= 0",
            "thermal_conductivity >= 0",
            "electrical_conductivity >= 0",
        ],
    }


def _summarize_iteration_reasoning(reasoning: Dict[str, Any]) -> Dict[str, Any]:
    task_completion = _pick_dict(reasoning.get("task_completion"))
    gap_analysis = _pick_dict(reasoning.get("gap_analysis"))
    root_cause = _pick_dict(reasoning.get("root_cause"))
    improvement = _pick_dict(reasoning.get("improvement_potential"))
    return {
        "task_completion": _pick_keys(
            task_completion,
            [
                "completion_level",
                "target_metric",
                "target_value",
                "actual_value",
                "gap_description",
                "physics_constraints_satisfied",
                "physics_violations",
            ],
        ),
        "performance_assessment": reasoning.get("performance_assessment"),
        "gap_analysis": _pick_keys(
            gap_analysis,
            [
                "primary_gap",
                "gap_magnitude",
                "contributing_factors",
            ],
        ),
        "root_cause": _pick_keys(
            root_cause,
            [
                "primary_root_cause",
                "dimension",
                "causal_chain",
                "upstream_stage_at_fault",
                "supporting_evidence",
            ],
        ),
        "improvement_potential": _pick_keys(
            improvement,
            ["estimate", "key_levers", "estimated_effort"],
        ),
        "final_reasoning_summary": reasoning.get("final_reasoning_summary"),
    }


def _summarize_iteration_iterate_path(
    iteration_plan: Dict[str, Any],
    revised_plan: Dict[str, Any],
    rerun_plan: Dict[str, Any],
    active: bool,
) -> Dict[str, Any]:
    stage_changes = iteration_plan.get("stage_changes", [])
    return {
        "active": active,
        "llm_iteration_plan": {
            "present": bool(iteration_plan),
            "rerun_from_stage": iteration_plan.get("rerun_from_stage"),
            "stage_changes": _summarize_iteration_stage_changes(stage_changes),
            "preserved_stages": iteration_plan.get("preserved_stages", []),
            "expected_improvement": iteration_plan.get("expected_improvement"),
            "estimated_remaining_iterations": iteration_plan.get(
                "estimated_remaining_iterations"
            ),
            "stop_condition": iteration_plan.get("stop_condition"),
        },
        "system_iteration_rerun_plan": _summarize_iteration_rerun_plan(
            rerun_plan
        ),
        "revised_workflow_plan": _summarize_revised_workflow_plan_for_iteration(
            revised_plan
        ),
    }


def _summarize_iteration_stage_changes(
    changes: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(changes, list):
        return {
            "items": [],
            "stage_counts": {},
            "action_counts": {},
            "total_stage_changes": 0,
            "omitted_stage_changes": 0,
        }

    items = []
    for change in changes:
        if not isinstance(change, dict):
            continue
        if len(items) < max_items:
            instructions = _pick_dict(change.get("specific_instructions"))
            item = _pick_keys(
                change,
                ["stage", "action", "description", "rationale"],
            )
            item["specific_instruction_keys"] = sorted(instructions.keys())
            item["specific_instructions_excluded"] = bool(instructions)
            items.append(item)

    dict_changes = [change for change in changes if isinstance(change, dict)]
    return {
        "items": items,
        "stage_counts": _count_by_key(dict_changes, "stage"),
        "action_counts": _count_by_key(dict_changes, "action"),
        "total_stage_changes": len(changes),
        "omitted_stage_changes": max(len(changes) - len(items), 0),
    }


def _summarize_iteration_rerun_plan(plan: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "present": bool(plan),
        "next_iteration_index": plan.get("next_iteration_index"),
        "rerun_from_stage": plan.get("rerun_from_stage"),
        "rerun_stages": plan.get("rerun_stages", []),
        "reuse_artifacts": plan.get("reuse_artifacts", []),
        "invalidate_artifacts": plan.get("invalidate_artifacts", []),
        "expected_improvement_targets": plan.get(
            "expected_improvement_targets",
            [],
        ),
        "minimum_improvement_threshold": plan.get(
            "minimum_improvement_threshold"
        ),
        "stop_after_next_iteration_if_no_gain": plan.get(
            "stop_after_next_iteration_if_no_gain"
        ),
        "reasoning": plan.get("reasoning"),
        "rerun_policy": [
            "the earliest changed stage determines rerun_from_stage",
            "all downstream stages from rerun_from_stage are invalidated",
            "upstream artifacts before rerun_from_stage are reused",
            "workflow_planning and feature_engineering changes force workflow planning rerun",
        ],
    }


def _summarize_revised_workflow_plan_for_iteration(
    plan: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "present": bool(plan),
        "status": plan.get("status"),
        "planning_mode": plan.get("planning_mode"),
        "changed_sections": plan.get("changed_sections", []),
        "preserved_sections": plan.get("preserved_sections", []),
        "iteration_guidance": _summarize_iteration_guidance(
            _pick_dict(plan.get("iteration_guidance"))
        ),
        "strategy_iteration_changes": {
            "feature_strategy": _summarize_strategy_iteration_changes(
                plan.get("feature_strategy")
            ),
            "model_strategy": _summarize_strategy_iteration_changes(
                plan.get("model_strategy")
            ),
            "hpo_strategy": _summarize_strategy_iteration_changes(
                plan.get("hpo_strategy")
            ),
            "validation_strategy": _summarize_strategy_iteration_changes(
                plan.get("validation_strategy")
            ),
            "evaluation_strategy": _summarize_strategy_iteration_changes(
                plan.get("evaluation_strategy")
            ),
        },
        "planning_warnings": plan.get("planning_warnings", []),
        "llm_reasoning_summary": plan.get("llm_reasoning_summary"),
        "full_revised_workflow_plan_excluded": True,
    }


def _summarize_iteration_guidance(guidance: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "iteration_index": guidance.get("iteration_index"),
        "decision": guidance.get("decision"),
        "confidence": guidance.get("confidence"),
        "root_cause": _pick_dict(guidance.get("root_cause")),
        "gap_analysis": _pick_dict(guidance.get("gap_analysis")),
        "improvement_potential": _pick_dict(
            guidance.get("improvement_potential")
        ),
        "stage_changes": _summarize_iteration_stage_changes(
            guidance.get("stage_changes", [])
        ),
        "final_reasoning_summary": guidance.get("final_reasoning_summary"),
    }


def _summarize_strategy_iteration_changes(strategy: Any) -> Dict[str, Any]:
    strategy_dict = _pick_dict(strategy)
    changes = _pick_dict(strategy_dict.get("_iteration_changes"))
    items = []
    for stage, change in changes.items():
        if not isinstance(change, dict):
            continue
        items.append(
            {
                "stage": stage,
                "action": change.get("action"),
                "description": change.get("description"),
                "rationale": change.get("rationale"),
                "specific_instruction_keys": sorted(
                    _pick_dict(change.get("specific_instructions")).keys()
                ),
                "specific_instructions_excluded": bool(
                    change.get("specific_instructions")
                ),
            }
        )

    return {
        "has_iteration_changes": bool(items),
        "changed_stages": sorted(changes.keys()),
        "items": items,
        "original_strategy_content_excluded": bool(strategy_dict),
    }


def _summarize_iteration_stop_path(
    stop_rationale: Dict[str, Any],
    active: bool,
) -> Dict[str, Any]:
    return {
        "active": active,
        "present": bool(stop_rationale),
        "primary_reason": stop_rationale.get("primary_reason"),
        "category": stop_rationale.get("category"),
        "supporting_reasons": stop_rationale.get("supporting_reasons", []),
        "best_result_summary": stop_rationale.get("best_result_summary"),
    }


def _extract_items(value: Any) -> list:
    if isinstance(value, dict):
        items = value.get("items", [])
        return items if isinstance(items, list) else []
    if isinstance(value, list):
        return value
    return []


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _summarize_global_feature_importance(
    items: Any,
    max_items: int = 30,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {
            "items": [],
            "method_counts": {},
            "feature_group_counts": {},
            "total_features_ranked": 0,
            "omitted_features": 0,
        }

    summarized = []
    importance_values = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("importance_value"), (int, float)):
            importance_values.append(item.get("importance_value"))
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(
                    item,
                    [
                        "feature_name",
                        "importance_value",
                        "importance_rank",
                        "importance_method",
                        "direction",
                        "feature_group",
                        "interpretation_hint",
                    ],
                )
            )

    dict_items = [item for item in items if isinstance(item, dict)]
    return {
        "items": summarized,
        "method_counts": _count_by_key(dict_items, "importance_method"),
        "feature_group_counts": _count_by_key(dict_items, "feature_group"),
        "importance_value_summary": _numeric_summary(importance_values),
        "total_features_ranked": len(items),
        "omitted_features": max(len(items) - len(summarized), 0),
        "full_importance_list_excluded_when_large": True,
    }


def _summarize_permutation_importance(
    items: Any,
    max_items: int = 20,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {
            "items": [],
            "total_permutation_items": 0,
            "omitted_permutation_items": 0,
        }

    summarized = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if len(summarized) < max_items:
            summarized.append(
                _pick_keys(
                    item,
                    [
                        "feature_name",
                        "importance_mean",
                        "importance_std",
                        "rank",
                        "n_repeats",
                    ],
                )
            )

    return {
        "items": summarized,
        "total_permutation_items": len(items),
        "omitted_permutation_items": max(len(items) - len(summarized), 0),
    }


def _summarize_shap_analysis(shap_summary: Dict[str, Any]) -> Dict[str, Any]:
    top_features = _as_list(shap_summary.get("top_shap_features"))
    return {
        "shap_available": shap_summary.get("shap_available"),
        "explainer_type": shap_summary.get("explainer_type"),
        "n_samples_explained": shap_summary.get("n_samples_explained"),
        "top_shap_features": [
            _pick_keys(
                item,
                ["feature_name", "mean_abs_shap", "rank", "direction_summary"],
            )
            for item in top_features[:20]
            if isinstance(item, dict)
        ],
        "total_top_shap_features": len(top_features),
        "omitted_top_shap_features": max(len(top_features) - 20, 0),
        "warnings": shap_summary.get("warnings", []),
        "shap_artifact_paths_recorded": bool(
            shap_summary.get("shap_artifact_paths")
        ),
        "shap_artifact_paths_excluded": bool(
            shap_summary.get("shap_artifact_paths")
        ),
        "raw_shap_values_excluded": True,
    }


def _summarize_cross_method_consensus(consensus: Dict[str, Any]) -> Dict[str, Any]:
    matrix = _pick_dict(consensus.get("rank_correlation_matrix"))
    divergent = _as_list(consensus.get("divergent_features"))
    return {
        "overall_agreement_score": consensus.get("overall_agreement_score"),
        "methods_compared": sorted(matrix.keys()),
        "rank_correlation_matrix": matrix,
        "consensus_features": _as_list(consensus.get("consensus_features")),
        "divergent_features": [
            _pick_keys(item, ["feature_name", "method_ranks", "rank_std"])
            for item in divergent[:10]
            if isinstance(item, dict)
        ],
        "total_divergent_features": len(divergent),
        "full_method_rankings_excluded": True,
    }


def _summarize_feature_group_from_importance(items: Any) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {
            "group_counts": {},
            "group_total_importance": {},
            "top_features_by_group": {},
        }

    group_counts: Dict[str, int] = {}
    group_importance: Dict[str, float] = {}
    top_by_group: Dict[str, list] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        group = item.get("feature_group") or "unknown"
        group_counts[group] = group_counts.get(group, 0) + 1
        value = item.get("importance_value")
        if isinstance(value, (int, float)):
            group_importance[group] = group_importance.get(group, 0.0) + float(value)
        top_by_group.setdefault(group, [])
        if len(top_by_group[group]) < 5:
            top_by_group[group].append(item.get("feature_name"))

    return {
        "group_counts": group_counts,
        "group_total_importance": {
            key: round(value, 6) for key, value in group_importance.items()
        },
        "top_features_by_group": top_by_group,
        "feature_lineage_grouping_used_when_available": True,
    }


def _summarize_material_insight(insight: Dict[str, Any]) -> Dict[str, Any]:
    patterns = _as_list(insight.get("top_material_patterns"))
    groups = _as_list(insight.get("feature_groups_interpretation"))
    return {
        "top_material_patterns": _summarize_material_patterns(patterns),
        "feature_groups_interpretation": _summarize_feature_group_interpretations(
            groups
        ),
        "domain_hypotheses": _as_list(insight.get("domain_hypotheses")),
        "limitations": _as_list(insight.get("limitations")),
        "confidence_level": insight.get("confidence_level"),
        "interpretation_boundary": (
            "Material insights are model-based associations and hypotheses, "
            "not causal physical conclusions."
        ),
    }


def _summarize_llm_interpretability_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "top_material_patterns": _summarize_material_patterns(
            _as_list(summary.get("top_material_patterns"))
        ),
        "feature_groups_interpretation": _summarize_feature_group_interpretations(
            _as_list(summary.get("feature_groups_interpretation"))
        ),
        "domain_hypotheses": _as_list(summary.get("domain_hypotheses")),
        "limitations": _as_list(summary.get("limitations")),
        "human_review_notes": _as_list(summary.get("human_review_notes")),
        "confidence_level": summary.get("confidence_level"),
    }


def _summarize_material_patterns(patterns: Any, max_items: int = 10) -> Dict[str, Any]:
    patterns = _as_list(patterns)

    items = []
    for item in patterns:
        if not isinstance(item, dict):
            continue
        if len(items) < max_items:
            items.append(
                _pick_keys(
                    item,
                    [
                        "pattern",
                        "supporting_features",
                        "possible_material_meaning",
                        "evidence_strength",
                        "caution",
                    ],
                )
            )

    return {
        "items": items,
        "strength_counts": _count_by_key(
            [item for item in patterns if isinstance(item, dict)],
            "evidence_strength",
        ),
        "total_patterns": len(patterns),
        "omitted_patterns": max(len(patterns) - len(items), 0),
    }


def _summarize_feature_group_interpretations(
    groups: Any,
    max_items: int = 10,
) -> Dict[str, Any]:
    groups = _as_list(groups)
    items = [
        _pick_keys(item, ["feature_group", "summary"])
        for item in groups[:max_items]
        if isinstance(item, dict)
    ]
    return {
        "items": items,
        "total_groups": len(groups),
        "omitted_groups": max(len(groups) - len(items), 0),
    }


def _summarize_local_explanations(
    items: Any,
    max_items: int = 10,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {
            "items": [],
            "total_local_explanations": 0,
            "local_shap_values_excluded": True,
        }

    summarized = []
    errors = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("prediction_error"), (int, float)):
            errors.append(item.get("prediction_error"))
        if len(summarized) < max_items:
            summarized.append(
                {
                    "sample_id_recorded": bool(item.get("sample_id")),
                    "sample_id_excluded": bool(item.get("sample_id")),
                    "y_true": item.get("y_true"),
                    "y_pred": item.get("y_pred"),
                    "prediction_error": item.get("prediction_error"),
                    "top_positive_features": _as_list(
                        item.get("top_positive_features")
                    )[:3],
                    "top_negative_features": _as_list(
                        item.get("top_negative_features")
                    )[:3],
                    "local_explanation_summary": item.get(
                        "local_explanation_summary"
                    ),
                    "local_shap_values_excluded": bool(
                        item.get("local_shap_values")
                    ),
                }
            )

    return {
        "items": summarized,
        "prediction_error_summary": _numeric_summary(errors),
        "total_local_explanations": len(items),
        "omitted_local_explanations": max(len(items) - len(summarized), 0),
        "local_shap_values_excluded": True,
    }


def _summarize_high_error_samples(
    items: Any,
    max_items: int = 10,
) -> Dict[str, Any]:
    if not isinstance(items, list):
        return {"items": [], "total_high_error_samples": 0}

    summarized = []
    abs_errors = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if isinstance(item.get("absolute_error"), (int, float)):
            abs_errors.append(item.get("absolute_error"))
        if len(summarized) < max_items:
            summarized.append(
                {
                    "sample_id_recorded": bool(item.get("sample_id")),
                    "sample_id_excluded": bool(item.get("sample_id")),
                    "absolute_error": item.get("absolute_error"),
                    "relative_error": item.get("relative_error"),
                    "error_rank": item.get("error_rank"),
                    "possible_error_factors": _as_list(
                        item.get("possible_error_factors")
                    ),
                    "feature_pattern_summary": item.get(
                        "feature_pattern_summary"
                    ),
                    "review_suggestion": item.get("review_suggestion"),
                }
            )

    return {
        "items": summarized,
        "absolute_error_summary": _numeric_summary(abs_errors),
        "total_high_error_samples": len(items),
        "omitted_high_error_samples": max(len(items) - len(summarized), 0),
    }


def _summarize_residual_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    residuals = result.get("residuals", [])
    predicted = result.get("predicted_values", [])
    segments = result.get("systematic_error_segments", [])
    histogram = result.get("histogram_bins", [])
    return {
        "r_squared": result.get("r_squared"),
        "rmse": result.get("rmse"),
        "residual_mean": result.get("residual_mean"),
        "residual_std": result.get("residual_std"),
        "histogram_bin_count": len(histogram) if isinstance(histogram, list) else 0,
        "systematic_error_segments": (
            segments[:10] if isinstance(segments, list) else []
        ),
        "total_systematic_error_segments": (
            len(segments) if isinstance(segments, list) else 0
        ),
        "residual_count": len(residuals) if isinstance(residuals, list) else 0,
        "predicted_value_count": len(predicted) if isinstance(predicted, list) else 0,
        "raw_residuals_excluded": True,
        "raw_predicted_values_excluded": True,
    }


def _summarize_correlation_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    matrix = result.get("feature_correlation_matrix", [])
    feature_names = result.get("feature_names", [])
    target_corr = result.get("target_correlations", [])
    high_pairs = result.get("high_correlation_pairs", [])
    return {
        "feature_count_in_matrix": len(feature_names)
        if isinstance(feature_names, list)
        else 0,
        "matrix_present": bool(matrix),
        "matrix_excluded": bool(matrix),
        "top_target_correlations": (
            target_corr[:20] if isinstance(target_corr, list) else []
        ),
        "high_correlation_pairs": (
            high_pairs[:20] if isinstance(high_pairs, list) else []
        ),
        "total_target_correlations": (
            len(target_corr) if isinstance(target_corr, list) else 0
        ),
        "total_high_correlation_pairs": (
            len(high_pairs) if isinstance(high_pairs, list) else 0
        ),
        "error": result.get("error"),
    }


def _summarize_partial_dependence(result: Dict[str, Any]) -> Dict[str, Any]:
    pdp_1d = _as_list(result.get("pdp_1d"))
    pdp_2d = _as_list(result.get("pdp_2d"))

    return {
        "pdp_1d": [
            {
                "feature_name": item.get("feature_name"),
                "grid_count": len(_as_list(item.get("grid_values"))),
                "pdp_value_count": len(_as_list(item.get("pdp_values"))),
                "trend_summary": _describe_pdp_values(
                    _as_list(item.get("pdp_values"))
                ),
                "grid_values_excluded": True,
                "pdp_values_excluded": True,
            }
            for item in pdp_1d[:15]
            if isinstance(item, dict)
        ],
        "pdp_2d": [
            {
                "feature_1": item.get("feature_1"),
                "feature_2": item.get("feature_2"),
                "grid_1_count": len(_as_list(item.get("grid_1"))),
                "grid_2_count": len(_as_list(item.get("grid_2"))),
                "pdp_matrix_excluded": bool(item.get("pdp_matrix")),
            }
            for item in pdp_2d[:10]
            if isinstance(item, dict)
        ],
        "total_pdp_1d": len(pdp_1d),
        "total_pdp_2d": len(pdp_2d),
        "full_pdp_grids_excluded": True,
    }


def _describe_pdp_values(values: Any) -> str:
    if not isinstance(values, list) or len(values) < 2:
        return "insufficient data"
    numeric = [v for v in values if isinstance(v, (int, float))]
    if len(numeric) < 2:
        return "insufficient numeric data"
    first = numeric[0]
    last = numeric[-1]
    value_range = max(numeric) - min(numeric)
    if abs(value_range) < 1e-12:
        return "flat"
    change = last - first
    if abs(change) / max(abs(value_range), 1e-12) < 0.1:
        return "mostly flat"
    diffs = [numeric[i + 1] - numeric[i] for i in range(len(numeric) - 1)]
    sign_changes = sum(
        1
        for i in range(1, len(diffs))
        if diffs[i] * diffs[i - 1] < 0
    )
    direction = "increasing" if change > 0 else "decreasing"
    if sign_changes > 1:
        return f"non_monotonic_generally_{direction}"
    return direction


def _summarize_physics_constraint_check(result: Dict[str, Any]) -> Dict[str, Any]:
    constraints = result.get("constraints", [])
    if not isinstance(constraints, list):
        constraints = []
    return {
        "passed": result.get("passed"),
        "constraints": [
            {
                **_pick_keys(
                    item,
                    [
                        "constraint_name",
                        "description",
                        "expected",
                        "actual",
                        "passed",
                        "severity",
                        "n_violations",
                        "violation_rate",
                    ],
                ),
                "violating_sample_indices_recorded": bool(
                    item.get("violating_sample_indices")
                ),
                "violating_sample_indices_excluded": bool(
                    item.get("violating_sample_indices")
                ),
            }
            for item in constraints
            if isinstance(item, dict)
        ],
        "constraint_count": len(constraints),
        "supported_default_constraints": [
            "band_gap",
            "formation_energy",
            "bulk_modulus",
            "shear_modulus",
            "thermal_conductivity",
            "electrical_conductivity",
            "density",
            "melting_point",
        ],
    }


def _summarize_interpretability_final_output_input(
    final_output_input: Dict[str, Any],
) -> Dict[str, Any]:
    global_importance = _as_list(final_output_input.get("global_feature_importance"))
    prediction_paths = _as_list(final_output_input.get("prediction_artifact_paths"))
    return {
        "ready_for_final_output": final_output_input.get(
            "ready_for_final_output"
        ),
        "final_model_id": final_output_input.get("final_model_id"),
        "final_trial_id": final_output_input.get("final_trial_id"),
        "model_artifact_path_recorded": bool(
            final_output_input.get("model_artifact_path")
        ),
        "model_artifact_path_excluded": bool(
            final_output_input.get("model_artifact_path")
        ),
        "prediction_artifact_count": len(prediction_paths),
        "prediction_artifact_paths_excluded": True,
        "metric_summary": _pick_dict(final_output_input.get("metric_summary")),
        "selection_summary": _pick_dict(
            final_output_input.get("selection_summary")
        ),
        "global_feature_importance_count": len(global_importance),
        "shap_summary_present": bool(final_output_input.get("shap_summary")),
        "material_insight_summary_present": bool(
            final_output_input.get("material_insight_summary")
        ),
        "interpretability_artifact_refs_recorded": bool(
            final_output_input.get("interpretability_artifacts")
        ),
        "interpretability_artifact_refs_excluded": bool(
            final_output_input.get("interpretability_artifacts")
        ),
        "workflow_trace_refs_recorded": bool(
            final_output_input.get("workflow_trace_refs")
        ),
        "workflow_trace_refs_excluded": bool(
            final_output_input.get("workflow_trace_refs")
        ),
    }


def _summarize_interpretability_artifact_manifest(
    manifest: Dict[str, Any],
) -> Dict[str, Any]:
    keys = [
        "manifest_path",
        "interpretability_analysis_result_path",
        "global_feature_importance_path",
        "permutation_importance_path",
        "shap_values_path",
        "shap_summary_path",
        "local_explanations_path",
        "high_error_sample_analysis_path",
        "feature_group_summary_path",
        "material_insight_summary_path",
        "llm_interpretability_summary_path",
        "final_output_input_path",
        "cross_method_consensus_path",
        "partial_dependence_path",
        "residual_analysis_path",
        "correlation_analysis_path",
        "physics_constraint_check_path",
    ]
    return {
        "saved_artifacts": {
            key.replace("_path", "_saved"): bool(manifest.get(key))
            for key in keys
        },
        "artifact_paths_excluded": True,
    }


def _interpretability_analysis_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Transforms the best-performing automated model into auditable "
            "feature-level, sample-level, error-level, and materials-domain "
            "interpretability evidence."
        ),
        "innovation_point": (
            "The module combines model-family-aware method selection, "
            "multi-method feature importance, SHAP, cross-method consensus, "
            "feature-lineage grouping, residual and high-error analysis, "
            "physics constraint checks, and LLM-constrained materials "
            "summarization."
        ),
        "why_this_module_matters": (
            "It bridges predictive performance and scientific reporting by "
            "framing model behavior as evidence-backed materials hypotheses "
            "while preserving numerical provenance and preventing causal "
            "overclaims."
        ),
    }


def _interpretability_analysis_exclusions() -> list:
    return [
        "complete model artifact path",
        "complete prediction artifact paths",
        "complete model-ready matrix path",
        "complete feature matrix",
        "complete SHAP values arrays",
        "complete local SHAP value dictionaries",
        "complete residuals array",
        "complete predicted_values array",
        "complete feature correlation matrix",
        "complete PDP grid values and PDP matrices",
        "violating sample indices",
        "artifact local paths",
        "complete LLM request prompt and user message",
        "complete raw LLM response",
        "traceback strings",
        "random interpretability_analysis_id",
        "random metric_evaluation_id",
        "random pipeline_execution_id",
        "created_at",
        "updated_at",
        "executable code, SQL, shell commands, or training scripts",
    ]


def _iteration_decision_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Closed-loop workflow control that turns evaluation results, "
            "materials constraints, deterministic rules, and iteration history "
            "into an explicit stop-or-iterate decision."
        ),
        "innovation_point": (
            "The module combines rule-based diagnostics with schema-constrained "
            "LLM reasoning, validates and normalizes the decision, and converts "
            "natural-language root-cause analysis into a bounded rerun plan "
            "that the automated workflow can execute."
        ),
        "why_this_module_matters": (
            "It prevents blind repeated AutoML runs by deciding whether further "
            "optimization is justified, where the workflow should restart, "
            "which artifacts can be reused, and what improvement threshold "
            "should govern the next iteration."
        ),
    }


def _iteration_decision_exclusions() -> list:
    return [
        "complete llm_request_json.system_prompt",
        "complete llm_request_json.user_message",
        "complete llm_response_json.raw_response",
        "complete upstream context",
        "complete evidence bundle when large",
        "complete revised workflow plan",
        "artifact local paths",
        "traceback strings",
        "executable code or shell commands",
        "SQL snippets",
        "training script text",
        "random iteration_decision_id",
        "random metric_evaluation_id",
        "random pipeline_execution_id",
        "created_at",
        "updated_at",
    ]


def _metric_evaluation_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Independent metric computation and model ranking from prediction "
            "artifacts rather than direct reuse of training logs."
        ),
        "innovation_point": (
            "The module creates an auditable evaluation bridge: fold-level "
            "metrics, trial aggregation, direction-aware ranking, baseline "
            "comparison, validation checks, and a structured Result Diagnosis "
            "handoff are produced in one controlled stage."
        ),
        "why_this_module_matters": (
            "It closes the loop between automated model training and scientific "
            "model selection by converting raw experiment outputs into compact, "
            "validated, and comparable evidence for diagnosis, interpretation, "
            "and final reporting."
        ),
    }


def _metric_evaluation_exclusions() -> list:
    return [
        "complete evaluation_json without summarization",
        "complete fold_metric_results when large",
        "complete trial_metric_results when large",
        "complete model_ranking_json when large",
        "raw prediction values",
        "prediction artifact paths",
        "trained model files",
        "evaluation artifact local paths",
        "per-sample residuals or classification errors",
        "complete hyperparameter dictionaries",
        "complete traceback strings",
        "random metric_evaluation_id",
        "random pipeline_execution_id",
        "random trial_id",
        "random fold_metric_id",
        "created_at",
        "updated_at",
    ]


def _pipeline_execution_paper_relevance() -> Dict[str, Any]:
    return {
        "methodological_value": (
            "Controlled execution of declarative pipeline specifications into "
            "fold-level model training, prediction artifacts, runtime logs, and "
            "metric-evaluation-ready outputs."
        ),
        "innovation_point": (
            "The module preserves the boundary between AI planning and training "
            "by using a controlled executor, registry-only model factory, "
            "fold-safe preprocessing, timeout handling, artifact manifests, and "
            "structured metric handoff."
        ),
        "why_this_module_matters": (
            "It turns the automated workflow into reproducible experiments while "
            "avoiding arbitrary code execution and preserving enough trial/fold "
            "evidence for downstream evaluation, diagnosis, and interpretation."
        ),
    }


def _pipeline_execution_exclusions() -> list:
    return [
        "complete execution_json without summarization",
        "complete runtime_log_json.events",
        "complete metric_evaluation_input_json.trial_results",
        "raw prediction values",
        "trained model files",
        "artifact local paths",
        "full feature column list when too long",
        "train_indices and validation_indices",
        "complete fold tracebacks",
        "random pipeline_execution_id",
        "random trial_id",
        "random pipeline_run_id",
        "random pipeline_spec_id",
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
        "large per-fold metric details",
    ]


def _summarize_invalid_rows(invalid_rows: Any) -> Dict[str, Any]:
    if not isinstance(invalid_rows, dict):
        return {}
    return {
        "count": invalid_rows.get("count", 0),
        "example_count": len(invalid_rows.get("examples", []) or []),
        "examples": (invalid_rows.get("examples", []) or [])[:5],
    }


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _truncate(value: Optional[str], max_chars: int) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
