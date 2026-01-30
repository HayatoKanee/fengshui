"""
Ten Gods (十神) domain models.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict

from .elements import WuXing, WuXingRelation, get_wuxing_relation
from .stems_branches import HeavenlyStem


class ShiShen(Enum):
    """
    Ten Gods (十神) - the relationship between Day Master and other elements.

    The Ten Gods represent different aspects of life and relationships
    based on the WuXing relationship and Yin-Yang polarity.
    """
    # Same element (比和)
    BI_JIAN = "比肩"      # Shoulder to Shoulder (same element, same polarity)
    JIE_CAI = "比劫"      # Rob Wealth (same element, different polarity) - also called 劫财

    # Element I generate (我生)
    SHI_SHEN = "食神"     # Eating God (I generate, same polarity)
    SHANG_GUAN = "伤官"   # Hurting Officer (I generate, different polarity)

    # Element I overcome (我克)
    ZHENG_CAI = "正财"    # Direct Wealth (I overcome, different polarity)
    PIAN_CAI = "偏财"     # Indirect Wealth (I overcome, same polarity)

    # Element that overcomes me (克我)
    ZHENG_GUAN = "正官"   # Direct Officer (overcomes me, different polarity)
    QI_SHA = "七杀"       # Seven Killings (overcomes me, same polarity) - also called 偏官

    # Element that generates me (生我)
    ZHENG_YIN = "正印"    # Direct Seal (generates me, different polarity)
    PIAN_YIN = "偏印"     # Indirect Seal (generates me, same polarity)

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def is_favorable(self) -> bool:
        """Whether this ShiShen is generally considered favorable."""
        return self in _FAVORABLE_SHISHEN

    @property
    def category(self) -> str:
        """Category of this ShiShen."""
        return _SHISHEN_CATEGORIES[self]


# Generally favorable ShiShen
_FAVORABLE_SHISHEN = {
    ShiShen.ZHENG_YIN,
    ShiShen.ZHENG_GUAN,
    ShiShen.ZHENG_CAI,
    ShiShen.SHI_SHEN,
    ShiShen.BI_JIAN,
}

# ShiShen categories
_SHISHEN_CATEGORIES: Dict[ShiShen, str] = {
    ShiShen.BI_JIAN: "比和",
    ShiShen.JIE_CAI: "比和",
    ShiShen.SHI_SHEN: "我生",
    ShiShen.SHANG_GUAN: "我生",
    ShiShen.ZHENG_CAI: "我克",
    ShiShen.PIAN_CAI: "我克",
    ShiShen.ZHENG_GUAN: "克我",
    ShiShen.QI_SHA: "克我",
    ShiShen.ZHENG_YIN: "生我",
    ShiShen.PIAN_YIN: "生我",
}


# ShiShen lookup by (WuXingRelation, same_polarity)
# ShiShen = WuXingRelation + YinYang polarity
_SHISHEN_LOOKUP: Dict[tuple, ShiShen] = {
    (WuXingRelation.SAME, True): ShiShen.BI_JIAN,
    (WuXingRelation.SAME, False): ShiShen.JIE_CAI,
    (WuXingRelation.I_GENERATE, True): ShiShen.SHI_SHEN,
    (WuXingRelation.I_GENERATE, False): ShiShen.SHANG_GUAN,
    (WuXingRelation.I_OVERCOME, True): ShiShen.PIAN_CAI,
    (WuXingRelation.I_OVERCOME, False): ShiShen.ZHENG_CAI,
    (WuXingRelation.OVERCOMES_ME, True): ShiShen.QI_SHA,
    (WuXingRelation.OVERCOMES_ME, False): ShiShen.ZHENG_GUAN,
    (WuXingRelation.GENERATES_ME, True): ShiShen.PIAN_YIN,
    (WuXingRelation.GENERATES_ME, False): ShiShen.ZHENG_YIN,
}


def calculate_shishen(day_master: HeavenlyStem, other: HeavenlyStem) -> ShiShen:
    """
    Calculate the ShiShen relationship between Day Master and another stem.

    ShiShen = WuXingRelation + YinYang polarity (5 relations × 2 polarities = 10 gods)

    Args:
        day_master: The Day Master (日主) stem
        other: The other stem to compare

    Returns:
        The ShiShen relationship
    """
    relation = get_wuxing_relation(day_master.wuxing, other.wuxing)
    same_polarity = day_master.yinyang == other.yinyang
    return _SHISHEN_LOOKUP[(relation, same_polarity)]


@dataclass(frozen=True)
class ShiShenChart:
    """
    Complete ShiShen analysis for a BaZi chart.

    Maps each position's ShiShen relationship to the Day Master.
    """
    year_stem: ShiShen
    year_branch_main: ShiShen  # Main hidden stem of branch
    month_stem: ShiShen
    month_branch_main: ShiShen
    day_branch_main: ShiShen   # Day stem is always self (日主)
    hour_stem: ShiShen
    hour_branch_main: ShiShen

    @property
    def all_shishen(self) -> Dict[str, ShiShen]:
        """All ShiShen as a dictionary."""
        return {
            "year_stem": self.year_stem,
            "year_branch": self.year_branch_main,
            "month_stem": self.month_stem,
            "month_branch": self.month_branch_main,
            "day_branch": self.day_branch_main,
            "hour_stem": self.hour_stem,
            "hour_branch": self.hour_branch_main,
        }

    def count(self) -> Dict[ShiShen, int]:
        """Count occurrences of each ShiShen."""
        result: Dict[ShiShen, int] = {ss: 0 for ss in ShiShen}
        for ss in self.all_shishen.values():
            result[ss] += 1
        return result
