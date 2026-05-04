import logging
from app.modules.model_search.schemas import ValidationPlan

logger = logging.getLogger(__name__)


def build_validation_plan(updated_validation_strategy: dict) -> ValidationPlan:
    """Build validation plan from updated strategy."""
    return ValidationPlan(
        split_strategy=updated_validation_strategy.get(
            "split_strategy", "k_fold_cross_validation"
        ),
        n_splits=int(updated_validation_strategy.get("n_splits", 5)),
        random_state=int(updated_validation_strategy.get("random_state", 42)),
        shuffle=bool(updated_validation_strategy.get("shuffle", True)),
        stratification_required=bool(
            updated_validation_strategy.get("stratification_required", False)
        ),
        benchmark_split=bool(
            updated_validation_strategy.get("benchmark_split", False)
        ),
    )
