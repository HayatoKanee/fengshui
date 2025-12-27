"""
Tests for FeiXing Domain Models.

Tests the value objects used in Flying Star Feng Shui calculations:
- Position: Grid coordinates with validation and opposite calculation
- Grid: 3x3 Lo Shu grid with rotation operations
- Mountain: 24 mountain compass directions
- FlightOrder: Forward/Reverse star movement
"""
import pytest

from bazi.domain.feixing.models import FlightOrder, Grid, Mountain, Position


class TestFlightOrder:
    """Tests for FlightOrder enum."""

    def test_forward_value(self):
        """FORWARD should have value 'f' for 顺飞."""
        assert FlightOrder.FORWARD.value == 'f'

    def test_reverse_value(self):
        """REVERSE should have value 'r' for 逆飞."""
        assert FlightOrder.REVERSE.value == 'r'


class TestPosition:
    """Tests for Position value object."""

    def test_valid_position_creation(self):
        """Should create position with valid coordinates."""
        pos = Position(0, 0)
        assert pos.row == 0
        assert pos.col == 0

    def test_center_position(self):
        """Center position should be (1, 1)."""
        pos = Position(1, 1)
        assert pos.is_center is True

    def test_non_center_positions(self):
        """Non-center positions should report is_center as False."""
        for row in range(3):
            for col in range(3):
                if row != 1 or col != 1:
                    pos = Position(row, col)
                    assert pos.is_center is False, f"({row}, {col}) should not be center"

    @pytest.mark.parametrize("row,col,expected_row,expected_col", [
        (0, 0, 2, 2),  # Top-left ↔ Bottom-right
        (0, 1, 2, 1),  # Top-center ↔ Bottom-center
        (0, 2, 2, 0),  # Top-right ↔ Bottom-left
        (1, 0, 1, 2),  # Middle-left ↔ Middle-right
        (1, 1, 1, 1),  # Center ↔ Center
        (1, 2, 1, 0),  # Middle-right ↔ Middle-left
        (2, 0, 0, 2),  # Bottom-left ↔ Top-right
        (2, 1, 0, 1),  # Bottom-center ↔ Top-center
        (2, 2, 0, 0),  # Bottom-right ↔ Top-left
    ])
    def test_opposite_position(self, row, col, expected_row, expected_col):
        """Opposite should mirror across center (formula: 2-row, 2-col)."""
        pos = Position(row, col)
        opp = pos.opposite
        assert opp.row == expected_row
        assert opp.col == expected_col

    def test_opposite_is_involution(self):
        """Taking opposite twice should return original position."""
        pos = Position(0, 2)
        assert pos.opposite.opposite == pos

    def test_to_tuple(self):
        """Should convert to tuple for compatibility."""
        pos = Position(1, 2)
        assert pos.to_tuple() == (1, 2)

    @pytest.mark.parametrize("row,col", [
        (-1, 0), (0, -1), (3, 0), (0, 3), (3, 3), (-1, -1)
    ])
    def test_invalid_position_raises_error(self, row, col):
        """Should raise ValueError for out-of-bounds coordinates."""
        with pytest.raises(ValueError, match="Position must be within 3x3 grid"):
            Position(row, col)

    def test_position_is_frozen(self):
        """Position should be immutable (frozen dataclass)."""
        pos = Position(0, 0)
        with pytest.raises(AttributeError):
            pos.row = 1


