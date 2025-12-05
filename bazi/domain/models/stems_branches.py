"""
Heavenly Stems (天干) and Earthly Branches (地支) domain models.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, Tuple

from .elements import WuXing, YinYang


class HeavenlyStem(Enum):
    """Ten Heavenly Stems (天干)."""
    JIA = "甲"    # Wood Yang
    YI = "乙"     # Wood Yin
    BING = "丙"   # Fire Yang
    DING = "丁"   # Fire Yin
    WU = "戊"     # Earth Yang
    JI = "己"     # Earth Yin
    GENG = "庚"   # Metal Yang
    XIN = "辛"    # Metal Yin
    REN = "壬"    # Water Yang
    GUI = "癸"    # Water Yin

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def wuxing(self) -> WuXing:
        """The Five Element of this stem."""
        return _STEM_WUXING[self]

    @property
    def yinyang(self) -> YinYang:
        """The Yin-Yang polarity of this stem."""
        return _STEM_YINYANG[self]

    @classmethod
    def from_chinese(cls, char: str) -> HeavenlyStem:
        """Create HeavenlyStem from Chinese character."""
        for stem in cls:
            if stem.value == char:
                return stem
        raise ValueError(f"Unknown stem: {char}")

    @classmethod
    def all_ordered(cls) -> Tuple[HeavenlyStem, ...]:
        """Return all stems in traditional order."""
        return tuple(cls)


class EarthlyBranch(Enum):
    """Twelve Earthly Branches (地支)."""
    ZI = "子"     # Rat / Water
    CHOU = "丑"   # Ox / Earth
    YIN = "寅"    # Tiger / Wood
    MAO = "卯"    # Rabbit / Wood
    CHEN = "辰"   # Dragon / Earth
    SI = "巳"     # Snake / Fire
    WU = "午"     # Horse / Fire
    WEI = "未"    # Goat / Earth
    SHEN = "申"   # Monkey / Metal
    YOU = "酉"    # Rooster / Metal
    XU = "戌"     # Dog / Earth
    HAI = "亥"    # Pig / Water

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def wuxing(self) -> WuXing:
        """The Five Element of this branch."""
        return _BRANCH_WUXING[self]

    @property
    def hidden_stems(self) -> Dict[HeavenlyStem, float]:
        """Hidden stems within this branch with their ratios."""
        return dict(_HIDDEN_STEMS[self])

    @classmethod
    def from_chinese(cls, char: str) -> EarthlyBranch:
        """Create EarthlyBranch from Chinese character."""
        for branch in cls:
            if branch.value == char:
                return branch
        raise ValueError(f"Unknown branch: {char}")

    @classmethod
    def all_ordered(cls) -> Tuple[EarthlyBranch, ...]:
        """Return all branches in traditional order."""
        return tuple(cls)


# Stem → WuXing mapping
_STEM_WUXING: Dict[HeavenlyStem, WuXing] = {
    HeavenlyStem.JIA: WuXing.WOOD,
    HeavenlyStem.YI: WuXing.WOOD,
    HeavenlyStem.BING: WuXing.FIRE,
    HeavenlyStem.DING: WuXing.FIRE,
    HeavenlyStem.WU: WuXing.EARTH,
    HeavenlyStem.JI: WuXing.EARTH,
    HeavenlyStem.GENG: WuXing.METAL,
    HeavenlyStem.XIN: WuXing.METAL,
    HeavenlyStem.REN: WuXing.WATER,
    HeavenlyStem.GUI: WuXing.WATER,
}

# Stem → YinYang mapping
_STEM_YINYANG: Dict[HeavenlyStem, YinYang] = {
    HeavenlyStem.JIA: YinYang.YANG,
    HeavenlyStem.YI: YinYang.YIN,
    HeavenlyStem.BING: YinYang.YANG,
    HeavenlyStem.DING: YinYang.YIN,
    HeavenlyStem.WU: YinYang.YANG,
    HeavenlyStem.JI: YinYang.YIN,
    HeavenlyStem.GENG: YinYang.YANG,
    HeavenlyStem.XIN: YinYang.YIN,
    HeavenlyStem.REN: YinYang.YANG,
    HeavenlyStem.GUI: YinYang.YIN,
}

# Branch → WuXing mapping
_BRANCH_WUXING: Dict[EarthlyBranch, WuXing] = {
    EarthlyBranch.ZI: WuXing.WATER,
    EarthlyBranch.CHOU: WuXing.EARTH,
    EarthlyBranch.YIN: WuXing.WOOD,
    EarthlyBranch.MAO: WuXing.WOOD,
    EarthlyBranch.CHEN: WuXing.EARTH,
    EarthlyBranch.SI: WuXing.FIRE,
    EarthlyBranch.WU: WuXing.FIRE,
    EarthlyBranch.WEI: WuXing.EARTH,
    EarthlyBranch.SHEN: WuXing.METAL,
    EarthlyBranch.YOU: WuXing.METAL,
    EarthlyBranch.XU: WuXing.EARTH,
    EarthlyBranch.HAI: WuXing.WATER,
}

# Hidden stems within each branch (地支藏干)
_HIDDEN_STEMS: Dict[EarthlyBranch, Dict[HeavenlyStem, float]] = {
    EarthlyBranch.ZI: {HeavenlyStem.GUI: 1.0},
    EarthlyBranch.CHOU: {HeavenlyStem.JI: 0.5, HeavenlyStem.GUI: 0.3, HeavenlyStem.XIN: 0.2},
    EarthlyBranch.YIN: {HeavenlyStem.JIA: 0.6, HeavenlyStem.BING: 0.3, HeavenlyStem.WU: 0.1},
    EarthlyBranch.MAO: {HeavenlyStem.YI: 1.0},
    EarthlyBranch.CHEN: {HeavenlyStem.WU: 0.5, HeavenlyStem.YI: 0.3, HeavenlyStem.GUI: 0.2},
    EarthlyBranch.SI: {HeavenlyStem.BING: 0.6, HeavenlyStem.WU: 0.3, HeavenlyStem.GENG: 0.1},
    EarthlyBranch.WU: {HeavenlyStem.DING: 0.5, HeavenlyStem.JI: 0.5},
    EarthlyBranch.WEI: {HeavenlyStem.YI: 0.2, HeavenlyStem.JI: 0.5, HeavenlyStem.DING: 0.3},
    EarthlyBranch.SHEN: {HeavenlyStem.GENG: 0.6, HeavenlyStem.REN: 0.3, HeavenlyStem.WU: 0.1},
    EarthlyBranch.YOU: {HeavenlyStem.XIN: 1.0},
    EarthlyBranch.XU: {HeavenlyStem.WU: 0.5, HeavenlyStem.XIN: 0.3, HeavenlyStem.DING: 0.2},
    EarthlyBranch.HAI: {HeavenlyStem.REN: 0.7, HeavenlyStem.JIA: 0.3},
}


@dataclass(frozen=True)
class StemBranchRelations:
    """Relationship constants between stems and branches."""

    # Six Harmonies (六合) - branch pairs that combine
    LIU_HE: FrozenSet[Tuple[EarthlyBranch, EarthlyBranch]] = frozenset({
        (EarthlyBranch.ZI, EarthlyBranch.CHOU),
        (EarthlyBranch.YIN, EarthlyBranch.HAI),
        (EarthlyBranch.MAO, EarthlyBranch.XU),
        (EarthlyBranch.CHEN, EarthlyBranch.YOU),
        (EarthlyBranch.SI, EarthlyBranch.SHEN),
        (EarthlyBranch.WU, EarthlyBranch.WEI),
    })

    # Five Combinations (五合) - stem pairs that combine
    WU_HE: FrozenSet[Tuple[HeavenlyStem, HeavenlyStem]] = frozenset({
        (HeavenlyStem.JIA, HeavenlyStem.JI),
        (HeavenlyStem.YI, HeavenlyStem.GENG),
        (HeavenlyStem.BING, HeavenlyStem.XIN),
        (HeavenlyStem.DING, HeavenlyStem.REN),
        (HeavenlyStem.WU, HeavenlyStem.GUI),
    })

    # Stem clashes (天干相冲)
    GAN_CHONG: FrozenSet[Tuple[HeavenlyStem, HeavenlyStem]] = frozenset({
        (HeavenlyStem.JIA, HeavenlyStem.GENG),
        (HeavenlyStem.YI, HeavenlyStem.XIN),
        (HeavenlyStem.BING, HeavenlyStem.REN),
        (HeavenlyStem.DING, HeavenlyStem.GUI),
    })

    # Branch clashes (地支相冲)
    ZHI_CHONG: FrozenSet[Tuple[EarthlyBranch, EarthlyBranch]] = frozenset({
        (EarthlyBranch.ZI, EarthlyBranch.WU),
        (EarthlyBranch.CHOU, EarthlyBranch.WEI),
        (EarthlyBranch.YIN, EarthlyBranch.SHEN),
        (EarthlyBranch.MAO, EarthlyBranch.YOU),
        (EarthlyBranch.CHEN, EarthlyBranch.XU),
        (EarthlyBranch.SI, EarthlyBranch.HAI),
    })


# Singleton for relations
RELATIONS = StemBranchRelations()
