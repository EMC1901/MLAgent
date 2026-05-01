from enum import Enum


class InterpretationStatus(str, Enum):
    pending = "pending"
    interpreting = "interpreting"
    interpreted = "interpreted"
    interpreted_with_warning = "interpreted_with_warning"
    failed = "failed"
    blocked = "blocked"


class TargetCategory(str, Enum):
    electronic_property = "electronic_property"
    mechanical_property = "mechanical_property"
    thermal_property = "thermal_property"
    optical_property = "optical_property"
    magnetic_property = "magnetic_property"
    structural_property = "structural_property"
    chemical_property = "chemical_property"
    other = "other"


class ModelingGoal(str, Enum):
    property_prediction = "property_prediction"
    material_screening = "material_screening"
    classification = "classification"
    ranking = "ranking"
    interpretability_analysis = "interpretability_analysis"
    benchmark_comparison = "benchmark_comparison"


class InputModality(str, Enum):
    composition = "composition"
    structure = "structure"
    descriptor = "descriptor"
    text = "text"
    mixed = "mixed"