class TestGrid:
    """Tests for Grid value object."""

    def test_standard_lo_shu_center_5(self):
        """Standard Lo Shu magic square with center 5."""
        # The classic Lo Shu:
        # 4 9 2
        # 3 5 7
        # 8 1 6
        lo_shu = Grid.from_lists([
            [4, 9, 2],
            [3, 5, 7],
            [8, 1, 6]
        ])
        assert lo_shu.center == 5
        assert lo_shu.at(Position(0, 0)) == 4
        assert lo_shu.at(Position(1, 1)) == 5
        assert lo_shu.at(Position(2, 2)) == 6

    def test_from_lists_to_lists_roundtrip(self):
        """Converting to/from lists should preserve data."""
        original = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        grid = Grid.from_lists(original)
        result = grid.to_lists()
        assert result == original

    def test_center_property(self):
        """Center should return the middle cell value."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 9, 6],
            [7, 8, 5]
        ])
        assert grid.center == 9

    def test_at_all_positions(self):
        """at() should return correct values for all positions."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        for row in range(3):
            for col in range(3):
                expected = row * 3 + col + 1
                assert grid.at(Position(row, col)) == expected

    def test_outer_ring_clockwise_order(self):
        """outer_ring should return values in clockwise order from top-left."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        # Clockwise from top-left: 1→2→3→6→9→8→7→4
        assert grid.outer_ring == [1, 2, 3, 6, 9, 8, 7, 4]

    def test_rotate_outer_zero_steps(self):
        """Rotating by 0 steps should return same grid."""
        original = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        grid = Grid.from_lists(original)
        rotated = grid.rotate_outer(0)
        assert rotated.to_lists() == original

    def test_rotate_outer_one_step(self):
        """Rotating by 1 step clockwise."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        # Outer ring [1,2,3,6,9,8,7,4] rotated 1 step → [4,1,2,3,6,9,8,7]
        # New grid:
        # 4 1 2
        # 7 5 3
        # 8 9 6
        rotated = grid.rotate_outer(1)
        assert rotated.to_lists() == [
            [4, 1, 2],
            [7, 5, 3],
            [8, 9, 6]
        ]

    def test_rotate_outer_preserves_center(self):
        """Rotation should never change center value."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        for steps in range(1, 9):
            rotated = grid.rotate_outer(steps)
            assert rotated.center == 5, f"Center changed after {steps} rotation steps"

    def test_rotate_outer_8_steps_returns_original(self):
        """8 steps (full rotation) should return to original."""
        original = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        grid = Grid.from_lists(original)
        rotated = grid.rotate_outer(8)
        assert rotated.to_lists() == original

    def test_rotate_outer_modulo(self):
        """Steps beyond 8 should wrap around."""
        grid = Grid.from_lists([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        assert grid.rotate_outer(9).to_lists() == grid.rotate_outer(1).to_lists()
        assert grid.rotate_outer(16).to_lists() == grid.to_lists()

    def test_get_shift_to_position(self):
        """Calculate steps to move digit to target position."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        # Outer ring: [1,2,3,6,9,8,7,4] indices 0-7
        # To move 1 (index 0) to index 5 (bottom-center): 5 - 0 = 5 steps
        assert grid.get_shift_to_position(1, target_index=5) == 5
        # To move 9 (index 4) to index 5: 5 - 4 = 1 step
        assert grid.get_shift_to_position(9, target_index=5) == 1

    def test_to_chinese(self):
        """Should convert numbers to Chinese numerals."""
        grid = Grid.from_lists([
            [1, 2, 3],
            [4, 5, 6],
            [7, 8, 9]
        ])
        chinese = grid.to_chinese()
        assert chinese[1][1] == '五'  # Center should be 五
        # First row should be 一 二 三
        assert chinese[0] == ['一', '二', '三']

    def test_invalid_grid_wrong_rows(self):
        """Should raise error for grids without 3 rows."""
        with pytest.raises(ValueError, match="Grid must have 3 rows"):
            Grid(((1, 2, 3), (4, 5, 6)))

    def test_invalid_grid_wrong_cols(self):
        """Should raise error for rows without 3 columns."""
        with pytest.raises(ValueError, match="Grid must have 3 columns"):
            Grid(((1, 2), (3, 4), (5, 6)))

    def test_grid_is_frozen(self):
        """Grid should be immutable (frozen dataclass)."""
        grid = Grid.from_lists([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        with pytest.raises(AttributeError):
            grid.cells = ((0, 0, 0), (0, 0, 0), (0, 0, 0))


class TestMountain:
    """Tests for Mountain value object."""

    def test_from_name_valid_mountain(self):
        """Should create Mountain from valid Chinese name."""
        mountain = Mountain.from_name('子')
        assert mountain.name == '子'
        assert isinstance(mountain.position, Position)
        assert mountain.yuan_long in ('天', '人', '地')
        assert isinstance(mountain.flight_order, FlightOrder)

    def test_from_name_invalid_raises_error(self):
        """Should raise ValueError for unknown mountain name."""
        with pytest.raises(ValueError, match="Unknown mountain name"):
            Mountain.from_name('无效')

    @pytest.mark.parametrize("mountain_name", [
        '子', '癸', '丑', '艮', '寅', '甲',  # North-East
        '卯', '乙', '辰', '巽', '巳', '丙',  # East-South
        '午', '丁', '未', '坤', '申', '庚',  # South-West
        '酉', '辛', '戌', '乾', '亥', '壬',  # West-North
    ])
    def test_all_24_mountains_valid(self, mountain_name):
        """All 24 mountains should be creatable."""
        mountain = Mountain.from_name(mountain_name)
        assert mountain.name == mountain_name

    def test_mountain_is_frozen(self):
        """Mountain should be immutable."""
        mountain = Mountain.from_name('子')
        with pytest.raises(AttributeError):
            mountain.name = '午'
