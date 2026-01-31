"""
WuXing (Five Elements) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Tuple

from ..models import (
    WuXing,
    WangXiang,
    Pillar,
    BaZi,
    HeavenlyStem,
    EarthlyBranch,
    WuXingStrength,
    get_wuxing_relation,
    RELATIONSHIP_WEIGHTS,
)

if TYPE_CHECKING:
    from .ganzhi_interaction import GanZhiInteractionService, GanZhiInteractions


# Season to WangXiang mapping for each element
_SEASON_PHASES: Dict[str, Dict[WuXing, WangXiang]] = {
    "春": {
        WuXing.WOOD: WangXiang.WANG,
        WuXing.FIRE: WangXiang.XIANG,
        WuXing.WATER: WangXiang.XIU,
        WuXing.METAL: WangXiang.QIU,
        WuXing.EARTH: WangXiang.SI,
    },
    "夏": {
        WuXing.FIRE: WangXiang.WANG,
        WuXing.EARTH: WangXiang.XIANG,
        WuXing.WOOD: WangXiang.XIU,
        WuXing.WATER: WangXiang.QIU,
        WuXing.METAL: WangXiang.SI,
    },
    "秋": {
        WuXing.METAL: WangXiang.WANG,
        WuXing.WATER: WangXiang.XIANG,
        WuXing.EARTH: WangXiang.XIU,
        WuXing.FIRE: WangXiang.QIU,
        WuXing.WOOD: WangXiang.SI,
    },
    "冬": {
        WuXing.WATER: WangXiang.WANG,
        WuXing.WOOD: WangXiang.XIANG,
        WuXing.METAL: WangXiang.XIU,
        WuXing.EARTH: WangXiang.QIU,
        WuXing.FIRE: WangXiang.SI,
    },
    # Earth phase (土旺) during seasonal transitions
    "土旺": {
        WuXing.EARTH: WangXiang.WANG,
        WuXing.METAL: WangXiang.XIANG,
        WuXing.FIRE: WangXiang.XIU,
        WuXing.WOOD: WangXiang.QIU,
        WuXing.WATER: WangXiang.SI,
    },
}

# Branch to season mapping
_BRANCH_SEASONS: Dict[EarthlyBranch, str] = {
    EarthlyBranch.YIN: "春",
    EarthlyBranch.MAO: "春",
    EarthlyBranch.CHEN: "春",
    EarthlyBranch.SI: "夏",
    EarthlyBranch.WU: "夏",
    EarthlyBranch.WEI: "夏",
    EarthlyBranch.SHEN: "秋",
    EarthlyBranch.YOU: "秋",
    EarthlyBranch.XU: "秋",
    EarthlyBranch.HAI: "冬",
    EarthlyBranch.ZI: "冬",
    EarthlyBranch.CHOU: "冬",
}

# Earth-dominant branches (四库)
_EARTH_BRANCHES = {EarthlyBranch.CHEN, EarthlyBranch.WEI, EarthlyBranch.XU, EarthlyBranch.CHOU}




class WuXingCalculator:
    """
    Calculator for WuXing (Five Elements) relationships and values.

    This service handles all calculations related to the Five Elements,
    including relationships, seasonal strength, and accumulated values.
    """

    @staticmethod
    def get_relationship_values(stem: HeavenlyStem, branch: EarthlyBranch) -> Tuple[int, int]:
        """
        Calculate the relationship values between a stem and branch.

        Returns:
            Tuple of (stem_value, branch_value) based on their WuXing relationship.
        """
        relation = get_wuxing_relation(stem.wuxing, branch.wuxing)
        return RELATIONSHIP_WEIGHTS[relation]

    @staticmethod
    def get_pillar_values(pillar: Pillar) -> Tuple[int, int]:
        """Get relationship values for a pillar."""
        return WuXingCalculator.get_relationship_values(pillar.stem, pillar.branch)

    @staticmethod
    def get_season(month_branch: EarthlyBranch, is_earth_dominant: bool = False) -> str:
        """
        Determine the season from the month branch.

        Args:
            month_branch: The earthly branch of the month pillar
            is_earth_dominant: Whether we're in the earth-dominant period
                              (last 18 days before season change)
        """
        if is_earth_dominant and month_branch in _EARTH_BRANCHES:
            return "土旺"
        return _BRANCH_SEASONS[month_branch]

    @staticmethod
    def get_wang_xiang(month_branch: EarthlyBranch, is_earth_dominant: bool = False) -> Dict[WuXing, WangXiang]:
        """
        Get the WangXiang (seasonal strength) mapping for the current season.

        Args:
            month_branch: The earthly branch of the month pillar
            is_earth_dominant: Whether we're in the earth-dominant period
        """
        season = WuXingCalculator.get_season(month_branch, is_earth_dominant)
        return _SEASON_PHASES[season]

    @staticmethod
    def calculate_wang_xiang_multiplier(element: WuXing, wang_xiang: Dict[WuXing, WangXiang]) -> float:
        """Get the strength multiplier for an element based on season."""
        phase = wang_xiang.get(element, WangXiang.XIU)
        return phase.multiplier

    def _accumulate_pillar_values(
        self,
        bazi: BaZi,
        wang_xiang: Dict[WuXing, WangXiang],
        interactions: Optional["GanZhiInteractions"] = None,
    ) -> Dict[WuXing, float]:
        """
        Accumulate WuXing values from all pillars with seasonal adjustment.

        Args:
            bazi: The BaZi chart
            wang_xiang: Seasonal strength mapping
            interactions: 合会冲克刑 interactions for position-specific modifiers

        Returns:
            Dictionary mapping each WuXing to its accumulated value.
        """
        from .ganzhi_interaction import PillarPosition

        result: Dict[WuXing, float] = {element: 0.0 for element in WuXing}

        # Map pillars to positions
        pillar_positions = [
            (bazi.year_pillar, PillarPosition.YEAR),
            (bazi.month_pillar, PillarPosition.MONTH),
            (bazi.day_pillar, PillarPosition.DAY),
            (bazi.hour_pillar, PillarPosition.HOUR),
        ]

        for pillar, position in pillar_positions:
            stem_value, branch_value = self.get_pillar_values(pillar)

            # Get position-specific reductions
            stem_reduction = 0.0
            hidden_reduction = 0.0
            if interactions:
                stem_reduction = interactions.get_stem_reduction(position)
                hidden_reduction = interactions.get_hidden_stem_reduction(position)

            # Stem contribution (with reduction if involved in 合/冲)
            stem_multiplier = self.calculate_wang_xiang_multiplier(pillar.stem_wuxing, wang_xiang)
            effective_stem_value = stem_value * (1 - stem_reduction)
            result[pillar.stem_wuxing] += effective_stem_value * stem_multiplier

            # Hidden stems contribution (with reduction if involved in 合/冲/刑/害)
            for hidden_stem, ratio in pillar.hidden_stems.items():
                hidden_element = hidden_stem.wuxing
                hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
                effective_hidden_value = branch_value * ratio * (1 - hidden_reduction)
                result[hidden_element] += effective_hidden_value * hidden_multiplier

        return result

    def accumulate_wuxing_values(
        self,
        bazi: BaZi,
        wang_xiang: Dict[WuXing, WangXiang],
    ) -> Dict[WuXing, float]:
        """
        Public wrapper for backward compatibility.

        Accumulates WuXing values without interaction modifiers.
        """
        return self._accumulate_pillar_values(bazi, wang_xiang, None)

    def calculate_strength(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False,
        include_interactions: bool = True,
    ) -> WuXingStrength:
        """
        Calculate the complete WuXing strength analysis for a BaZi chart.

        考虑合会冲克刑对五行力量的影响:
        - 天干合/地支合: 被合的天干/藏干力量减少
        - 地支冲/刑/害: 被冲刑害的藏干力量减少
        - 合局成功: 化神五行获得额外力量

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period
            include_interactions: Whether to include 合会冲克刑 modifiers

        Returns:
            WuXingStrength with raw and adjusted values
        """
        wang_xiang_map = self.get_wang_xiang(bazi.month_pillar.branch, is_earth_dominant)

        # Neutral wang_xiang for raw values (all XIU = 1.0 multiplier)
        neutral_wang_xiang: Dict[WuXing, WangXiang] = {e: WangXiang.XIU for e in WuXing}

        # Analyze interactions first
        interactions: Optional["GanZhiInteractions"] = None
        if include_interactions:
            from .ganzhi_interaction import GanZhiInteractionService
            interaction_service = GanZhiInteractionService()
            interactions = interaction_service.analyze(bazi)

        # Calculate raw values (without interactions, without wang_xiang)
        raw_values = self._accumulate_pillar_values(bazi, neutral_wang_xiang, None)

        # Calculate adjusted values (with interactions, with wang_xiang)
        adjusted_values = self._accumulate_pillar_values(bazi, wang_xiang_map, interactions)

        # Add bonus from successful combinations (三会/三合/六合)
        if interactions:
            for element, bonus in interactions.wuxing_bonus.items():
                adjusted_values[element] += bonus

            # Ensure no negative values
            for element in adjusted_values:
                if adjusted_values[element] < 0:
                    adjusted_values[element] = 0.0

        return WuXingStrength(
            raw_values=raw_values,
            wang_xiang=wang_xiang_map,
            adjusted_values=adjusted_values,
            interactions=interactions,
        )
