"""
ShiShen (Ten Gods) calculation service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

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
    ) -> List[Tuple[ShiShen, Dict[ShiShen, float]]]:
        """
        Get detailed ShiShen for each pillar including all hidden stems.

        Returns:
            List of (stem_shishen, {hidden_shishen: ratio}) for each pillar
        """
        day_master = bazi.day_master
        result = []

        for i, pillar in enumerate(bazi.pillars):
            if i == 2:  # Day pillar - stem is self
                # For day pillar, stem is 日主 (self), only calculate hidden
                hidden_ss: Dict[ShiShen, float] = {}
                for hidden_stem, ratio in pillar.hidden_stems.items():
                    ss = self.calculate(day_master, hidden_stem)
                    hidden_ss[ss] = hidden_ss.get(ss, 0) + ratio
                result.append((None, hidden_ss))  # type: ignore
            else:
                stem_ss, hidden_ss = self.calculate_for_pillar(
                    day_master, pillar.stem, pillar.hidden_stems
                )
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
