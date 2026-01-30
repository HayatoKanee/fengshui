"""
String-based element lookups - DERIVED from domain Enums.

This module provides string-to-string conversions for:
- Presentation layer (templates)
- External library integration (lunar_python returns strings)

IMPORTANT: These are derived from the authoritative Enum definitions in
`bazi.domain.models.elements` and `bazi.domain.models.stems_branches`.
DO NOT add data here - add to the Enum definitions instead.

For domain logic, use Enums directly:
    from bazi.domain.models import WuXing, HeavenlyStem

For string conversion (presentation/external):
    from bazi.domain.constants import GAN_WUXING, get_stem_wuxing
"""
from typing import Dict, FrozenSet, Tuple

from ..models.elements import WuXing, YinYang
from ..models.stems_branches import HeavenlyStem, EarthlyBranch


# =============================================================================
# DERIVED LOOKUPS - Generated from Enums (single source of truth)
# =============================================================================

# 天干五行 - Heavenly Stems to WuXing (derived from HeavenlyStem enum)
GAN_WUXING: Dict[str, str] = {
    stem.chinese: stem.wuxing.chinese for stem in HeavenlyStem
}

# 地支五行 - Earthly Branches to WuXing (derived from EarthlyBranch enum)
ZHI_WUXING: Dict[str, str] = {
    branch.chinese: branch.wuxing.chinese for branch in EarthlyBranch
}

# 干支五行 - Combined (derived)
GANZHI_WUXING: Dict[str, str] = {**GAN_WUXING, **ZHI_WUXING}

# 天干阴阳 - Heavenly Stems Yin/Yang (derived from HeavenlyStem enum)
GAN_YINYANG: Dict[str, str] = {
    stem.chinese: stem.yinyang.chinese for stem in HeavenlyStem
}

# 五行列表 (derived from WuXing enum)
WUXING_LIST: FrozenSet[str] = frozenset(e.chinese for e in WuXing)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_stem_wuxing(stem: str) -> str:
    """Get WuXing element for a Heavenly Stem (Chinese character)."""
    return GAN_WUXING.get(stem, '')


def get_branch_wuxing(branch: str) -> str:
    """Get WuXing element for an Earthly Branch (Chinese character)."""
    return ZHI_WUXING.get(branch, '')


def get_stem_yinyang(stem: str) -> str:
    """Get Yin/Yang polarity for a Heavenly Stem (Chinese character)."""
    return GAN_YINYANG.get(stem, '')


def stem_from_chinese(char: str) -> HeavenlyStem:
    """Convert Chinese character to HeavenlyStem Enum."""
    return HeavenlyStem.from_chinese(char)


def branch_from_chinese(char: str) -> EarthlyBranch:
    """Convert Chinese character to EarthlyBranch Enum."""
    return EarthlyBranch.from_chinese(char)


def wuxing_from_chinese(char: str) -> WuXing:
    """Convert Chinese character to WuXing Enum."""
    return WuXing.from_chinese(char)


# =============================================================================
# HOUR INFORMATION (Static data - no Enum equivalent needed)
# =============================================================================

# 时辰 - Chinese Hours (Shichen)
# Mapping from hour number to (name, time_range, earthly_branch)
HOUR_INFO: Dict[int, Tuple[str, str, str]] = {
    0: ("子时", "23:00-01:00", "子"),   # Zi hour (late night)
    1: ("丑时", "01:00-03:00", "丑"),   # Chou hour
    3: ("寅时", "03:00-05:00", "寅"),   # Yin hour
    5: ("卯时", "05:00-07:00", "卯"),   # Mao hour
    7: ("辰时", "07:00-09:00", "辰"),   # Chen hour
    9: ("巳时", "09:00-11:00", "巳"),   # Si hour
    11: ("午时", "11:00-13:00", "午"),  # Wu hour
    13: ("未时", "13:00-15:00", "未"),  # Wei hour
    15: ("申时", "15:00-17:00", "申"),  # Shen hour
    17: ("酉时", "17:00-19:00", "酉"),  # You hour
    19: ("戌时", "19:00-21:00", "戌"),  # Xu hour
    21: ("亥时", "21:00-23:00", "亥"),  # Hai hour
    23: ("子时", "23:00-01:00", "子"),  # Zi hour (early part)
}

# List of valid zodiac hours
ZODIAC_HOURS: Tuple[int, ...] = (0, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21)


def get_hour_name(hour: int) -> str:
    """Get Chinese hour name for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[0] if info else ""


def get_hour_time_range(hour: int) -> str:
    """Get time range for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[1] if info else ""


def get_hour_branch(hour: int) -> str:
    """Get earthly branch for a given hour number."""
    info = HOUR_INFO.get(hour)
    return info[2] if info else ""


def get_hour_display(hour: int) -> str:
    """Get display string for a given hour (name + time range)."""
    info = HOUR_INFO.get(hour)
    if info:
        return f"{info[0]} ({info[1]})"
    return ""
