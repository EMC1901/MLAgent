import logging
import re
import pandas as pd
import numpy as np
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

# Built-in element property table (atomic number, atomic weight, electronegativity)
_ELEMENT_PROPERTIES = {
    "H":  (1, 1.008, 2.20),   "He": (2, 4.0026, 0.0),
    "Li": (3, 6.94, 0.98),    "Be": (4, 9.0122, 1.57),
    "B":  (5, 10.81, 2.04),   "C":  (6, 12.011, 2.55),
    "N":  (7, 14.007, 3.04),  "O":  (8, 15.999, 3.44),
    "F":  (9, 18.998, 3.98),  "Ne": (10, 20.180, 0.0),
    "Na": (11, 22.990, 0.93), "Mg": (12, 24.305, 1.31),
    "Al": (13, 26.982, 1.61), "Si": (14, 28.085, 1.90),
    "P":  (15, 30.974, 2.19), "S":  (16, 32.06, 2.58),
    "Cl": (17, 35.45, 3.16),  "Ar": (18, 39.948, 0.0),
    "K":  (19, 39.098, 0.82), "Ca": (20, 40.078, 1.00),
    "Sc": (21, 44.956, 1.36), "Ti": (22, 47.867, 1.54),
    "V":  (23, 50.942, 1.63), "Cr": (24, 51.996, 1.66),
    "Mn": (25, 54.938, 1.55), "Fe": (26, 55.845, 1.83),
    "Co": (27, 58.933, 1.88), "Ni": (28, 58.693, 1.91),
    "Cu": (29, 63.546, 1.90), "Zn": (30, 65.38, 1.65),
    "Ga": (31, 69.723, 1.81), "Ge": (32, 72.630, 2.01),
    "As": (33, 74.922, 2.18), "Se": (34, 78.971, 2.55),
    "Br": (35, 79.904, 2.96), "Kr": (36, 83.798, 3.00),
    "Rb": (37, 85.468, 0.82), "Sr": (38, 87.62, 0.95),
    "Y":  (39, 88.906, 1.22), "Zr": (40, 91.224, 1.33),
    "Nb": (41, 92.906, 1.60), "Mo": (42, 95.95, 2.16),
    "Tc": (43, 97.907, 1.90), "Ru": (44, 101.07, 2.20),
    "Rh": (45, 102.91, 2.28), "Pd": (46, 106.42, 2.20),
    "Ag": (47, 107.87, 1.93), "Cd": (48, 112.41, 1.69),
    "In": (49, 114.82, 1.78), "Sn": (50, 118.71, 1.96),
    "Sb": (51, 121.76, 2.05), "Te": (52, 127.60, 2.10),
    "I":  (53, 126.90, 2.66), "Xe": (54, 131.29, 2.60),
    "Cs": (55, 132.91, 0.79), "Ba": (56, 137.33, 0.89),
    "La": (57, 138.91, 1.10), "Ce": (58, 140.12, 1.12),
    "Pr": (59, 140.91, 1.13), "Nd": (60, 144.24, 1.14),
    "Sm": (62, 150.36, 1.17), "Eu": (63, 151.96, 1.20),
    "Gd": (64, 157.25, 1.20), "Tb": (65, 158.93, 1.10),
    "Dy": (66, 162.50, 1.22), "Ho": (67, 164.93, 1.23),
    "Er": (68, 167.26, 1.24), "Tm": (69, 168.93, 1.25),
    "Yb": (70, 173.05, 1.10), "Lu": (71, 174.97, 1.27),
    "Hf": (72, 178.49, 1.30), "Ta": (73, 180.95, 1.50),
    "W":  (74, 183.84, 2.36), "Re": (75, 186.21, 1.90),
    "Os": (76, 190.23, 2.20), "Ir": (77, 192.22, 2.20),
    "Pt": (78, 195.08, 2.28), "Au": (79, 196.97, 2.54),
    "Hg": (80, 200.59, 2.00), "Tl": (81, 204.38, 1.62),
    "Pb": (82, 207.2, 2.33),  "Bi": (83, 208.98, 2.02),
    "Po": (84, 208.98, 2.00), "At": (85, 209.99, 2.20),
    "Rn": (86, 222.02, 2.20), "Fr": (87, 223.02, 0.70),
    "Ra": (88, 226.03, 0.90), "Ac": (89, 227.03, 1.10),
    "Th": (90, 232.04, 1.30), "Pa": (91, 231.04, 1.50),
    "U":  (92, 238.03, 1.38),
}

_TRANSITION_METALS = {
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd",
    "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
}
_METALS = _TRANSITION_METALS | {
    "Li", "Be", "Na", "Mg", "Al", "K", "Ca", "Rb", "Sr", "Cs",
    "Ba", "Fr", "Ra", "Ga", "In", "Sn", "Tl", "Pb", "Bi",
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu", "Ac", "Th", "Pa", "U",
}

_ELEMENT_PATTERN = re.compile(r"([A-Z][a-z]?)(\d*\.?\d*)")


def _parse_composition(formula: str):
    """Parse a chemical formula string into a dict of {element: amount}."""
    if not isinstance(formula, str) or not formula.strip():
        return {}
    elements = {}
    for match in _ELEMENT_PATTERN.findall(formula):
        elem, amt = match
        elements[elem] = elements.get(elem, 0.0) + (float(amt) if amt else 1.0)
    return elements


