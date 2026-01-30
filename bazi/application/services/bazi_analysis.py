"""
BaZi Analysis Application Service.

Orchestrates the complete BaZi analysis workflow by coordinating
domain services and infrastructure adapters.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

from bazi.domain.models import (
    BaZi,
    BirthData,
    WuXing,
    ShiShenChart,
    WuXingStrength,
    DayMasterStrength,
    FavorableElements,
)
from bazi.domain.services import (
    WuXingCalculator,
    ShiShenCalculator,
    DayMasterAnalyzer,
    ShenShaCalculator,
)

if TYPE_CHECKING:
    from bazi.domain.ports import LunarPort
    from bazi.domain.models import ShenShaAnalysis


@dataclass
class BaziAnalysisResult:
    """
    Complete BaZi analysis result.

    This is a comprehensive DTO containing all analysis data
    that the presentation layer needs to render the BaZi view.
    """

    # Core BaZi data
    bazi: BaZi
    birth_data: BirthData

    # Element analysis
    wuxing_strength: WuXingStrength
    day_master_strength: DayMasterStrength
    favorable_elements: FavorableElements

    # ShiShen analysis
    shishen_chart: ShiShenChart

    # ShenSha analysis
    shensha_analysis: ShenShaAnalysis

    # Lunar calendar info
    shengxiao: str  # Chinese zodiac animal
    is_earth_dominant: bool  # 土旺 period

    @property
    def is_day_master_strong(self) -> bool:
        """Whether the day master is strong."""
        return self.day_master_strength.is_strong

    @property
    def day_master_wuxing(self) -> WuXing:
        """The day master's WuXing element."""
        return self.bazi.day_master_wuxing

    @property
    def beneficial_percentage(self) -> float:
        """Percentage of beneficial element strength."""
        return self.day_master_strength.beneficial_percentage

    @property
    def harmful_percentage(self) -> float:
        """Percentage of harmful element strength."""
        return self.day_master_strength.harmful_percentage


class BaziAnalysisService:
    """
    Application service for BaZi analysis.

    This service orchestrates the complete BaZi analysis workflow:
    1. Calculate BaZi from birth data
    2. Analyze WuXing element strengths
    3. Determine day master strength
    4. Calculate favorable/unfavorable elements
    5. Generate ShiShen chart
    6. Calculate ShenSha (auxiliary stars)

    Usage:
        service = BaziAnalysisService(lunar_adapter)
        result = service.analyze(birth_data)
        # Use result.bazi, result.day_master_strength, etc.
    """

    def __init__(
        self,
        lunar_adapter: LunarPort,
        wuxing_calculator: Optional[WuXingCalculator] = None,
        shishen_calculator: Optional[ShiShenCalculator] = None,
        day_master_analyzer: Optional[DayMasterAnalyzer] = None,
        shensha_calculator: Optional[ShenShaCalculator] = None,
    ):
        """
        Initialize the service with required adapters and calculators.

        Args:
            lunar_adapter: Adapter for lunar calendar calculations
            wuxing_calculator: Calculator for WuXing strengths (optional, created if not provided)
            shishen_calculator: Calculator for ShiShen relationships (optional)
            day_master_analyzer: Analyzer for day master strength (optional)
            shensha_calculator: Calculator for ShenSha stars (optional)
        """
        self._lunar = lunar_adapter
        self._wuxing_calc = wuxing_calculator or WuXingCalculator()
        self._shishen_calc = shishen_calculator or ShiShenCalculator()
        self._day_master = day_master_analyzer or DayMasterAnalyzer()
        self._shensha_calc = shensha_calculator or ShenShaCalculator()

    def analyze(self, birth_data: BirthData) -> BaziAnalysisResult:
        """
        Perform complete BaZi analysis for given birth data.

        Args:
            birth_data: Birth date/time information

        Returns:
            BaziAnalysisResult containing all analysis data
        """
        # Step 1: Calculate BaZi from birth data
        bazi = self._lunar.get_bazi(birth_data)

        # Step 2: Check if in earth-dominant period
        is_earth_dominant = self._lunar.is_earth_dominant_period(
            birth_data.year,
            birth_data.month,
            birth_data.day,
        )

        # Step 3: Full day master analysis (includes WuXing strength)
        dm_strength, favorable, wuxing_strength = self._day_master.full_analysis(
            bazi, is_earth_dominant
        )

        # Step 4: Calculate ShiShen chart
        shishen_chart = self._shishen_calc.calculate_for_bazi(bazi)

        # Step 5: Calculate ShenSha
        shensha_analysis = self._shensha_calc.calculate_for_bazi(bazi)

        # Step 6: Get Chinese zodiac animal (生肖)
        shengxiao = self._lunar.get_shengxiao(
            birth_data.year,
            birth_data.month,
            birth_data.day,
        )

        return BaziAnalysisResult(
            bazi=bazi,
            birth_data=birth_data,
            wuxing_strength=wuxing_strength,
            day_master_strength=dm_strength,
            favorable_elements=favorable,
            shishen_chart=shishen_chart,
            shensha_analysis=shensha_analysis,
            shengxiao=shengxiao,
            is_earth_dominant=is_earth_dominant,
        )

    def analyze_for_year(
        self,
        birth_data: BirthData,
        year: int,
    ) -> Dict:
        """
        Analyze BaZi with yearly (LiuNian) context.

        Args:
            birth_data: Birth date/time information
            year: The year to analyze for (流年)

        Returns:
            Dictionary with base analysis plus yearly analysis
        """
        base_result = self.analyze(birth_data)

        # Get the year's BaZi (just year pillar matters for LiuNian)
        year_bazi = self._lunar.get_bazi_from_datetime(
            __import__('datetime').datetime(year, 6, 15, 12, 0, 0)
        )

        # Calculate ShiShen relationship between LiuNian and day master
        year_stem_shishen = self._shishen_calc.calculate(
            base_result.bazi.day_master,
            year_bazi.year_pillar.stem,
        )

        return {
            "base": base_result,
            "year": year,
            "year_pillar": year_bazi.year_pillar,
            "year_stem_shishen": year_stem_shishen,
        }

    def get_quick_summary(self, birth_data: BirthData) -> Dict:
        """
        Get a quick summary of BaZi analysis (less detailed).

        Useful for calendar views or profile cards where full
        analysis is not needed.

        Args:
            birth_data: Birth date/time information

        Returns:
            Dictionary with key BaZi information
        """
        bazi = self._lunar.get_bazi(birth_data)
        is_earth_dominant = self._lunar.is_earth_dominant_period(
            birth_data.year,
            birth_data.month,
            birth_data.day,
        )

        dm_strength, favorable, _ = self._day_master.full_analysis(
            bazi, is_earth_dominant
        )

        return {
            "bazi_chinese": bazi.chinese,
            "day_master": bazi.day_master.chinese,
            "day_master_wuxing": bazi.day_master_wuxing.value,
            "is_strong": dm_strength.is_strong,
            "favorable_wuxing": [e.value for e in favorable.favorable],
            "unfavorable_wuxing": [e.value for e in favorable.unfavorable],
        }
