"""
ShenSha (神煞) - Auxiliary stars domain models.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, List, Optional, Tuple


# ============================================================
# Shared Constants
# ============================================================

PILLAR_POSITIONS: Tuple[str, ...] = ("year", "month", "day", "hour")
"""Standard pillar position names used throughout the system."""


class ShenShaType(Enum):
    """Types of ShenSha (神煞) - auxiliary stars/spirits."""

    # Beneficial stars (吉星)
    TIAN_YI_GUI_REN = "天乙贵人"    # Heavenly Noble
    TIAN_DE = "天德"                # Heavenly Virtue
    TIAN_DE_HE = "天德合"           # Heavenly Virtue Combination
    YUE_DE = "月德"                 # Monthly Virtue
    WEN_CHANG = "文昌"              # Literary Prosperity
    LU_SHEN = "禄神"                # Prosperity Spirit
    JIANG_XING = "将星"             # General Star
    HUA_GAI = "华盖"                # Canopy Star
    SAN_QI = "三奇"                 # Three Wonders

    # Challenging stars (凶星)
    YANG_REN = "羊刃"               # Goat Blade
    QI_SHA = "七杀"                 # Seven Killings (star version)
    KONG_WANG = "空亡"              # Void/Emptiness

    # Relationship stars
    TAO_HUA = "桃花"                # Peach Blossom (romance)
    HONG_YAN_SHA = "红艳煞"         # Red Beauty Star
    GU_CHEN = "孤辰"                # Lonely Star (male)
    GUA_SU = "寡宿"                 # Widow Star (female)

    # Movement/travel stars
    YI_MA = "驿马"                  # Traveling Horse

    # Misfortune stars
    JIE_SHA = "劫煞"                # Robbery Star
    WANG_SHEN = "亡神"              # Death Spirit

    # Special day stars (for date selection)
    YANG_GONG_JI_RI = "杨公忌日"    # Yang Gong Taboo Day
    PO_RI = "破日"                  # Breaking Day
    SI_JUE_RI = "四绝日"            # Four Extinction Days
    SI_LI_RI = "四离日"             # Four Separation Days

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def is_beneficial(self) -> bool:
        """Whether this ShenSha is generally beneficial."""
        return self in _BENEFICIAL_SHENSHA

    @property
    def category(self) -> str:
        """Category of this ShenSha."""
        return SHENSHA_CATEGORIES.get(self, "其他")


# Beneficial ShenSha
_BENEFICIAL_SHENSHA = {
    ShenShaType.TIAN_YI_GUI_REN,
    ShenShaType.TIAN_DE,
    ShenShaType.TIAN_DE_HE,
    ShenShaType.YUE_DE,
    ShenShaType.WEN_CHANG,
    ShenShaType.LU_SHEN,
    ShenShaType.JIANG_XING,
    ShenShaType.HUA_GAI,
    ShenShaType.SAN_QI,
}

# ShenSha categories - single source of truth for category mapping
SHENSHA_CATEGORIES: dict[ShenShaType, str] = {
    ShenShaType.TIAN_YI_GUI_REN: "贵人",
    ShenShaType.TIAN_DE: "德星",
    ShenShaType.TIAN_DE_HE: "德星",
    ShenShaType.YUE_DE: "德星",
    ShenShaType.WEN_CHANG: "文星",
    ShenShaType.LU_SHEN: "禄星",
    ShenShaType.JIANG_XING: "将星",
    ShenShaType.HUA_GAI: "艺术",
    ShenShaType.YANG_REN: "刃星",
    ShenShaType.TAO_HUA: "桃花",
    ShenShaType.HONG_YAN_SHA: "桃花",
    ShenShaType.GU_CHEN: "孤寡",
    ShenShaType.GUA_SU: "孤寡",
    ShenShaType.YI_MA: "驿马",
    ShenShaType.JIE_SHA: "凶煞",
    ShenShaType.WANG_SHEN: "凶煞",
    ShenShaType.KONG_WANG: "空亡",
}

# Backward compatibility alias
_SHENSHA_CATEGORIES = SHENSHA_CATEGORIES


def get_all_categories() -> FrozenSet[str]:
    """Get all unique category names from SHENSHA_CATEGORIES."""
    return frozenset(SHENSHA_CATEGORIES.values()) | {"其他"}


@dataclass(frozen=True)
class ShenSha:
    """
    A single ShenSha occurrence in a BaZi chart.

    Records what type, where it appears, and optionally what triggers it.
    """
    type: ShenShaType
    position: str  # e.g., "year_branch", "day_stem", etc.
    triggered_by: Optional[str] = None  # What stem/branch triggered this

    @property
    def chinese(self) -> str:
        return self.type.chinese

    @property
    def is_beneficial(self) -> bool:
        return self.type.is_beneficial


@dataclass
class ShenShaAnalysis:
    """
    Complete ShenSha analysis for a BaZi chart.
    """
    shensha_list: List[ShenSha]

    @property
    def beneficial(self) -> List[ShenSha]:
        """Filter to only beneficial ShenSha."""
        return [ss for ss in self.shensha_list if ss.is_beneficial]

    @property
    def challenging(self) -> List[ShenSha]:
        """Filter to only challenging ShenSha."""
        return [ss for ss in self.shensha_list if not ss.is_beneficial]

    def has(self, shensha_type: ShenShaType) -> bool:
        """Check if a specific ShenSha type is present."""
        return any(ss.type == shensha_type for ss in self.shensha_list)

    def count_by_type(self) -> dict[ShenShaType, int]:
        """Count occurrences of each ShenSha type."""
        result: dict[ShenShaType, int] = {}
        for ss in self.shensha_list:
            result[ss.type] = result.get(ss.type, 0) + 1
        return result

    def get_by_position(self, position: str) -> List[ShenSha]:
        """Get all ShenSha at a specific position."""
        return [ss for ss in self.shensha_list if ss.position == position]
