import logging
from typing import Optional
from sqlmodel import Session

from app.modules.interpretability_analysis.repository import InterpretabilityAnalysisRepository
from app.modules.metric_evaluation.repository import MetricEvaluationRepository
from app.modules.dataset_profile.repository import DatasetProfileRepository
from app.modules.pipeline_execution.repository import PipelineExecutionRepository
from app.modules.feature_preprocessing.repository import FeaturePreprocessingRepository
from app.modules.interpretability_analysis.model import InterpretabilityAnalysis
from app.modules.metric_evaluation.model import MetricEvaluation
from app.modules.dataset_profile.model import DatasetProfile
from app.modules.pipeline_execution.model import PipelineExecution
from app.modules.feature_preprocessing.model import FeaturePreprocessing
from app.modules.visualization.visualization_data_builder import build_visualization_data
from app.modules.visualization.schemas import VisualizationDataResponse
from app.shared.common.exceptions import BusinessException

logger = logging.getLogger(__name__)


class VisualizationService:

    def __init__(self):
        self.ia_repo = InterpretabilityAnalysisRepository()
        self.me_repo = MetricEvaluationRepository()
        self.dp_repo = DatasetProfileRepository()
        self.pe_repo = PipelineExecutionRepository()
        self.fp_repo = FeaturePreprocessingRepository()

    def get_visualization_data(self, session: Session, task_id: str) -> VisualizationDataResponse:
        ia = self._get_latest(session, task_id, self.ia_repo, "interpretability analysis", required=False)
        me = self._get_latest(session, task_id, self.me_repo, "metric evaluation", required=False)
        dp = self._get_latest(session, task_id, self.dp_repo, "dataset profile", required=False)
        pe = self._get_latest(session, task_id, self.pe_repo, "pipeline execution", required=False)
        fp = self._get_latest(session, task_id, self.fp_repo, "feature preprocessing", required=False)

        if ia is None and me is None:
            raise BusinessException(
                "VISUALIZATION_PREREQUISITES_MISSING",
                "Run interpretability analysis or metric evaluation first to generate visualization data.",
            )

        return build_visualization_data(
            task_id=task_id,
            ia=ia,
            me=me,
            dp=dp,
            pe=pe,
            fp=fp,
        )

    def _get_latest(self, session, task_id, repo, label, required=True):
        try:
            records = repo.list_by_task_id(session, task_id)
            record = next((r for r in records if self._is_completed(r)), None)
        except Exception as e:
            logger.warning("Failed to query %s: %s", label, str(e))
            record = None
        if record is None and required:
            raise BusinessException(
                "VISUALIZATION_DATA_MISSING",
                f"No completed {label} record found for task {task_id}. Run the pipeline first.",
            )
        return record

    @staticmethod
    def _is_completed(record) -> bool:
        status = (getattr(record, "status", None) or "").strip().lower()
        if not status:
            return True
        return status in {
            "completed", "completed_with_warning", "success", "success_with_warning",
            "succeeded", "evaluated", "evaluated_with_warning", "partially_evaluated",
            "analyzed", "analyzed_with_warning", "profiled", "profiled_with_warning",
            "preprocessed", "preprocessed_with_warning", "ready",
        }