def _compute_descriptors(elements: dict) -> dict:
    """Compute lightweight composition descriptors from an element dict."""
    if not elements:
        return {
            "n_elements": 0, "n_total_atoms": 0,
            "mean_atomic_number": np.nan, "max_atomic_number": np.nan,
            "min_atomic_number": np.nan, "mean_atomic_weight": np.nan,
            "max_atomic_weight": np.nan, "min_atomic_weight": np.nan,
            "mean_electronegativity": np.nan, "max_electronegativity": np.nan,
            "min_electronegativity": np.nan, "stoichiometric_entropy": np.nan,
            "max_element_fraction": np.nan, "min_element_fraction": np.nan,
            "has_metal": False, "has_transition_metal": False,
        }

    total = sum(elements.values())
    fractions = {e: a / total for e, a in elements.items()}

    atomic_numbers = []
    atomic_weights = []
    electronegativities = []
    has_metal = False
    has_transition = False

    for elem, frac in fractions.items():
        props = _ELEMENT_PROPERTIES.get(elem)
        if props is None:
            continue
        z, w, en = props
        atomic_numbers.append(z)
        atomic_weights.append(w)
        if en > 0:
            electronegativities.append(en)
        if elem in _METALS:
            has_metal = True
        if elem in _TRANSITION_METALS:
            has_transition = True

    frac_values = list(fractions.values())
    max_frac = max(frac_values)
    min_frac = min(frac_values)

    # Stoichiometric entropy: -sum(p_i * log(p_i))
    entropy = -sum(f * np.log(f) for f in frac_values if f > 0)

    return {
        "n_elements": len(elements),
        "n_total_atoms": total,
        "mean_atomic_number": float(np.mean(atomic_numbers)) if atomic_numbers else np.nan,
        "max_atomic_number": int(max(atomic_numbers)) if atomic_numbers else np.nan,
        "min_atomic_number": int(min(atomic_numbers)) if atomic_numbers else np.nan,
        "mean_atomic_weight": float(np.mean(atomic_weights)) if atomic_weights else np.nan,
        "max_atomic_weight": float(max(atomic_weights)) if atomic_weights else np.nan,
        "min_atomic_weight": float(min(atomic_weights)) if atomic_weights else np.nan,
        "mean_electronegativity": float(np.mean(electronegativities)) if electronegativities else np.nan,
        "max_electronegativity": float(max(electronegativities)) if electronegativities else np.nan,
        "min_electronegativity": float(min(electronegativities)) if electronegativities else np.nan,
        "stoichiometric_entropy": float(entropy),
        "max_element_fraction": float(max_frac),
        "min_element_fraction": float(min_frac),
        "has_metal": has_metal,
        "has_transition_metal": has_transition,
    }


class CompositionFeaturizer(BaseFeaturizer):

    def featurizer_name(self) -> str:
        return "basic_composition"

    def featurize(self, raw_dataframe, context, resolved_strategy) -> dict:
        data_context = context.get("data_context") or {}
        input_columns = data_context.get("input_columns", [])
        if not input_columns:
            return {
                "status": "failed",
                "feature_dataframe": None,
                "feature_columns": [],
                "executed_featurizers": [],
                "failed_samples": [],
                "warnings": [],
                "errors": ["No input columns found for composition featurization."],
            }

        composition_col = input_columns[0]
        if composition_col not in raw_dataframe.columns:
            return {
                "status": "failed",
                "feature_dataframe": None,
                "feature_columns": [],
                "executed_featurizers": [],
                "failed_samples": [],
                "warnings": [],
                "errors": [f"Composition column '{composition_col}' not found in data."],
            }

        formulas = raw_dataframe[composition_col].astype(str)
        features_list = []
        failed_indices = []
        failed_count = 0

        for idx, formula in formulas.items():
            elements = _parse_composition(formula)
            if not elements:
                failed_indices.append(str(idx))
                failed_count += 1
                features_list.append({
                    "n_elements": 0, "n_total_atoms": 0,
                    "mean_atomic_number": np.nan, "max_atomic_number": np.nan,
                    "min_atomic_number": np.nan, "mean_atomic_weight": np.nan,
                    "max_atomic_weight": np.nan, "min_atomic_weight": np.nan,
                    "mean_electronegativity": np.nan, "max_electronegativity": np.nan,
                    "min_electronegativity": np.nan, "stoichiometric_entropy": np.nan,
                    "max_element_fraction": np.nan, "min_element_fraction": np.nan,
                    "has_metal": False, "has_transition_metal": False,
                })
            else:
                features_list.append(_compute_descriptors(elements))

        feature_df = pd.DataFrame(features_list, index=raw_dataframe.index)

        feature_columns = list(feature_df.columns)
        warnings = []

        if failed_count > 0:
            ratio = failed_count / len(raw_dataframe)
            if ratio > 0.2:
                return {
                    "status": "failed",
                    "feature_dataframe": feature_df,
                    "feature_columns": feature_columns,
                    "executed_featurizers": [
                        {"name": self.featurizer_name(), "status": "failed",
                         "n_features_generated": len(feature_columns),
                         "failed_sample_count": failed_count}
                    ],
                    "failed_samples": failed_indices,
                    "warnings": [],
                    "errors": [f"Failed sample ratio {ratio:.2%} exceeds threshold 20%."],
                }
            warnings.append(f"{failed_count} samples failed composition parsing.")

        executed = [{
            "name": self.featurizer_name(),
            "status": "success" if failed_count == 0 else "success_with_failures",
            "n_features_generated": len(feature_columns),
            "failed_sample_count": failed_count,
        }]

        return {
            "status": "success",
            "feature_dataframe": feature_df,
            "feature_columns": feature_columns,
            "executed_featurizers": executed,
            "failed_samples": failed_indices,
            "warnings": warnings,
            "errors": [],
        }
