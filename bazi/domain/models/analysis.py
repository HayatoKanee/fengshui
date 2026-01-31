"""
BaZi analysis result models.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from .elements import WuXing, WangXiang
from .bazi import BaZi, BirthData
from .shishen import ShiShen, ShiShenChart
from .shensha import ShenSha, ShenShaAnalysis

if TYPE_CHECKING:
    from ..services.ganzhi_interaction import GanZhiInteractions


@dataclass
class WuXingStrength:
    """
    Strength analysis of each WuXing element.

    Contains raw values, seasonal adjustments, and 合会冲克刑 interactions.
    """
    raw_values: Dict[WuXing, float]
    wang_xiang: Dict[WuXing, WangXiang]
    adjusted_values: Dict[WuXing, float]
    interactions: Optional[Any] = None  # GanZhiInteractions (避免循环导入)

    @property
    def total(self) -> float:
        """Total of all adjusted values."""
        return sum(self.adjusted_values.values())

    def percentage(self, element: WuXing) -> float:
        """Percentage of total for a specific element."""
        if self.total == 0:
            return 0.0
        return (self.adjusted_values[element] / self.total) * 100

    @property
    def strongest(self) -> WuXing:
        """The strongest element."""
        return max(self.adjusted_values, key=lambda k: self.adjusted_values[k])

    @property
    def weakest(self) -> WuXing:
        """The weakest element."""
        return min(self.adjusted_values, key=lambda k: self.adjusted_values[k])

    @property
    def has_combinations(self) -> bool:
        """是否有合局"""
        if self.interactions is None:
            return False
        return bool(
            self.interactions.stem_combinations or
            self.interactions.branch_combinations
        )

    @property
    def has_clashes(self) -> bool:
        """是否有相冲"""
        if self.interactions is None:
            return False
        return bool(self.interactions.branch_clashes)


@dataclass(frozen=True)
class DayMasterStrength:
    """
    Day Master (日主) strength analysis.

    Determines if the Day Master is strong or weak.
    """
    beneficial_value: float   # 生扶 - elements that help
    harmful_value: float      # 耗泄克 - elements that drain

    @property
    def total(self) -> float:
        return self.beneficial_value + self.harmful_value

    @property
    def beneficial_percentage(self) -> float:
        """Percentage of beneficial elements."""
        if self.total == 0:
            return 50.0
        return (self.beneficial_value / self.total) * 100

    @property
    def harmful_percentage(self) -> float:
        """Percentage of harmful elements."""
        return 100.0 - self.beneficial_percentage

    @property
    def is_strong(self) -> bool:
        """Whether the Day Master is considered strong (身强)."""
        return self.beneficial_percentage >= 50.0

    @property
    def strength_level(self) -> str:
        """
        日主强弱判断。
        Qualitative strength level based on 50% threshold.
        """
        return "身强" if self.is_strong else "身弱"


@dataclass(frozen=True)
class FavorableElements:
    """
    Favorable and unfavorable elements for a BaZi chart (用神/忌神).
    """
    yong_shen: WuXing          # 用神 - Most needed element
    xi_shen: Optional[WuXing]  # 喜神 - Supportive element
    ji_shen: WuXing            # 忌神 - Element to avoid
    chou_shen: Optional[WuXing] = None  # 仇神 - Hostile element

    @property
    def favorable(self) -> List[WuXing]:
        """List of favorable elements."""
        result = [self.yong_shen]
        if self.xi_shen:
            result.append(self.xi_shen)
        return result

    @property
    def unfavorable(self) -> List[WuXing]:
        """List of unfavorable elements."""
        result = [self.ji_shen]
        if self.chou_shen:
            result.append(self.chou_shen)
        return result


@dataclass
class BaZiAnalysis:
    """
    Complete BaZi analysis result.

    This is the main output of a BaZi reading, containing all
    calculated attributes and interpretations.
    """
    # Input data
    birth_data: BirthData
    bazi: BaZi

    # Core analysis
    wuxing_strength: WuXingStrength
    day_master_strength: DayMasterStrength
    shishen_chart: ShiShenChart
    favorable_elements: FavorableElements

    # ShenSha analysis
    shensha: ShenShaAnalysis

    # Optional interpretations
    personality_traits: List[str] = field(default_factory=list)
    career_suggestions: List[str] = field(default_factory=list)
    relationship_analysis: Optional[str] = None
    health_notes: List[str] = field(default_factory=list)

    # Luck periods (can be populated separately)
    current_luck_period: Optional[str] = None
    annual_fortune: Optional[str] = None

    @property
    def summary(self) -> str:
        """Brief summary of the analysis."""
        dm = self.bazi.day_master
        strength = self.day_master_strength.strength_level
        yong = self.favorable_elements.yong_shen.chinese
        return f"日主{dm.chinese}({dm.wuxing.chinese})，{strength}，用神{yong}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "bazi": str(self.bazi),
            "day_master": self.bazi.day_master.chinese,
            "day_master_wuxing": self.bazi.day_master_wuxing.chinese,
            "strength_level": self.day_master_strength.strength_level,
            "beneficial_pct": round(self.day_master_strength.beneficial_percentage, 1),
            "yong_shen": self.favorable_elements.yong_shen.chinese,
            "ji_shen": self.favorable_elements.ji_shen.chinese,
            "shensha_count": len(self.shensha.shensha_list),
            "beneficial_shensha": [ss.chinese for ss in self.shensha.beneficial],
        }
