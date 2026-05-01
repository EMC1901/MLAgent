import logging
from datetime import datetime
from sqlmodel import Session

from app.modules.dataset_profile.model import DatasetProfile
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.dataset_profile.schemas import (
    DatasetProfileCreateRequest,
    DatasetProfileResponse,
    DatasetPreviewResponse,
    DatasetSource,
    DatasetSchema,
    ModalityCheck,
    TargetProfile,
    DataQuality,
    ProfilingSummary,
    WorkflowPlanningInput,
    MissingValues,
    Duplicates,
    InvalidRows,
    ClassDistribution,
)
from app.modules.dataset_profile.context_builder import build_dataset_loading_context
from app.modules.dataset_profile.source_resolver import resolve_source
from app.modules.dataset_profile.loaders import MatbenchLoader, FileLoader
from app.modules.dataset_profile.checkers import (
    check_schema,
    check_modality,
    check_quality,
    check_target,
)
from app.modules.dataset_profile.builder import build_dataset_profile
from app.modules.dataset_profile.exceptions import (
    DatasetProfileNotFoundException,
    DatasetSourceUnresolvedException,
    DatasetSourceUnsupportedException,
    DatasetLoadException,
)

logger = logging.getLogger(__name__)


class DatasetProfileService:

    def __init__(self):
        self.repository = DatasetProfileRepository()
        self._loaders = {
            "matbench": MatbenchLoader(),
            "file": FileLoader(),
        }

    def create_profile(
        self,
        session: Session,
        task_id: str,
        request: DatasetProfileCreateRequest,
    ) -> DatasetProfileResponse:
        context = build_dataset_loading_context(session, task_id)
        dataset_intent = context["dataset_context"]["dataset_intent"]

        source = resolve_source(
            dataset_intent=dataset_intent,
            dataset_description=context["task_context"].get("dataset_description"),
            uploaded_file_id=request.uploaded_file_id,
            uploaded_file_path=request.uploaded_file_path,
        )

        if source["source_type"] == "unknown":
            raise DatasetSourceUnresolvedException(
                "Unable to determine dataset source. "
                "Specify dataset_reference or upload a file."
            )

        if not source["is_supported"]:
            raise DatasetSourceUnsupportedException(
                f"Source type '{source['source_type']}' is not supported in MVP."
            )

        loader_name = source.get("loader_name", "")
        loader = self._loaders.get(loader_name)
        if loader is None:
            raise DatasetSourceUnsupportedException(
                f"No loader available for loader '{loader_name}'."
            )

        df, loading_result = loader.load(context, source)

        if df is None:
            failed_profile = self._save_failed(
                session, context, source, loading_result,
            )
            return self._to_response(failed_profile)

        schema_result = check_schema(
            df,
            expected_input_columns=context["dataset_context"]["expected_input_columns"],
            expected_target_column=context["expected_target_column"],
        )

        modality_result = check_modality(
            df,
            expected_input_modality=context["expected_input_modality"],
            input_columns=context["dataset_context"]["expected_input_columns"],
        )

        quality_result = check_quality(
            df,
            input_columns=context["dataset_context"]["expected_input_columns"],
            target_column=context["expected_target_column"],
        )

        target_result = check_target(
            df,
            target_column=context["expected_target_column"],
            task_type=context["expected_task_type"] or "regression",
        )

        profile_dict = build_dataset_profile(
            context=context,
            loading_result=loading_result,
            df=df,
            schema_result=schema_result,
            modality_result=modality_result,
            quality_result=quality_result,
            target_result=target_result,
            source_resolution=source,
            max_preview_rows=request.max_preview_rows,
        )

        profile_model = self._dict_to_model(profile_dict, loading_result, source)
        created = self.repository.create(session, profile_model)
        return self._to_response(created)

    def get_profile(self, session: Session, profile_id: str) -> DatasetProfileResponse:
        profile = self.repository.get_by_id(session, profile_id)
        if not profile:
            raise DatasetProfileNotFoundException(
                f"Dataset profile with id {profile_id} not found."
            )
        return self._to_response(profile)

    def get_latest_by_task_id(
        self, session: Session, task_id: str
    ) -> DatasetProfileResponse:
        profile = self.repository.get_latest_by_task_id(session, task_id)
        if not profile:
            raise DatasetProfileNotFoundException(
                f"No dataset profile found for task {task_id}."
            )
        return self._to_response(profile)

    def rerun_profile(
        self,
        session: Session,
        task_id: str,
        request: DatasetProfileCreateRequest,
    ) -> DatasetProfileResponse:
        return self.create_profile(session, task_id, request)

    def get_preview(
        self, session: Session, profile_id: str
    ) -> DatasetPreviewResponse:
        profile = self.repository.get_by_id(session, profile_id)
        if not profile:
            raise DatasetProfileNotFoundException(
                f"Dataset profile with id {profile_id} not found."
            )

        preview_json = profile.preview_json or {}
        return DatasetPreviewResponse(
            dataset_profile_id=profile.id,
            columns=preview_json.get("columns", []),
            rows=preview_json.get("rows", []),
            total_rows=preview_json.get("total_rows", 0),
            preview_rows=preview_json.get("preview_rows", 0),
        )

    def _save_failed(
        self,
        session: Session,
        context: dict,
        source: dict,
        loading_result: dict,
    ) -> DatasetProfile:
        profile_json = {
            "dataset_profile_id": f"profile_{__import__('uuid').uuid4().hex[:8]}",
            "task_id": context["task_id"],
            "interpretation_id": context["interpretation_id"],
            "status": "failed",
            "dataset_source": {
                "source_type": source.get("source_type"),
                "dataset_reference": source.get("dataset_reference"),
                "loader": source.get("loader_name"),
            },
            "profiling_summary": {
                "is_loadable": False,
                "is_usable_for_ml": False,
            },
            "load_messages": loading_result.get("load_messages", []),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }
        model = DatasetProfile(
            id=profile_json["dataset_profile_id"],
            task_id=context["task_id"],
            interpretation_id=context["interpretation_id"],
            status="failed",
            source_type=source.get("source_type"),
            dataset_reference=source.get("dataset_reference"),
            loader_name=source.get("loader_name"),
            profile_json=profile_json,
            error_message="; ".join(loading_result.get("load_messages", [])),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        return self.repository.create(session, model)

    def _dict_to_model(
        self,
        profile_dict: dict,
        loading_result: dict,
        source: dict,
    ) -> DatasetProfile:
        schema = profile_dict.get("dataset_schema", {})
        summary = profile_dict.get("profiling_summary", {})
        preview = profile_dict.get("preview", {})

        return DatasetProfile(
            id=profile_dict["dataset_profile_id"],
            task_id=profile_dict["task_id"],
            interpretation_id=profile_dict["interpretation_id"],
            status=profile_dict["status"],
            source_type=source.get("source_type"),
            dataset_reference=source.get("dataset_reference"),
            loader_name=source.get("loader_name"),
            n_samples=schema.get("n_samples"),
            n_columns=schema.get("n_columns"),
            input_modality=profile_dict.get("modality_check", {}).get("detected_input_modality"),
            target_column=schema.get("target_column"),
            quality_level=summary.get("quality_level"),
            is_usable_for_ml=summary.get("is_usable_for_ml"),
            profile_json=profile_dict,
            preview_json=preview,
            created_at=datetime.fromisoformat(profile_dict["created_at"]),
            updated_at=datetime.fromisoformat(profile_dict["updated_at"]),
        )

    def _to_response(self, model: DatasetProfile) -> DatasetProfileResponse:
        pj = model.profile_json or {}

        ds_raw = pj.get("dataset_source") or {}
        dataset_source = DatasetSource(
            source_type=ds_raw.get("source_type", model.source_type or "unknown"),
            dataset_reference=ds_raw.get("dataset_reference", model.dataset_reference),
            loader=ds_raw.get("loader", model.loader_name),
            loaded_from=ds_raw.get("loaded_from"),
            file_name=ds_raw.get("file_name"),
        )

        schema_raw = pj.get("dataset_schema") or {}
        dataset_schema = DatasetSchema(
            n_samples=schema_raw.get("n_samples", model.n_samples or 0),
            n_columns=schema_raw.get("n_columns", model.n_columns or 0),
            columns=schema_raw.get("columns", []),
            input_columns=schema_raw.get("input_columns", []),
            target_column=schema_raw.get("target_column", model.target_column),
        )

        mc_raw = pj.get("modality_check") or {}
        modality_check = ModalityCheck(
            expected_input_modality=mc_raw.get("expected_input_modality"),
            detected_input_modality=mc_raw.get("detected_input_modality"),
            is_consistent=mc_raw.get("is_consistent", True),
            messages=mc_raw.get("messages", []),
        )

        tp_raw = pj.get("target_profile") or {}
        class_dist = None
        if tp_raw.get("class_distribution"):
            class_dist = [
                ClassDistribution(label=d["label"], count=d["count"], ratio=d["ratio"])
                for d in tp_raw["class_distribution"]
            ]
        target_profile = TargetProfile(
            target_column=tp_raw.get("target_column"),
            task_type=tp_raw.get("task_type"),
            dtype=tp_raw.get("dtype"),
            missing_count=tp_raw.get("missing_count", 0),
            missing_ratio=tp_raw.get("missing_ratio", 0.0),
            min=tp_raw.get("min"),
            max=tp_raw.get("max"),
            mean=tp_raw.get("mean"),
            median=tp_raw.get("median"),
            std=tp_raw.get("std"),
            skewness=tp_raw.get("skewness"),
            outlier_count=tp_raw.get("outlier_count", 0),
            class_count=tp_raw.get("class_count"),
            class_distribution=class_dist,
            majority_class_ratio=tp_raw.get("majority_class_ratio"),
            minority_class_count=tp_raw.get("minority_class_count"),
            is_imbalanced=tp_raw.get("is_imbalanced"),
        )

        dq_raw = pj.get("data_quality") or {}
        mv_raw = dq_raw.get("missing_values") or {}
        dup_raw = dq_raw.get("duplicates") or {}
        inv_raw = dq_raw.get("invalid_rows") or {}
        data_quality = DataQuality(
            missing_values=MissingValues(
                total_missing=mv_raw.get("total_missing", 0),
                columns_with_missing=mv_raw.get("columns_with_missing", []),
            ),
            duplicates=Duplicates(
                duplicate_rows=dup_raw.get("duplicate_rows", 0),
                duplicate_input_samples=dup_raw.get("duplicate_input_samples", 0),
            ),
            invalid_rows=InvalidRows(
                count=inv_raw.get("count", 0),
                examples=inv_raw.get("examples", []),
            ),
            warnings=dq_raw.get("warnings", []),
            errors=dq_raw.get("errors", []),
        )

        ps_raw = pj.get("profiling_summary") or {}
        profiling_summary = ProfilingSummary(
            is_loadable=ps_raw.get("is_loadable", False),
            is_usable_for_ml=ps_raw.get("is_usable_for_ml", False),
            sample_size_level=ps_raw.get("sample_size_level", "very_small"),
            quality_level=ps_raw.get("quality_level", "unusable"),
            main_issues=ps_raw.get("main_issues", []),
            recommended_next_step=ps_raw.get("recommended_next_step"),
        )

        wf_raw = pj.get("workflow_planning_input") or {}
        workflow_planning_input = WorkflowPlanningInput(
            input_modality=wf_raw.get("input_modality"),
            task_type=wf_raw.get("task_type"),
            target_column=wf_raw.get("target_column"),
            input_columns=wf_raw.get("input_columns", []),
            n_samples=wf_raw.get("n_samples", 0),
            n_columns=wf_raw.get("n_columns", 0),
            n_features_raw=wf_raw.get("n_features_raw", 0),
            sample_size_level=wf_raw.get("sample_size_level", "very_small"),
            has_missing_values=wf_raw.get("has_missing_values", False),
            has_duplicates=wf_raw.get("has_duplicates", False),
            requires_cleaning=wf_raw.get("requires_cleaning", False),
            requires_target_transformation_check=wf_raw.get("requires_target_transformation_check", False),
            target_distribution=wf_raw.get("target_distribution"),
            quality_level=wf_raw.get("quality_level", "unusable"),
            is_usable_for_ml=wf_raw.get("is_usable_for_ml", False),
        )

        return DatasetProfileResponse(
            dataset_profile_id=model.id,
            task_id=model.task_id,
            interpretation_id=model.interpretation_id,
            status=model.status,
            dataset_source=dataset_source,
            dataset_schema=dataset_schema,
            modality_check=modality_check,
            target_profile=target_profile,
            data_quality=data_quality,
            profiling_summary=profiling_summary,
            workflow_planning_input=workflow_planning_input,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
