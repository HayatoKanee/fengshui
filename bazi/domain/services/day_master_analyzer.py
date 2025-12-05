"""
Day Master (日主) strength analysis service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict

from ..models import (
    WuXing,
    BaZi,
    DayMasterStrength,
    FavorableElements,
    WuXingStrength,
)
from .wuxing_calculator import WuXingCalculator


class DayMasterAnalyzer:
    """
    Analyzer for Day Master strength and favorable elements.

    Determines whether the Day Master is strong or weak,
    and calculates the favorable (用神) and unfavorable (忌神) elements.
    """

    def __init__(self, wuxing_calculator: WuXingCalculator | None = None):
        self._wuxing_calc = wuxing_calculator or WuXingCalculator()

    def calculate_shenghao(
        self,
        wuxing_values: Dict[WuXing, float],
        day_master_element: WuXing,
    ) -> tuple[float, float]:
        """
        Calculate beneficial (生扶) and harmful (耗泄克) values.

        Args:
            wuxing_values: Accumulated WuXing values from the chart
            day_master_element: The Day Master's WuXing element

        Returns:
            Tuple of (beneficial_value, harmful_value)
        """
        beneficial = day_master_element.beneficial
        harmful = day_master_element.harmful

        beneficial_value = sum(
            wuxing_values.get(element, 0) for element in beneficial
        )
        harmful_value = sum(
            wuxing_values.get(element, 0) for element in harmful
        )

        return (beneficial_value, harmful_value)

    def analyze_strength(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False,
    ) -> DayMasterStrength:
        """
        Analyze the Day Master's strength.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            DayMasterStrength with beneficial/harmful analysis
        """
        # Calculate WuXing strength
        wuxing_strength = self._wuxing_calc.calculate_strength(bazi, is_earth_dominant)

        # Calculate shenghao
        beneficial, harmful = self.calculate_shenghao(
            wuxing_strength.adjusted_values,
            bazi.day_master_wuxing,
        )

        return DayMasterStrength(
            beneficial_value=beneficial,
            harmful_value=harmful,
        )

    def determine_favorable_elements(
        self,
        bazi: BaZi,
        strength: DayMasterStrength,
    ) -> FavorableElements:
        """
        Determine the favorable (用神) and unfavorable (忌神) elements.

        Based on Day Master strength:
        - Strong Day Master: needs elements that drain/control (泄/克)
        - Weak Day Master: needs elements that support/generate (生/扶)

        Args:
            bazi: The BaZi chart
            strength: The Day Master strength analysis

        Returns:
            FavorableElements with yong_shen and ji_shen
        """
        dm_element = bazi.day_master_wuxing

        if strength.is_strong:
            # Strong Day Master - need to drain/control
            # 用神: Element I generate (泄) or element that overcomes me (克)
            yong_shen = dm_element.generates  # 食伤 - drains energy
            xi_shen = dm_element.overcome_by  # 官杀 - controls
            # 忌神: Elements that help me
            ji_shen = dm_element.generated_by  # 印星 - generates me
            chou_shen = dm_element  # 比劫 - same element
        else:
            # Weak Day Master - need support/generation
            # 用神: Element that generates me (印) or same element (比劫)
            yong_shen = dm_element.generated_by  # 印星
            xi_shen = dm_element  # 比劫
            # 忌神: Elements that drain me
            ji_shen = dm_element.generates  # 食伤 - drains
            chou_shen = dm_element.overcomes  # 财星 - I drain to control

        return FavorableElements(
            yong_shen=yong_shen,
            xi_shen=xi_shen,
            ji_shen=ji_shen,
            chou_shen=chou_shen,
        )

    def full_analysis(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False,
    ) -> tuple[DayMasterStrength, FavorableElements, WuXingStrength]:
        """
        Perform complete Day Master analysis.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            Tuple of (strength, favorable_elements, wuxing_strength)
        """
        wuxing_strength = self._wuxing_calc.calculate_strength(bazi, is_earth_dominant)

        beneficial, harmful = self.calculate_shenghao(
            wuxing_strength.adjusted_values,
            bazi.day_master_wuxing,
        )

        dm_strength = DayMasterStrength(
            beneficial_value=beneficial,
            harmful_value=harmful,
        )

        favorable = self.determine_favorable_elements(bazi, dm_strength)

        return (dm_strength, favorable, wuxing_strength)
