"""
Day Master (日主) strength analysis service.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

from ..models import (
    WuXing,
    BaZi,
    DayMasterStrength,
    FavorableElements,
    WuXingStrength,
)
from .wuxing_calculator import WuXingCalculator

if TYPE_CHECKING:
    from .integrated_yongshen_analyzer import (
        IntegratedYongShenAnalyzer,
        IntegratedYongShenResult,
    )


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
        use_integrated: bool = False,
    ) -> tuple[DayMasterStrength, FavorableElements, WuXingStrength]:
        """
        Perform complete Day Master analysis.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period
            use_integrated: Whether to use integrated 扶抑+调候 method

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

        if use_integrated:
            favorable = self.determine_favorable_elements_integrated(bazi, dm_strength)
        else:
            favorable = self.determine_favorable_elements(bazi, dm_strength)

        return (dm_strength, favorable, wuxing_strength)

    def determine_favorable_elements_integrated(
        self,
        bazi: BaZi,
        strength: DayMasterStrength,
    ) -> FavorableElements:
        """
        Determine favorable elements using integrated 扶抑+调候 method.

        This modern approach combines:
        - 扶抑用神: Based on day master strength (strong/weak)
        - 调候用神: Based on season (climate adjustment from《穷通宝鉴》)

        Weighting:
        - Extreme seasons (子丑午未): 扶抑 40% + 调候 60%
        - Moderate seasons: 扶抑 70% + 调候 30%

        Args:
            bazi: The BaZi chart
            strength: The Day Master strength analysis

        Returns:
            FavorableElements with integrated analysis
        """
        from .integrated_yongshen_analyzer import IntegratedYongShenAnalyzer

        analyzer = IntegratedYongShenAnalyzer()
        result = analyzer.analyze(bazi, strength)
        return analyzer.to_favorable_elements(result)

    def full_analysis_integrated(
        self,
        bazi: BaZi,
        is_earth_dominant: bool = False,
    ) -> tuple[DayMasterStrength, FavorableElements, WuXingStrength, "IntegratedYongShenResult"]:
        """
        Perform complete Day Master analysis with integrated 用神 method.

        This returns additional detailed scoring information from the
        integrated 扶抑+调候 analysis.

        Args:
            bazi: The BaZi chart to analyze
            is_earth_dominant: Whether we're in earth-dominant period

        Returns:
            Tuple of (strength, favorable_elements, wuxing_strength, integrated_result)
        """
        from .integrated_yongshen_analyzer import IntegratedYongShenAnalyzer

        wuxing_strength = self._wuxing_calc.calculate_strength(bazi, is_earth_dominant)

        beneficial, harmful = self.calculate_shenghao(
            wuxing_strength.adjusted_values,
            bazi.day_master_wuxing,
        )

        dm_strength = DayMasterStrength(
            beneficial_value=beneficial,
            harmful_value=harmful,
        )

        # Use integrated analyzer
        integrated_analyzer = IntegratedYongShenAnalyzer()
        integrated_result = integrated_analyzer.analyze(bazi, dm_strength)
        favorable = integrated_analyzer.to_favorable_elements(integrated_result)

        return (dm_strength, favorable, wuxing_strength, integrated_result)
