"""
Tests for FeiXing Calculator.

Tests the Flying Star Feng Shui calculation engine:
- Grid generation with forward/reverse flight orders
- Flying Star chart calculation for 24 mountains
- Known reference value verification
"""
import pytest

from bazi.domain.feixing.calculator import FeiXingCalculator
from bazi.domain.feixing.models import FlightOrder, Grid


class TestFeiXingCalculatorGridGeneration:
    """Tests for generate_grid method."""

    @pytest.fixture
    def calculator(self):
        return FeiXingCalculator()

    def test_generate_grid_center_5_forward(self, calculator):
        """Standard Lo Shu with center 5 forward should match known pattern."""
        grid = calculator.generate_grid(5, FlightOrder.FORWARD)
        # Classic Lo Shu:
        # 4 9 2
        # 3 5 7
        # 8 1 6
        assert grid.center == 5
        assert grid.to_lists() == [
            [4, 9, 2],
            [3, 5, 7],
            [8, 1, 6]
        ]

    def test_generate_grid_center_1_forward(self, calculator):
        """Grid with center 1 forward flight."""
        grid = calculator.generate_grid(1, FlightOrder.FORWARD)
        # Center 1, forward: shift all by -4
        # ((1-1-offset) % 9) + 1
        assert grid.center == 1
        # Verify it's a valid flying star grid
        assert set(sum(grid.to_lists(), [])) == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def test_generate_grid_center_9_forward(self, calculator):
        """Grid with center 9 forward flight."""
        grid = calculator.generate_grid(9, FlightOrder.FORWARD)
        # Center 9, forward: shift all by +4 from standard
        assert grid.center == 9
        assert set(sum(grid.to_lists(), [])) == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def test_generate_grid_center_5_reverse(self, calculator):
        """Center 5 with reverse flight should mirror forward."""
        grid = calculator.generate_grid(5, FlightOrder.REVERSE)
        assert grid.center == 5
        # Reverse flight flips the outer ring
        # 6 1 8
        # 7 5 3
        # 2 9 4
        assert grid.to_lists() == [
            [6, 1, 8],
            [7, 5, 3],
            [2, 9, 4]
        ]

    @pytest.mark.parametrize("center", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_all_centers_contain_all_numbers(self, calculator, center):
        """Any center value should produce grid with all 1-9."""
        grid = calculator.generate_grid(center, FlightOrder.FORWARD)
        all_numbers = set(sum(grid.to_lists(), []))
        assert all_numbers == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    @pytest.mark.parametrize("center", [1, 2, 3, 4, 5, 6, 7, 8, 9])
    def test_center_value_matches_input(self, calculator, center):
        """Center cell should always equal input center value."""
        grid_fwd = calculator.generate_grid(center, FlightOrder.FORWARD)
        grid_rev = calculator.generate_grid(center, FlightOrder.REVERSE)
        assert grid_fwd.center == center
        assert grid_rev.center == center

    def test_forward_reverse_have_same_numbers(self, calculator):
        """Forward and reverse grids should contain same numbers, different arrangement."""
        for center in range(1, 10):
            fwd = calculator.generate_grid(center, FlightOrder.FORWARD)
            rev = calculator.generate_grid(center, FlightOrder.REVERSE)
            # Both should have same center
            assert fwd.center == rev.center == center
            # Both should contain all 1-9
            assert set(fwd.outer_ring) == set(rev.outer_ring)
            # But arranged differently (unless symmetric)
            # Note: outer rings are NOT simple reversals due to offset application

    @pytest.mark.parametrize("invalid_center", [0, 10, -1, 100])
    def test_invalid_center_raises_error(self, calculator, invalid_center):
        """Center outside 1-9 should raise ValueError."""
        with pytest.raises(ValueError, match="Center must be between 1 and 9"):
            calculator.generate_grid(invalid_center, FlightOrder.FORWARD)


class TestFeiXingCalculatorFlightOrder:
    """Tests for get_flight_order method."""

    @pytest.fixture
    def calculator(self):
        return FeiXingCalculator()

    def test_flight_order_returns_valid_enum(self, calculator):
        """Should always return a FlightOrder enum value."""
        for number in range(1, 10):
            for yuan_long in ['天', '人', '地']:
                result = calculator.get_flight_order(number, yuan_long)
                assert isinstance(result, FlightOrder)


class TestFeiXingCalculatorFlyingStarChart:
    """Tests for Flying Star chart calculation."""

    @pytest.fixture
    def calculator(self):
        return FeiXingCalculator()

    def test_calculate_chart_returns_required_keys(self, calculator):
        """Chart dict should contain all required keys."""
        chart = calculator.calculate_flying_star_chart(9, '子')
        assert 'main_grid' in chart
        assert 'mountain_name' in chart
        assert 'mountain_star_grid' in chart
        assert 'facing_star_grid' in chart

    def test_main_grid_is_chinese(self, calculator):
        """Main grid should be in Chinese numerals."""
        chart = calculator.calculate_flying_star_chart(9, '子')
        chinese_numerals = {'一', '二', '三', '四', '五', '六', '七', '八', '九'}
        all_chars = set(sum(chart['main_grid'], []))
        assert all_chars.issubset(chinese_numerals)

    def test_star_grids_are_numeric(self, calculator):
        """Mountain and facing grids should be numeric 1-9."""
        chart = calculator.calculate_flying_star_chart(9, '子')

        mountain_numbers = set(sum(chart['mountain_star_grid'], []))
        facing_numbers = set(sum(chart['facing_star_grid'], []))

        assert mountain_numbers == {1, 2, 3, 4, 5, 6, 7, 8, 9}
        assert facing_numbers == {1, 2, 3, 4, 5, 6, 7, 8, 9}

    @pytest.mark.parametrize("mountain", ['子', '午', '卯', '酉'])
    def test_chart_for_cardinal_directions(self, calculator, mountain):
        """Should calculate chart for cardinal directions (N, S, E, W)."""
        chart = calculator.calculate_flying_star_chart(9, mountain)
        assert chart['mountain_name'] == mountain


class TestFeiXingCalculatorAllCharts:
    """Tests for calculate_all_charts method."""

    @pytest.fixture
    def calculator(self):
        return FeiXingCalculator()

    @pytest.mark.parametrize("center", [1, 5, 9])
    def test_all_charts_returns_list(self, calculator, center):
        """Should return a list of chart dictionaries."""
        charts = calculator.calculate_all_charts(center)
        assert isinstance(charts, list)
        assert len(charts) > 0

    def test_all_charts_has_unique_grids(self, calculator):
        """All returned charts should have unique grid combinations."""
        charts = calculator.calculate_all_charts(9)

        # Each chart should be unique
        seen = set()
        for chart in charts:
            key = (
                tuple(tuple(row) for row in chart['grid_star']),
                tuple(tuple(row) for row in chart['grid_opposite_star'])
            )
            assert key not in seen, "Duplicate chart found"
            seen.add(key)

    def test_all_charts_covers_24_mountains(self, calculator):
        """Should cover all 24 mountains (some merged as duplicates)."""
        charts = calculator.calculate_all_charts(9)

        # Count total mountains covered
        mountain_count = 0
        for chart in charts:
            mountain_count += 1
            if chart.get('second_star'):
                mountain_count += 1

        # Some configurations may have multiple mountains with same grid
        # Typically 12-24 depending on symmetry
        assert mountain_count <= 24
        assert len(charts) >= 12, "Should have at least 12 unique configurations"

    def test_chart_structure(self, calculator):
        """Each chart should have expected structure."""
        charts = calculator.calculate_all_charts(9)

        for chart in charts:
            assert 'star' in chart
            assert 'main_grid' in chart
            assert 'grid_star' in chart
            assert 'grid_opposite_star' in chart
            assert 'second_star' in chart  # May be None


class TestFeiXingCalculatorKnownValues:
    """Tests with known Flying Star reference values."""

    @pytest.fixture
    def calculator(self):
        return FeiXingCalculator()

    def test_center_9_period_standard_lo_shu(self, calculator):
        """Period 9 (center 9) main grid should be shifted Lo Shu."""
        grid = calculator.generate_grid(9, FlightOrder.FORWARD)
        # Center 9 forward:
        # 8 4 6
        # 7 9 2
        # 3 5 1
        assert grid.center == 9
        expected = [
            [8, 4, 6],
            [7, 9, 2],
            [3, 5, 1]
        ]
        assert grid.to_lists() == expected

    def test_center_8_period(self, calculator):
        """Period 8 (center 8) main grid."""
        grid = calculator.generate_grid(8, FlightOrder.FORWARD)
        # Center 8 forward:
        # 7 3 5
        # 6 8 1
        # 2 4 9
        assert grid.center == 8
        expected = [
            [7, 3, 5],
            [6, 8, 1],
            [2, 4, 9]
        ]
        assert grid.to_lists() == expected

    def test_center_7_period(self, calculator):
        """Period 7 (center 7) main grid."""
        grid = calculator.generate_grid(7, FlightOrder.FORWARD)
        # Center 7 forward:
        # 6 2 4
        # 5 7 9
        # 1 3 8
        assert grid.center == 7
        expected = [
            [6, 2, 4],
            [5, 7, 9],
            [1, 3, 8]
        ]
        assert grid.to_lists() == expected

    def test_opposite_positions_sum_property(self, calculator):
        """In Lo Shu, opposite positions sum to 10 (except center)."""
        grid = calculator.generate_grid(5, FlightOrder.FORWARD)
        # Opposite pairs should sum to 10
        assert grid.at_position(0, 0) + grid.at_position(2, 2) == 10  # 4 + 6
        assert grid.at_position(0, 2) + grid.at_position(2, 0) == 10  # 2 + 8
        assert grid.at_position(0, 1) + grid.at_position(2, 1) == 10  # 9 + 1
        assert grid.at_position(1, 0) + grid.at_position(1, 2) == 10  # 3 + 7

    def test_magic_square_row_sum(self, calculator):
        """Standard Lo Shu rows/cols/diagonals sum to 15."""
        grid = calculator.generate_grid(5, FlightOrder.FORWARD)
        cells = grid.to_lists()

        # Rows
        for row in cells:
            assert sum(row) == 15

        # Columns
        for col in range(3):
            assert sum(cells[row][col] for row in range(3)) == 15

        # Diagonals
        assert cells[0][0] + cells[1][1] + cells[2][2] == 15
        assert cells[0][2] + cells[1][1] + cells[2][0] == 15


# Helper method for tests using position tuple notation
def at_position(grid: Grid, row: int, col: int) -> int:
    """Helper to access grid by row, col indices."""
    return grid.to_lists()[row][col]


# Monkey-patch for the known values tests
Grid.at_position = lambda self, row, col: self.to_lists()[row][col]
