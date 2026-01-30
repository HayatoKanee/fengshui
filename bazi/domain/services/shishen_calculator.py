"""
ShiShen (Ten Gods) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..models import (
    BaZi,
    HeavenlyStem,
    ShiShen,
    ShiShenChart,
    calculate_shishen,
)


class ShiShenCalculator:
    """
    Calculator for ShiShen (Ten Gods) relationships.

    The Ten Gods represent the relationship between the Day Master
    and other elements in the chart, indicating different aspects of life.
    """

    @staticmethod
    def calculate(day_master: HeavenlyStem, other: HeavenlyStem) -> ShiShen:
        """
        Calculate the ShiShen relationship between Day Master and another stem.

        This is a convenience wrapper around the model-level function.
        """
        return calculate_shishen(day_master, other)

    def calculate_for_pillar(
        self,
        day_master: HeavenlyStem,
        stem: HeavenlyStem,
        hidden_stems: Dict[HeavenlyStem, float],
    ) -> Tuple[ShiShen, Dict[ShiShen, float]]:
        """
        Calculate ShiShen for a pillar's stem and hidden stems.

        Args:
            day_master: The Day Master stem
            stem: The pillar's heavenly stem
            hidden_stems: The hidden stems with their ratios

        Returns:
            Tuple of (stem_shishen, {hidden_shishen: ratio})
        """
        stem_shishen = self.calculate(day_master, stem)

        hidden_shishen: Dict[ShiShen, float] = {}
        for hidden_stem, ratio in hidden_stems.items():
            ss = self.calculate(day_master, hidden_stem)
            # Accumulate if same ShiShen appears multiple times
            hidden_shishen[ss] = hidden_shishen.get(ss, 0) + ratio

        return (stem_shishen, hidden_shishen)

    def _get_main_hidden_shishen(
        self,
        day_master: HeavenlyStem,
        hidden_stems: Dict[HeavenlyStem, float],
    ) -> ShiShen:
        """Get ShiShen for the dominant hidden stem in a branch."""
        main_hidden = max(hidden_stems.keys(), key=lambda k: hidden_stems[k])
        return self.calculate(day_master, main_hidden)

    def calculate_for_bazi(self, bazi: BaZi) -> ShiShenChart:
        """
        Calculate the complete ShiShen chart for a BaZi.

        Args:
            bazi: The BaZi chart to analyze

        Returns:
            ShiShenChart with all positions' ShiShen values
        """
        dm = bazi.day_master

        return ShiShenChart(
            year_stem=self.calculate(dm, bazi.year_pillar.stem),
            year_branch_main=self._get_main_hidden_shishen(dm, bazi.year_pillar.hidden_stems),
            month_stem=self.calculate(dm, bazi.month_pillar.stem),
            month_branch_main=self._get_main_hidden_shishen(dm, bazi.month_pillar.hidden_stems),
            day_branch_main=self._get_main_hidden_shishen(dm, bazi.day_pillar.hidden_stems),
            hour_stem=self.calculate(dm, bazi.hour_pillar.stem),
            hour_branch_main=self._get_main_hidden_shishen(dm, bazi.hour_pillar.hidden_stems),
        )

    def get_detailed_shishen(
        self,
        bazi: BaZi
    ) -> List[Tuple[Optional[ShiShen], Dict[ShiShen, float]]]:
        """
        获取每柱的详细十神信息，包括所有藏干。
        Get detailed ShiShen for each pillar including all hidden stems.

        日柱天干即日主本身，故 stem_shishen 为 None。
        Day pillar stem IS the Day Master, so stem_shishen is None.

        Returns:
            List of (stem_shishen, {hidden_shishen: ratio}) for each pillar.
            Order: [year, month, day, hour]
        """
        day_master = bazi.day_master
        result: List[Tuple[Optional[ShiShen], Dict[ShiShen, float]]] = []

        for pillar in bazi.pillars:
            # 藏干十神计算对所有柱相同
            # Hidden stem ShiShen calculation is the same for all pillars
            _, hidden_ss = self.calculate_for_pillar(
                day_master, pillar.stem, pillar.hidden_stems
            )

            # 日柱天干即日主，无需计算十神
            # Day pillar stem is the Day Master itself - no ShiShen to calculate
            if pillar is bazi.day_pillar:
                result.append((None, hidden_ss))
            else:
                stem_ss = self.calculate(day_master, pillar.stem)
                result.append((stem_ss, hidden_ss))

        return result

    def count_shishen(self, bazi: BaZi) -> Dict[ShiShen, int]:
        """
        Count occurrences of each ShiShen in the chart.

        Only counts stems (not weighted by hidden stem ratios).
        """
        chart = self.calculate_for_bazi(bazi)
        return chart.count()

    def find_positions(self, bazi: BaZi, target: ShiShen) -> List[str]:
        """
        Find all positions where a specific ShiShen appears.

        Args:
            bazi: The BaZi chart
            target: The ShiShen to find

        Returns:
            List of position names (e.g., ["year_stem", "hour_branch"])
        """
        chart = self.calculate_for_bazi(bazi)
        positions = []

        if chart.year_stem == target:
            positions.append("year_stem")
        if chart.year_branch_main == target:
            positions.append("year_branch")
        if chart.month_stem == target:
            positions.append("month_stem")
        if chart.month_branch_main == target:
            positions.append("month_branch")
        if chart.day_branch_main == target:
            positions.append("day_branch")
        if chart.hour_stem == target:
            positions.append("hour_stem")
        if chart.hour_branch_main == target:
            positions.append("hour_branch")

        return positions
