"""
Featurizer Router — maps Registry featurizer IDs to Featurizer class instances.

This is the bridge between the Registry (static specs) and the executable
featurizer classes. When a new featurizer is added:
  1. Register it in the Registry (featurizer_registry.py)
  2. Implement the class (featurizers/*.py)
  3. Map it here in _ROUTER

Both Workflow Planning and Feature Engineering consume this indirectly via the Registry.
"""
import logging
from typing import Optional, List, Tuple
from app.modules.feature_engineering.featurizers.base_featurizer import BaseFeaturizer

logger = logging.getLogger(__name__)

_ROUTER: dict = {}
_INSTANCES: dict = {}


def _init_router():
    """Lazy-initialize the router to avoid circular imports."""
    if _ROUTER:
        return

    from app.modules.feature_engineering.featurizers.composition_featurizer import CompositionFeaturizer
    from app.modules.feature_engineering.featurizers.descriptor_featurizer import DescriptorFeaturizer
    from app.modules.feature_engineering.featurizers.structure_featurizer import StructureFeaturizer
    from app.modules.feature_engineering.featurizers.pymatgen_composition_parser import PymatgenCompositionParserFeaturizer
    from app.modules.feature_engineering.featurizers.matminer_featurizers import (
        MatminerStoichiometryFeaturizer,
        MatminerElementPropertyFeaturizer,
        MatminerMagpieFeaturizer,
        MatminerValenceOrbitalFeaturizer,
        MatminerOxidationStatesFeaturizer,
        MatminerIonicCompoundFeaturizer,
        MatminerBandCenterFeaturizer,
    )
    from app.modules.feature_engineering.featurizers.descriptor_cleaner import DescriptorCleanerFeaturizer
    from app.modules.feature_engineering.featurizers.matminer_structure_basic import MatminerStructureBasicFeaturizer
    from app.modules.feature_engineering.featurizers.pymatgen_structure_parser import PymatgenStructureParserFeaturizer
    from app.modules.feature_engineering.featurizers.matminer_structure_featurizers import MatminerSiteStatsFeaturizer
    from app.modules.feature_engineering.featurizers.descriptor_statistical_featurizer import DescriptorStatisticalFeaturizer
    from app.modules.feature_engineering.featurizers.metadata_featurizer import MetadataFeaturizer

    _ROUTER.update({
        "basic_composition": CompositionFeaturizer,
        "descriptor_passthrough": DescriptorFeaturizer,
        "structure_placeholder": StructureFeaturizer,
        "pymatgen_composition_parser": PymatgenCompositionParserFeaturizer,
        "matminer_stoichiometry": MatminerStoichiometryFeaturizer,
        "matminer_element_property": MatminerElementPropertyFeaturizer,
        "matminer_magpie": MatminerMagpieFeaturizer,
        "matminer_valence_orbital": MatminerValenceOrbitalFeaturizer,
        "descriptor_cleaner": DescriptorCleanerFeaturizer,
        "pymatgen_structure_parser": PymatgenStructureParserFeaturizer,
        "matminer_structure_basic": MatminerStructureBasicFeaturizer,
        "matminer_oxidation_states": MatminerOxidationStatesFeaturizer,
        "matminer_ion_property": MatminerIonicCompoundFeaturizer,
        "matminer_band_center": MatminerBandCenterFeaturizer,
        "matminer_site_stats": MatminerSiteStatsFeaturizer,
        "descriptor_statistical": DescriptorStatisticalFeaturizer,
        "metadata_feature_extractor": MetadataFeaturizer,
    })


def get_featurizer_instance(featurizer_id: str) -> Optional[BaseFeaturizer]:
    """Return a singleton instance for the given featurizer ID, or None if not found."""
    _init_router()

    if featurizer_id in _INSTANCES:
        return _INSTANCES[featurizer_id]

    cls = _ROUTER.get(featurizer_id)
    if cls is None:
        logger.warning("No featurizer class mapped for id '%s'", featurizer_id)
        return None

    instance = cls()
    _INSTANCES[featurizer_id] = instance
    return instance


def get_executable_featurizers(
    selected_ids: List[str],
    input_modality: str,
) -> List[Tuple[str, BaseFeaturizer]]:
    """Return (featurizer_id, instance) tuples for each selected featurizer
    that has an executable implementation. Logs warnings for missing ones."""
    from app.shared.registry.featurizer_registry import (
        get_featurizer_by_id,
        get_featurizer_effective_status,
    )

    results = []
    for fid in selected_ids:
        spec = get_featurizer_by_id(fid)
        if spec is None:
            logger.warning("Featurizer '%s' not found in Registry.", fid)
            continue

        eff = get_featurizer_effective_status(spec)
        if eff != "available":
            logger.info("Featurizer '%s' effective status='%s', skipping.", fid, eff)
            continue

        if input_modality not in spec.input_modalities:
            logger.info("Featurizer '%s' does not support modality '%s', skipping.", fid, input_modality)
            continue

        instance = get_featurizer_instance(fid)
        if instance is None:
            logger.warning("Featurizer '%s' has no executable class, skipping.", fid)
            continue

        results.append((fid, instance))

    return results
