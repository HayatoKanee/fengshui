"""
Harmony Relationships Domain Constants - DERIVED from Enums.

String-based lookups for presentation layer and external libraries.
Single source of truth is in `bazi.domain.models.stems_branches`.
"""
from typing import Dict, FrozenSet, Tuple

from ..models.stems_branches import (
    HeavenlyStem,
    EarthlyBranch,
    RELATIONS,
)


# =============================================================================
# DERIVED STRING LOOKUPS - Generated from Enums
# =============================================================================

def _derive_liu_he() -> FrozenSet[Tuple[str, str]]:
    """Derive string-based LIU_HE from Enum-based RELATIONS.LIU_HE."""
    result = set()
    for b1, b2 in RELATIONS.LIU_HE:
        result.add((b1.chinese, b2.chinese))
        result.add((b2.chinese, b1.chinese))  # Both directions
    return frozenset(result)


def _derive_wu_he() -> FrozenSet[Tuple[str, str]]:
    """Derive string-based WU_HE from Enum-based RELATIONS.WU_HE."""
    result = set()
    for s1, s2 in RELATIONS.WU_HE:
        result.add((s1.chinese, s2.chinese))
        result.add((s2.chinese, s1.chinese))  # Both directions
    return frozenset(result)


def _derive_hidden_gan_ratios() -> Dict[str, Dict[str, float]]:
    """Derive string-based hidden stems from EarthlyBranch.hidden_stems."""
    result = {}
    for branch in EarthlyBranch:
        result[branch.chinese] = {
            stem.chinese: ratio
            for stem, ratio in branch.hidden_stems.items()
        }
    return result


# 六合 - Six Harmonies (Branch combinations) - DERIVED
LIU_HE: FrozenSet[Tuple[str, str]] = _derive_liu_he()

# 五合 - Five Harmonies (Stem combinations) - DERIVED
WU_HE: FrozenSet[Tuple[str, str]] = _derive_wu_he()

# 地支藏干比例 - Hidden Stems in Branches - DERIVED
HIDDEN_GAN_RATIOS: Dict[str, Dict[str, float]] = _derive_hidden_gan_ratios()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_harmony(char1: str, char2: str) -> bool:
    """
    Check if two characters form a harmony (合) relationship.

    Checks both Liu He (六合, branch harmonies) and
    Wu He (五合, stem harmonies).

    Args:
        char1: First Chinese character (stem or branch)
        char2: Second Chinese character (stem or branch)

    Returns:
        True if the pair forms a harmony relationship
    """
    pair = (char1, char2)
    return pair in LIU_HE or pair in WU_HE
