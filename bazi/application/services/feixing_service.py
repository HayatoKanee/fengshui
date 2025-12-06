"""
FeiXing Application Service.

Application service that orchestrates Flying Star calculations
and transforms results for presentation layer consumption.
"""
from __future__ import annotations

from typing import Dict, List

from bazi.domain.feixing import FeiXingCalculator


class FeiXingService:
    """
    Application service for Flying Star Feng Shui analysis.

    This service acts as the interface between the presentation layer
    and the domain layer, orchestrating calculations and preparing
    data for views.
    """

    def __init__(self, calculator: FeiXingCalculator | None = None):
        """
        Initialize the service with an optional calculator.

        Args:
            calculator: FeiXingCalculator instance (creates default if not provided)
        """
        self._calculator = calculator or FeiXingCalculator()

    def generate_flying_star_charts(self, center: int) -> List[Dict]:
        """
        Generate Flying Star charts for all 24 mountain directions.

        Args:
            center: The center star number (1-9)

        Returns:
            List of chart configurations for each mountain direction,
            with identical configurations merged
        """
        if not (1 <= center <= 9):
            center = 9  # Default to 9 if invalid

        return self._calculator.calculate_all_charts(center)

    def get_chart_for_mountain(self, center: int, mountain_name: str) -> Dict:
        """
        Generate a Flying Star chart for a specific mountain direction.

        Args:
            center: The center star number (1-9)
            mountain_name: One of the 24 mountain directions

        Returns:
            Chart configuration for the specified mountain
        """
        return self._calculator.calculate_flying_star_chart(center, mountain_name)
