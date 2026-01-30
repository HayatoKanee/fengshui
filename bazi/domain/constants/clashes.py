"""
Clash Relationships Domain Constants - DERIVED from Enums.

String-based lookups for presentation layer and external libraries.
Single source of truth is in `bazi.domain.models.stems_branches`.
"""
from typing import FrozenSet, Tuple

from ..models.stems_branches import RELATIONS


# =============================================================================
# DERIVED STRING LOOKUPS - Generated from Enums
# =============================================================================

def _derive_gan_chong() -> FrozenSet[Tuple[str, str]]:
    """Derive string-based stem clashes from Enum-based RELATIONS.GAN_CHONG."""
    result = set()
    for s1, s2 in RELATIONS.GAN_CHONG:
        result.add((s1.chinese, s2.chinese))
        result.add((s2.chinese, s1.chinese))  # Both directions
    return frozenset(result)


def _derive_zhi_chong() -> FrozenSet[Tuple[str, str]]:
    """Derive string-based branch clashes from Enum-based RELATIONS.ZHI_CHONG."""
    result = set()
    for b1, b2 in RELATIONS.ZHI_CHONG:
        result.add((b1.chinese, b2.chinese))
        result.add((b2.chinese, b1.chinese))  # Both directions
    return frozenset(result)


# 天干相冲 - Heavenly Stem Clashes - DERIVED
GAN_XIANG_CHONG: FrozenSet[Tuple[str, str]] = _derive_gan_chong()

# 地支相冲 - Earthly Branch Clashes - DERIVED
ZHI_XIANG_CHONG: FrozenSet[Tuple[str, str]] = _derive_zhi_chong()


# =============================================================================
# WU BU YU SHI - Not derived (unique to this file)
# =============================================================================

# 五不遇时 - Wu Bu Yu Shi (Five Misfortune Hours)
# Unfavorable day stem + hour branch combinations
# This is presentation data, not part of core domain model
WU_BU_YU_SHI: FrozenSet[Tuple[str, str]] = frozenset([
    ('甲', '午'), ('乙', '巳'), ('丙', '辰'), ('丁', '卯'),
    ('戊', '寅'), ('己', '丑'), ('己', '亥'), ('庚', '子'),
    ('庚', '戌'), ('辛', '酉'), ('壬', '申'), ('癸', '未'),
])


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_gan_clash(gan1: str, gan2: str) -> bool:
    """Check if two heavenly stems clash."""
    return (gan1, gan2) in GAN_XIANG_CHONG


def is_zhi_clash(zhi1: str, zhi2: str) -> bool:
    """Check if two earthly branches clash."""
    return (zhi1, zhi2) in ZHI_XIANG_CHONG


def is_clash(char1: str, char2: str) -> bool:
    """Check if two characters (stems or branches) clash."""
    pair = (char1, char2)
    return pair in GAN_XIANG_CHONG or pair in ZHI_XIANG_CHONG


def is_wu_bu_yu_shi(day_gan: str, hour_zhi: str) -> bool:
    """Check if day stem and hour branch form Wu Bu Yu Shi."""
    return (day_gan, hour_zhi) in WU_BU_YU_SHI
