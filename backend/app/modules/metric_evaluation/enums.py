class MetricEvaluationStatus:
    EVALUATING = "evaluating"
    EVALUATED = "evaluated"
    EVALUATED_WITH_WARNING = "evaluated_with_warning"
    PARTIALLY_EVALUATED = "partially_evaluated"
    FAILED = "failed"


class TrialEvaluationStatus:
    EVALUATED = "evaluated"
    FAILED = "failed"
    SKIPPED = "skipped"


class MetricDirection:
    MINIMIZE = "minimize"
    MAXIMIZE = "maximize"


class TaskType:
    REGRESSION = "regression"
    CLASSIFICATION = "classification"
