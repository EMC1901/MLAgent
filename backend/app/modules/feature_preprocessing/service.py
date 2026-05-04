import logging
import uuid
from datetime import datetime
from sqlmodel import Session

from app.modules.task_specification.repository import TaskSpecificationRepository
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.modules.feature_preprocessing.schemas import (
    FeaturePreprocessingCreateRequest,
    FeaturePreprocessingResponse,
    PreviewResponse,
)
from app.modules.feature_preprocessing.context_builder import build_preprocessing_context
from app.modules.feature_preprocessing.artifact_loader import load_raw_feature_matrix
from app.modules.feature_preprocessing.feature_filter import filter_features
from app.modules.feature_preprocessing.feature_group_validator import validate_feature_groups
from app.modules.feature_preprocessing.preprocessing_executor import execute_preprocessing
from app.modules.feature_preprocessing.preprocessing_pipeline_builder import build_pipeline
from app.modules.feature_preprocessing.artifact_manager import (
    save_model_ready_artifact,
    read_preview_from_model_ready,
)
from app.modules.feature_preprocessing.builder import build_preprocessing_object
from app.modules.feature_preprocessing.enums import FeaturePreprocessingStatus
from app.modules.feature_preprocessing.exceptions import (
    FeaturePreprocessingNotFoundException,
    FeaturePreprocessingUpstreamNotReadyException,
    FeatureArtifactLoadException,
    FeatureArtifactMissingException,
    TargetColumnMissingException,
    NoValidFeaturesException,
    ImputationFailedException,
    ScalingFailedException,
    FeatureSelectionFailedException,
    ModelReadyArtifactSaveException,
    PreprocessorArtifactSaveException,
)

logger = logging.getLogger(__name__)


