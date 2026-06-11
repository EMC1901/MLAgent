"""Shared structure parsing utilities for structure featurizers.

Parses pymatgen Structure objects, Monty-serialized dicts (both native and
string-represented), CIF strings, and POSCAR strings into Structure objects.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from pymatgen.core import Structure
    _PYMATGEN_AVAILABLE = True
except ImportError:
    _PYMATGEN_AVAILABLE = False
    Structure = None


def parse_structure_string(val: str):
    """Parse a string into a pymatgen Structure.

    Tries (in order):
      1. JSON/dict-literal string (Monty format) -> Structure.from_dict()
      2. CIF format -> Structure.from_str(fmt="cif")
      3. POSCAR format -> Structure.from_str(fmt="poscar")
    """
    val_stripped = val.strip()
    if not val_stripped:
        raise ValueError("Empty structure string")

    if val_stripped.startswith("{"):
        try:
            import json
            d = json.loads(val_stripped)
            if isinstance(d, dict):
                return Structure.from_dict(d)
        except Exception:
            pass
        try:
            import ast
            d = ast.literal_eval(val_stripped)
            if isinstance(d, dict):
                return Structure.from_dict(d)
        except Exception:
            pass

    try:
        return Structure.from_str(val_stripped, fmt="cif")
    except Exception:
        return Structure.from_str(val_stripped, fmt="poscar")


def parse_structure_value(val):
    """Parse a value of any supported type into a pymatgen Structure.

    Supported types:
      - pymatgen Structure (passthrough)
      - dict (Monty-serialized) -> Structure.from_dict()
      - str -> parse_structure_string()
    """
    if isinstance(val, Structure):
        return val
    elif isinstance(val, dict):
        return Structure.from_dict(val)
    elif isinstance(val, str):
        return parse_structure_string(val)
    else:
        raise ValueError(f"Unsupported structure value type: {type(val)}")
