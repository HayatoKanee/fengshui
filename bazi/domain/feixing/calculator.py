"""
FeiXing Calculator.

Pure domain logic for Flying Star grid generation and manipulation.
This calculator is stateless and contains no side effects.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .constants import (
    FIXED_POSITIONS,
    FORWARD_OFFSETS,
    GRID_POSITIONS,
    MOUNTAINS_24,
    STAR_TO_FLIGHT,
    YUAN_LONG_MAPPING,
    YUAN_MAP,
)
from .models import FlightOrder, Grid, Mountain, Position


class FeiXingCalculator:
    """
    Calculator for Flying Star Feng Shui grids.

    This is a stateless calculator that performs pure domain calculations
    for Flying Star analysis. All methods are deterministic and side-effect free.
    """

    def generate_grid(self, center: int, order: FlightOrder = FlightOrder.FORWARD) -> Grid:
        """
        Generate a 3×3 Lo Shu grid with the given center number.

        The eight outer cells are computed with fixed offsets using the formula:
            ((center - 1 - offset) % 9) + 1

        Args:
            center: The center number (1-9)
            order: FlightOrder.FORWARD (顺飞) or FlightOrder.REVERSE (逆飞)

        Returns:
            A Grid with the calculated values

        Raises:
            ValueError: If center is not between 1 and 9
        """
        if not (1 <= center <= 9):
            raise ValueError("Center must be between 1 and 9.")

        # Select offsets based on flight order
        if order == FlightOrder.FORWARD:
            offsets = FORWARD_OFFSETS
        else:
            offsets = FORWARD_OFFSETS[::-1]

        # Create grid with center
        cells = [[0 for _ in range(3)] for _ in range(3)]
        cells[1][1] = center

        # Fill outer cells using offsets
        for (r, c), offset in zip(GRID_POSITIONS, offsets):
            cells[r][c] = ((center - 1 - offset) % 9) + 1

        return Grid.from_lists(cells)

    def get_flight_order(self, number: int, yuan_long: str) -> FlightOrder:
        """
        Determine the flight order for a given number and Yuan Long category.

        Args:
            number: The star number (1-9)
            yuan_long: The Yuan Long category (天, 人, or 地)

        Returns:
            The appropriate flight order
        """
        # Find mountains at this number's position
        position = YUAN_MAP.get(number)
        if position is None:
            return FlightOrder.FORWARD

        mountains = self._get_mountains_at_position(position)

        # Find the mountain matching the yuan_long
        for mountain in mountains:
            if YUAN_LONG_MAPPING.get(mountain) == yuan_long:
                flight_char = STAR_TO_FLIGHT.get(mountain, 'f')
                return FlightOrder.FORWARD if flight_char == 'f' else FlightOrder.REVERSE

        return FlightOrder.FORWARD

    def _get_mountains_at_position(self, position: Tuple[int, int]) -> List[str]:
        """Get all mountains at a given grid position."""
        return [
            mountain for mountain, pos in FIXED_POSITIONS.items()
            if pos == position
        ]

    def calculate_flying_star_chart(
        self,
        main_center: int,
        mountain_name: str,
    ) -> Dict:
        """
        Calculate a complete Flying Star chart for a mountain direction.

        Args:
            main_center: The center star for the main period (1-9)
            mountain_name: One of the 24 mountain directions

        Returns:
            Dictionary containing:
            - main_grid: The main Lo Shu grid (Chinese numerals)
            - mountain_name: The mountain direction
            - mountain_star_grid: Mountain star distribution
            - facing_star_grid: Facing star distribution
        """
        position = Position(*FIXED_POSITIONS[mountain_name])
        yuan_long = YUAN_LONG_MAPPING.get(mountain_name, '天')

        # Generate main grid
        main_grid = self.generate_grid(main_center, FlightOrder.FORWARD)

        # Get star centers
        star_center = main_grid.at(position)
        facing_center = main_grid.at(position.opposite)

        # Calculate flight orders and grids
        mountain_grid, facing_grid = self._calculate_star_grids(
            star_center, facing_center, yuan_long
        )

        # Calculate shift to align bottom-center
        shift = main_grid.get_shift_to_position(star_center)

        # Apply rotation to all grids
        main_grid = main_grid.rotate_outer(shift)
        mountain_grid = mountain_grid.rotate_outer(shift)
        facing_grid = facing_grid.rotate_outer(shift)

        return {
            'main_grid': main_grid.to_chinese(),
            'mountain_name': mountain_name,
            'mountain_star_grid': mountain_grid.to_lists(),
            'facing_star_grid': facing_grid.to_lists(),
        }

    def _calculate_star_grids(
        self,
        star_center: int,
        facing_center: int,
        yuan_long: str,
    ) -> Tuple[Grid, Grid]:
        """Calculate mountain and facing star grids."""
        if star_center != 5:
            order_main = self.get_flight_order(star_center, yuan_long)
            order_facing = (
                FlightOrder.REVERSE if order_main == FlightOrder.FORWARD
                else FlightOrder.FORWARD
            )
            mountain_grid = self.generate_grid(star_center, order_main)
            facing_grid = self.generate_grid(facing_center, order_facing)
        else:
            # Special case when star_center is 5
            order_facing = self.get_flight_order(facing_center, yuan_long)
            order_main = (
                FlightOrder.REVERSE if order_facing == FlightOrder.FORWARD
                else FlightOrder.FORWARD
            )
            mountain_grid = self.generate_grid(star_center, order_main)
            facing_grid = self.generate_grid(facing_center, order_facing)

        return mountain_grid, facing_grid

    def calculate_all_charts(self, main_center: int) -> List[Dict]:
        """
        Calculate Flying Star charts for all 24 mountain directions.

        Identical grid configurations are merged with second_star field.

        Args:
            main_center: The center star for the main period (1-9)

        Returns:
            List of chart dictionaries
        """
        charts = []

        for mountain_name in MOUNTAINS_24:
            chart = self.calculate_flying_star_chart(main_center, mountain_name)

            # Check for duplicate grids
            duplicate = self._find_duplicate_chart(
                charts,
                chart['mountain_star_grid'],
                chart['facing_star_grid'],
            )

            if duplicate is not None:
                duplicate['second_star'] = mountain_name
            else:
                chart['star'] = mountain_name
                chart['second_star'] = None
                chart['grid_star'] = chart['mountain_star_grid']
                chart['grid_opposite_star'] = chart['facing_star_grid']
                charts.append(chart)

        return charts

    def _find_duplicate_chart(
        self,
        charts: List[Dict],
        mountain_grid: List[List[int]],
        facing_grid: List[List[int]],
    ) -> Optional[Dict]:
        """Find an existing chart with identical grids."""
        for existing in charts:
            if (existing.get('grid_star') == mountain_grid and
                    existing.get('grid_opposite_star') == facing_grid):
                return existing
        return None
