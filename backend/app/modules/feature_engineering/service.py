import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.feature_engineering.model import FeatureEngineering
from app.modules.feature_engineering.repository import FeatureEngineeringRepository
from app.modules.feature_engineering.schemas import (
    FeatureEngineeringCreateRequest,
    FeatureEngineeringResponse,
    FeaturePreviewResponse,
)
from app.modules.feature_engineering.context_builder import build_feature_engineering_context
from app.modules.feature_engineering.data_loader_adapter import reload_raw_data
from app.modules.feature_engineering.strategy_resolver import resolve_feature_strategy
from app.modules.feature_engineering.featurizers.composition_featurizer import CompositionFeaturizer
from app.modules.feature_engineering.featurizers.descriptor_featurizer import DescriptorFeaturizer
from app.modules.feature_engineering.featurizers.structure_featurizer import StructureFeaturizer
from app.modules.feature_engineering.featurizers.featurizer_router import (
    get_featurizer_instance,
    get_executable_featurizers,
)
from app.modules.feature_engineering.feature_matrix_builder import (
    build_feature_matrix,
    get_feature_schema,
)
from app.modules.feature_engineering.checkers.feature_quality_checker import check_feature_quality
from app.modules.feature_engineering.artifact_manager import (
    save_feature_artifact,
    read_preview_from_artifact,
)
from app.modules.feature_engineering.builder import build_feature_engineering_object
from app.modules.feature_engineering.enums import (
    FeatureEngineeringStatus,
    FeatureType,
    InputModality,
)
from app.modules.feature_engineering.exceptions import (
    FeatureEngineeringNotFoundException,
    FeatureEngineeringUpstreamNotReadyException,
    FeatureStrategyMissingException,
    RawDataLoadException,
    InputModalityUnsupportedException,
    FeaturizerNotAvailableException,
    FeatureGenerationException,
    FeatureMatrixInvalidException,
    FeatureArtifactSaveException,
)

logger = logging.getLogger(__name__)