class FeaturePreprocessingService:

    def __init__(self):
        self.task_repo = TaskSpecificationRepository()
        self.fmp_repo = FeaturePreprocessingRepository()

    def create_feature_preprocessing(
        self, session: Session, task_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        fmp_id = f"fmp_{uuid.uuid4().hex[:8]}"
        all_warnings = []
        all_errors = []

        # --- 1. Build upstream context ---
        try:
            context = build_preprocessing_context(session, task_id)
        except FeaturePreprocessingUpstreamNotReadyException:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                status=FeaturePreprocessingStatus.BLOCKED,
                error_message="Upstream not ready.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        fe_context = context.get("feature_engineering_context") or {}
        artifact_path = fe_context.get("artifact_path")

        # --- 2. Load raw feature matrix ---
        try:
            load_result = load_raw_feature_matrix(artifact_path)
        except (FeatureArtifactLoadException, FeatureArtifactMissingException):
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                error_message="Failed to load feature artifact.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        raw_df = load_result["dataframe"]
        candidate_features = load_result["candidate_feature_columns"]
        target_column = context.get("task_context", {}).get("target_column") or load_result["target_column"]
        n_raw_features = len(candidate_features)

        # Check target column
        if not target_column or target_column not in raw_df.columns:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                target_column=target_column,
                error_message="Target column missing.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise TargetColumnMissingException(f"Target column '{target_column}' not found in feature matrix.")

        # --- 3. Filter invalid features ---
        max_missing_ratio = request.max_missing_ratio
        filter_result = filter_features(raw_df, candidate_features, max_missing_ratio)
        retained_features = filter_result["retained_feature_columns"]

        if not retained_features:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=0,
                n_final_features=0,
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="No valid features after filtering.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise NoValidFeaturesException()

        # --- 4. Feature group validation ---
        fe_json = fe_context.get("feature_json", {})
        feature_groups = (
            fe_json.get("feature_schema", {}).get("feature_groups", [])
            or fe_json.get("feature_groups", [])
        )
        group_validation = validate_feature_groups(feature_groups, retained_features)

        # --- 5. Execute preprocessing ---
        filtered_df = filter_result["dataframe"]
        execution_result = execute_preprocessing(
            df=filtered_df,
            target_column=target_column,
            feature_columns=retained_features,
            imputation_strategy=request.imputation_strategy,
            scaling_strategy=request.scaling_strategy,
            feature_selection_strategy=request.feature_selection_strategy,
        )

        exec_errors = execution_result.get("errors", [])
        exec_warnings = execution_result.get("warnings", [])
        all_warnings.extend(exec_warnings)
        all_errors.extend(exec_errors)

        if exec_errors:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=len(execution_result.get("feature_columns", [])),
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="; ".join(exec_errors),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise ImputationFailedException("; ".join(exec_errors))

        model_ready_df = execution_result["dataframe"]
        final_features = execution_result["feature_columns"]

        if model_ready_df is None or final_features is None or len(final_features) == 0:
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=0,
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="No features after preprocessing.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise NoValidFeaturesException("No features remain after preprocessing.")

        # --- 6. Build preprocessing pipeline ---
        pipeline = build_pipeline(execution_result, final_features)

        # --- 7. Save artifacts ---
        try:
            artifact_result = save_model_ready_artifact(fmp_id, model_ready_df, pipeline)
        except (ModelReadyArtifactSaveException, PreprocessorArtifactSaveException):
            failed = FeaturePreprocessing(
                id=fmp_id,
                task_id=task_id,
                interpretation_id=context.get("interpretation_id"),
                dataset_profile_id=context.get("dataset_profile_id"),
                workflow_plan_id=context.get("workflow_plan_id"),
                feature_engineering_id=context.get("feature_engineering_id"),
                status=FeaturePreprocessingStatus.FAILED,
                n_samples=len(raw_df),
                n_raw_features=n_raw_features,
                n_valid_features=len(retained_features),
                n_final_features=len(final_features),
                n_dropped_features=len(filter_result.get("total_dropped", [])),
                target_column=target_column,
                error_message="Failed to save artifacts.",
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            self.fmp_repo.create(session, failed)
            raise

        # --- 8. Determine status ---
        if all_errors:
            status = FeaturePreprocessingStatus.FAILED
        elif all_warnings or filter_result.get("total_dropped"):
            status = FeaturePreprocessingStatus.PREPROCESSED_WITH_WARNING
        else:
            status = FeaturePreprocessingStatus.PREPROCESSED

        filter_result["n_samples"] = len(raw_df)

        # --- 9. Build Feature Preprocessing Object ---
        fmp_object = build_preprocessing_object(
            preprocessing_id=fmp_id,
            context=context,
            status=status,
            filter_result=filter_result,
            group_validation=group_validation,
            execution_result=execution_result,
            artifact_result=artifact_result,
            warnings=all_warnings,
            errors=all_errors,
        )

        # --- 10. Persist ---
        fmp_model = FeaturePreprocessing(
            id=fmp_id,
            task_id=context["task_id"],
            interpretation_id=context.get("interpretation_id"),
            dataset_profile_id=context.get("dataset_profile_id"),
            workflow_plan_id=context.get("workflow_plan_id"),
            feature_engineering_id=context.get("feature_engineering_id"),
            status=status,
            n_samples=fmp_object.validation_summary.n_samples if fmp_object.validation_summary else len(raw_df),
            n_raw_features=n_raw_features,
            n_valid_features=len(retained_features),
            n_final_features=fmp_object.validation_summary.n_features_after_preprocessing if fmp_object.validation_summary else len(final_features),
            n_dropped_features=fmp_object.validation_summary.n_dropped_features if fmp_object.validation_summary else len(filter_result.get("total_dropped", [])),
            target_column=target_column,
            model_ready_artifact_id=artifact_result.get("model_ready_artifact_id"),
            model_ready_artifact_path=artifact_result.get("model_ready_file_path"),
            preprocessor_artifact_id=artifact_result.get("preprocessor_artifact_id"),
            preprocessor_artifact_path=artifact_result.get("preprocessor_file_path"),
            is_ready_for_model_search=fmp_object.model_search_input.ready_for_model_search if fmp_object.model_search_input else False,
            preprocessing_json=fmp_object.model_dump(mode="json"),
            preview_json=artifact_result.get("preview_json"),
            error_message=None if all_errors == [] else "; ".join(all_errors),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self.fmp_repo.create(session, fmp_model)

        return fmp_object

    def get_feature_preprocessing(self, session: Session, fmp_id: str) -> FeaturePreprocessingResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )
        return self._to_response(fmp)

    def get_latest_by_task_id(self, session: Session, task_id: str) -> FeaturePreprocessingResponse:
        self._check_task_exists(session, task_id)
        fmp = self.fmp_repo.get_latest_by_task_id(session, task_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"No feature preprocessing found for task {task_id}."
            )
        return self._to_response(fmp)

    def rerun_feature_preprocessing(
        self, session: Session, task_id: str, request: FeaturePreprocessingCreateRequest,
    ) -> FeaturePreprocessingResponse:
        return self.create_feature_preprocessing(session, task_id, request)

    def get_preview(self, session: Session, fmp_id: str) -> PreviewResponse:
        fmp = self.fmp_repo.get_by_id(session, fmp_id)
        if not fmp:
            raise FeaturePreprocessingNotFoundException(
                f"Feature preprocessing with id {fmp_id} not found."
            )

        if fmp.preview_json:
            return PreviewResponse(
                columns=fmp.preview_json.get("columns", []),
                preview_rows=fmp.preview_json.get("preview_rows", 0),
                total_rows=fmp.preview_json.get("total_rows", 0),
                rows=fmp.preview_json.get("rows", []),
            )

        preview = read_preview_from_model_ready(fmp_id)
        return PreviewResponse(
            columns=preview.get("columns", []),
            preview_rows=preview.get("preview_rows", 0),
            total_rows=preview.get("total_rows", 0),
            rows=preview.get("rows", []),
        )

    def _check_task_exists(self, session: Session, task_id: str):
        task_spec = self.task_repo.get_by_id(session, task_id)
        if not task_spec:
            from app.shared.common.exceptions import NotFoundException
            raise NotFoundException(f"Task specification with id {task_id} not found.")

    def _to_response(self, fmp: FeaturePreprocessing) -> FeaturePreprocessingResponse:
        if fmp.preprocessing_json:
            return FeaturePreprocessingResponse(**fmp.preprocessing_json)
        return FeaturePreprocessingResponse(
            preprocessing_id=fmp.id or "",
            task_id=fmp.task_id or "",
            interpretation_id=fmp.interpretation_id,
            dataset_profile_id=fmp.dataset_profile_id,
            workflow_plan_id=fmp.workflow_plan_id,
            feature_engineering_id=fmp.feature_engineering_id,
            status=fmp.status or FeaturePreprocessingStatus.PENDING,
            created_at=fmp.created_at,
            updated_at=fmp.updated_at,
        )
