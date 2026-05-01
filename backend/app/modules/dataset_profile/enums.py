from enum import Enum


class ProfileStatus(str, Enum):
    pending = "pending"
    loading = "loading"
    loaded = "loaded"
    checking = "checking"
    profiled = "profiled"
    profiled_with_warning = "profiled_with_warning"
    failed = "failed"
    blocked = "blocked"


class SourceType(str, Enum):
    public_benchmark = "public_benchmark"
    uploaded_file = "uploaded_file"
    database_table = "database_table"
    external_url = "external_url"
    unknown = "unknown"


class QualityLevel(str, Enum):
    good = "good"
    fair = "fair"
    poor = "poor"
    unusable = "unusable"


class SampleSizeLevel(str, Enum):
    very_small = "very_small"
    small = "small"
    medium = "medium"
    large = "large"


class InputModality(str, Enum):
    composition = "composition"
    structure = "structure"
    descriptor = "descriptor"
    text = "text"
    mixed = "mixed"