class FeatureEngineeringService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.fe_repo = FeatureEngineeringRepository()

    def create_feature_engineering(
        self, session: Session, task_id: str, request: FeatureEngineeringCreateRequest,
    ) -> FeatureEngineeringResponse:
        fe_id = f"feat_{uuid.uuid4().hex[:8]}"
        all_warnings = []
        all_errors = []

        # --- 1. Build upstream context ---
        try:
            context = build_feature_engineering_context(session, task_id)
        except (FeatureEngineeringUpstreamNotReadyException, FeatureStrategyMissingException):
            failed = FeatureEngineering(
                id=fe_id,
                task_id=task_id,
                status=FeatureEngineeringStatus.BLOCKED,
                error_message="Upstream not ready or feature strategy missing.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fe_repo.create(session, failed)
            raise

        # --- 2. Load raw data ---
        data_context = context.get("data_context") or {}
        raw_df, loading_summary = reload_raw_data(data_context)

        input_modality = data_context.get("input_modality", "")
        target_column = data_context.get("target_column")

        # --- 3. Resolve feature strategy ---
        feature_context = context.get("feature_context") or {}
        resolved = resolve_feature_strategy(feature_context, input_modality)
        resolved_dict = resolved.model_dump()

        # --- 4. Select and run featurizers ---
        featurization_result = self._run_featurizers(
            raw_df, context, resolved_dict, input_modality
        )
        if featurization_result["status"] == "failed":
            all_errors.extend(featurization_result.get("errors", []))
            failed = FeatureEngineering(
                id=fe_id,
                task_id=task_id,
                interpretation_id=context["interpretation_id"],
                dataset_profile_id=context["dataset_profile_id"],
                workflow_plan_id=context["workflow_plan_id"],
                status=FeatureEngineeringStatus.FAILED,
                input_modality=input_modality,
                feature_type=resolved_dict.get("feature_type"),
                error_message="; ".join(all_errors),
                feature_json={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fe_repo.create(session, failed)
            raise FeatureGenerationException("; ".join(all_errors))

        all_warnings.extend(featurization_result.get("warnings", []))

        feature_df = featurization_result["feature_dataframe"]
        if feature_df is None:
            failed = FeatureEngineering(
                id=fe_id,
                task_id=task_id,
                interpretation_id=context["interpretation_id"],
                dataset_profile_id=context["dataset_profile_id"],
                workflow_plan_id=context["workflow_plan_id"],
                status=FeatureEngineeringStatus.FAILED,
                input_modality=input_modality,
                feature_type=resolved_dict.get("feature_type"),
                error_message="Featurization produced no feature dataframe.",
                feature_json={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fe_repo.create(session, failed)
            raise FeatureGenerationException("Featurization produced no feature dataframe.")

        # --- 5. Build feature matrix ---
        feature_matrix = build_feature_matrix(raw_df, feature_df, target_column)

        # --- 6. Check feature quality ---
        target_series = raw_df[target_column] if target_column and target_column in raw_df.columns else None
        quality_result = check_feature_quality(feature_df, target_series)
        all_warnings.extend(quality_result.get("warnings", []))
        all_errors.extend(quality_result.get("errors", []))

        if not quality_result.get("is_valid_feature_matrix"):
            failed = FeatureEngineering(
                id=fe_id,
                task_id=task_id,
                interpretation_id=context["interpretation_id"],
                dataset_profile_id=context["dataset_profile_id"],
                workflow_plan_id=context["workflow_plan_id"],
                status=FeatureEngineeringStatus.FAILED,
                input_modality=input_modality,
                feature_type=resolved_dict.get("feature_type"),
                n_samples=len(feature_df),
                n_features=len(feature_df.columns),
                target_column=target_column,
                error_message="; ".join(all_errors),
                feature_json={},
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fe_repo.create(session, failed)
            raise FeatureMatrixInvalidException("; ".join(all_errors))

        # --- 7. Save feature artifact ---
        try:
            artifact_result = save_feature_artifact(fe_id, feature_matrix)
        except FeatureArtifactSaveException:
            failed = FeatureEngineering(
                id=fe_id,
                task_id=task_id,
                interpretation_id=context["interpretation_id"],
                dataset_profile_id=context["dataset_profile_id"],
                workflow_plan_id=context["workflow_plan_id"],
                status=FeatureEngineeringStatus.FAILED,
                input_modality=input_modality,
                feature_type=resolved_dict.get("feature_type"),
                n_samples=len(feature_df),
                n_features=len(feature_df.columns),
                target_column=target_column,
                error_message="Failed to save feature artifact.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fe_repo.create(session, failed)
            raise

        # --- 8. Build feature schema ---
        feature_groups_list = featurization_result.get("feature_groups", [])
        feature_schema = get_feature_schema(feature_df, quality_result, feature_groups_list)

        # --- 9. Determine status ---
        if all_errors:
            status = FeatureEngineeringStatus.FAILED
        elif all_warnings:
            status = FeatureEngineeringStatus.COMPLETED_WITH_WARNING
        else:
            status = FeatureEngineeringStatus.COMPLETED

        # --- 10. Build Feature Engineering Object ---
        fe_object = build_feature_engineering_object(
            feature_engineering_id=fe_id,
            task_id=task_id,
            context=context,
            status=status,
            featurization_result=featurization_result,
            artifact_result=artifact_result,
            feature_schema=feature_schema,
            quality_result=quality_result,
            resolved_strategy=resolved_dict,
            warnings=all_warnings,
            errors=all_errors,
        )

        # --- 11. Persist ---
        fe_model = FeatureEngineering(
            id=fe_id,
            task_id=context["task_id"],
            interpretation_id=context["interpretation_id"],
            dataset_profile_id=context["dataset_profile_id"],
            workflow_plan_id=context["workflow_plan_id"],
            status=status,
            input_modality=input_modality,
            feature_type=resolved_dict.get("feature_type"),
            n_samples=artifact_result.get("n_samples"),
            n_features=artifact_result.get("n_features"),
            target_column=target_column,
            artifact_id=artifact_result.get("artifact_id"),
            artifact_path=artifact_result.get("file_path"),
            is_ready_for_pipeline=fe_object.downstream_input.ready_for_pipeline_generation,
            feature_json=fe_object.model_dump(mode="json"),
            preview_json=artifact_result.get("preview_json"),
            error_message=None if all_errors == [] else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fe_repo.create(session, fe_model)

        return fe_object

    def get_feature_engineering(self, session: Session, fe_id: str) -> FeatureEngineeringResponse:
        fe = self.fe_repo.get_by_id(session, fe_id)
        if not fe:
            raise FeatureEngineeringNotFoundException(
                f"Feature engineering with id {fe_id} not found."
            )
        return self._to_response(fe)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> FeatureEngineeringResponse:
        self._check_task_exists(session, task_id)
        fe = self.fe_repo.get_latest_by_task_id(session, task_id)
        if not fe:
            raise FeatureEngineeringNotFoundException(
                f"No feature engineering found for task {task_id}."
            )
        return self._to_response(fe)

    def rerun_feature_engineering(
        self, session: Session, task_id: str, request: FeatureEngineeringCreateRequest,
    ) -> FeatureEngineeringResponse:
        return self.create_feature_engineering(session, task_id, request)

    def get_preview(self, session: Session, fe_id: str) -> FeaturePreviewResponse:
        fe = self.fe_repo.get_by_id(session, fe_id)
        if not fe:
            raise FeatureEngineeringNotFoundException(
                f"Feature engineering with id {fe_id} not found."
            )

        # Try preview_json first
        if fe.preview_json:
            return FeaturePreviewResponse(
                columns=fe.preview_json.get("columns", []),
                preview_rows=fe.preview_json.get("preview_rows", 0),
                total_rows=fe.preview_json.get("total_rows", 0),
                rows=fe.preview_json.get("rows", []),
            )

        # Fallback: read from artifact
        preview = read_preview_from_artifact(fe_id)
        return FeaturePreviewResponse(
            columns=preview.get("columns", []),
            preview_rows=preview.get("preview_rows", 0),
            total_rows=preview.get("total_rows", 0),
            rows=preview.get("rows", []),
        )

    def _run_featurizers(self, raw_df, context, resolved_strategy, input_modality) -> dict:
        """Run multiple featurizers based on the resolved strategy.

        Each featurizer runs independently. Feature columns are prefixed with
        {featurizer_id}__ to avoid name conflicts. Single featurizer failures
        are skipped; only all failing causes overall failure.
        """
        selected = resolved_strategy.get("selected_featurizers", [])

        if not selected:
            # Use legacy single-featurizer dispatch for backward compatibility
            return self._run_legacy_single_featurizer(
                raw_df, context, resolved_strategy, input_modality
            )

        executable = get_executable_featurizers(selected, input_modality)

        if not executable:
            # Try fallback: run legacy single featurizer for the modality
            logger.warning(
                "No executable featurizers from selected=%s for modality=%s. "
                "Trying legacy dispatcher.",
                selected, input_modality,
            )
            return self._run_legacy_single_featurizer(
                raw_df, context, resolved_strategy, input_modality
            )

        all_feature_dfs = []
        all_executed = []
        all_failed_samples = []
        all_warnings = []
        all_errors = []
        feature_groups = []
        any_success = False

        for fid, instance in executable:
            try:
                result = instance.featurize(raw_df, context, resolved_strategy)
            except Exception as exc:
                logger.error("Featurizer '%s' raised exception: %s", fid, exc)
                all_executed.append({
                    "name": fid,
                    "display_name": getattr(instance, 'featurizer_name', lambda: fid)(),
                    "status": "failed",
                    "n_features_generated": 0,
                    "failed_sample_count": 0,
                    "execution_time_ms": 0,
                    "dependency_versions": {},
                })
                all_errors.append(f"Featurizer '{fid}' raised exception: {exc}")
                continue

            exec_list = result.get("executed_featurizers", [])
            if exec_list:
                all_executed.extend(exec_list)

            feat_status = result.get("status", "failed")
            feat_df = result.get("feature_dataframe")

            if feat_status in ("unavailable", "skipped"):
                all_warnings.extend(result.get("warnings", []))
                continue

            if feat_df is not None and len(feat_df.columns) > 0:
                all_feature_dfs.append(feat_df)
                if feat_status in ("success", "success_with_warning"):
                    any_success = True

                ef_for_group = exec_list[0] if exec_list else {"name": fid}
                feature_groups.append({
                    "group_name": ef_for_group.get("name", fid),
                    "display_name": ef_for_group.get("display_name", ""),
                    "n_features": len(feat_df.columns),
                    "feature_columns": list(feat_df.columns),
                    "status": feat_status,
                })

            all_failed_samples.extend(result.get("failed_samples", []))
            all_warnings.extend(result.get("warnings", []))
            all_errors.extend(result.get("errors", []))

        if not all_feature_dfs:
            return {
                "status": "failed",
                "feature_dataframe": None,
                "feature_columns": [],
                "executed_featurizers": all_executed,
                "feature_groups": feature_groups,
                "failed_samples": all_failed_samples,
                "warnings": all_warnings,
                "errors": all_errors or ["All featurizers failed."],
            }

        # Merge all feature dataframes horizontally
        import pandas as pd
        merged = pd.concat(all_feature_dfs, axis=1)
        merged = merged.loc[:, ~merged.columns.duplicated()]

        overall_status = "success" if any_success else "failed"
        if all_errors:
            overall_status = "failed"
        elif all_warnings:
            overall_status = "success_with_warning"

        return {
            "status": overall_status,
            "feature_dataframe": merged,
            "feature_columns": list(merged.columns),
            "executed_featurizers": all_executed,
            "feature_groups": feature_groups,
            "failed_samples": all_failed_samples,
            "failed_sample_count": len(all_failed_samples),
            "warnings": all_warnings,
            "errors": all_errors,
        }

    def _run_legacy_single_featurizer(self, raw_df, context, resolved_strategy, input_modality) -> dict:
        """Legacy single-featurizer dispatch. Used when no executable featurizers
        are selected or as fallback for backward compatibility."""
        feature_type = resolved_strategy.get("feature_type")

        if input_modality == InputModality.COMPOSITION or feature_type == FeatureType.COMPOSITION_DESCRIPTORS:
            featurizer = CompositionFeaturizer()
        elif input_modality == InputModality.DESCRIPTOR or feature_type == FeatureType.EXISTING_DESCRIPTORS:
            featurizer = DescriptorFeaturizer()
        elif input_modality == InputModality.STRUCTURE or feature_type == FeatureType.STRUCTURE_DESCRIPTORS:
            featurizer = StructureFeaturizer()
        else:
            return {
                "status": "failed",
                "feature_dataframe": None,
                "feature_columns": [],
                "executed_featurizers": [],
                "feature_groups": [],
                "failed_samples": [],
                "warnings": [],
                "errors": [f"Unsupported input modality: '{input_modality}'."],
            }

        result = featurizer.featurize(raw_df, context, resolved_strategy)
        result.setdefault("feature_groups", [])
        return result

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, fe: FeatureEngineering) -> FeatureEngineeringResponse:
        if fe.feature_json:
            return FeatureEngineeringResponse(**fe.feature_json)
        return FeatureEngineeringResponse(
            feature_engineering_id=fe.id or "",
            task_id=fe.task_id or "",
            interpretation_id=fe.interpretation_id,
            dataset_profile_id=fe.dataset_profile_id,
            workflow_plan_id=fe.workflow_plan_id,
            status=fe.status or FeatureEngineeringStatus.PENDING,
            input_modality=fe.input_modality,
            feature_type=fe.feature_type,
            created_at=fe.created_at,
            updated_at=fe.updated_at,
        )
