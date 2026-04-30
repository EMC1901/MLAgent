from enum import Enum


class TaskStatus(str, Enum):
    draft = "draft"
    received = "received"
    valid = "valid"
    incomplete = "incomplete"
    invalid = "invalid"
    valid_with_warning = "valid_with_warning"


class TaskType(str, Enum):
    regression = "regression"
    classification = "classification"
    ranking = "ranking"


class InputType(str, Enum):
    composition = "composition"
    structure = "structure"
    descriptor_table = "descriptor_table"
    text_features = "text_features"


class EvaluationMetric(str, Enum):
    MAE = "MAE"
    RMSE = "RMSE"
    R2 = "R2"
    Accuracy = "Accuracy"
    F1 = "F1"
    ROC_AUC = "ROC-AUC"
    Spearman = "Spearman"
    NDCG = "NDCG"
    Top_k_recall = "Top-k recall"


class UserPriority(str, Enum):
    accuracy = "accuracy"
    interpretability = "interpretability"
    speed = "speed"
    robustness = "robustness"
