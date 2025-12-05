"""
WuXing (Five Elements) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from ..models import (
    WuXing,
    WangXiang,
    Pillar,
    BaZi,
    HeavenlyStem,
    EarthlyBranch,
    WuXingStrength,
)


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
        stem_element = stem.wuxing
        branch_element = branch.wuxing

        if stem_element == branch_element:
            return (10, 10)
        elif stem_element.generates == branch_element:
            return (6, 8)
        elif stem_element.overcomes == branch_element:
            return (4, 2)
        elif branch_element.overcomes == stem_element:
            return (2, 4)
        elif branch_element.generates == stem_element:
            return (8, 6)

        return (5, 5)  # Default fallback

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

    def calculate_pillar_strength(
        self,
        pillar: Pillar,
        wang_xiang: Dict[WuXing, WangXiang]
    ) -> Tuple[float, List[float]]:
        """
        Calculate the strength values for a pillar.

        Returns:
            Tuple of (stem_strength, [hidden_stem_strengths])
        """
        # Base relationship values
        stem_value, branch_value = self.get_pillar_values(pillar)

        # Apply wang_xiang multiplier to stem
        stem_multiplier = self.calculate_wang_xiang_multiplier(pillar.stem_wuxing, wang_xiang)
        stem_strength = stem_value * stem_multiplier

        # Calculate hidden stem strengths
        hidden_strengths = []
        for hidden_stem, ratio in pillar.hidden_stems.items():
            hidden_element = hidden_stem.wuxing
            hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
            hidden_strength = branch_value * ratio * hidden_multiplier
            hidden_strengths.append(hidden_strength)

        return (stem_strength, hidden_strengths)

    def accumulate_wuxing_values(
        self,
        bazi: BaZi,
        wang_xiang: Dict[WuXing, WangXiang]
    ) -> Dict[WuXing, float]:
        """
        Calculate the accumulated WuXing values for an entire BaZi chart.

        Args:
            bazi: The BaZi chart
            wang_xiang: The seasonal WangXiang mapping

        Returns:
            Dictionary mapping each WuXing to its accumulated strength value.
        """
        result: Dict[WuXing, float] = {element: 0.0 for element in WuXing}

        for pillar in bazi.pillars:
            # Add stem value
            stem_value, _ = self.get_pillar_values(pillar)
            stem_multiplier = self.calculate_wang_xiang_multiplier(pillar.stem_wuxing, wang_xiang)
            result[pillar.stem_wuxing] += stem_value * stem_multiplier

            # Add hidden stem values
            _, branch_value = self.get_pillar_values(pillar)
            for hidden_stem, ratio in pillar.hidden_stems.items():
                hidden_element = hidden_stem.wuxing
                hidden_multiplier = self.calculate_wang_xiang_multiplier(hidden_element, wang_xiang)
                result[hidden_element] += branch_value * ratio * hidden_multiplier

        return result

    def calculate_strength(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False
    ) -> WuXingStrength:
        """
        Calculate the complete WuXing strength analysis for a BaZi chart.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            WuXingStrength with raw and adjusted values
        """
        # Get wang_xiang based on month branch
        wang_xiang_map = self.get_wang_xiang(bazi.month_pillar.branch, is_earth_dominant)

        # Calculate raw values (without seasonal adjustment)
        raw_values: Dict[WuXing, float] = {element: 0.0 for element in WuXing}
        for pillar in bazi.pillars:
            stem_value, branch_value = self.get_pillar_values(pillar)
            raw_values[pillar.stem_wuxing] += stem_value
            for hidden_stem, ratio in pillar.hidden_stems.items():
                raw_values[hidden_stem.wuxing] += branch_value * ratio

        # Calculate adjusted values (with seasonal adjustment)
        adjusted_values = self.accumulate_wuxing_values(bazi, wang_xiang_map)

        return WuXingStrength(
            raw_values=raw_values,
            wang_xiang=wang_xiang_map,
            adjusted_values=adjusted_values,
        )
