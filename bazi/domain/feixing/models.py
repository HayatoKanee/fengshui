"""
FeiXing Domain Models.

Value objects for Flying Star Feng Shui calculations.
These are immutable domain objects representing core concepts.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class FlightOrder(Enum):
    """
    Flight order for star movement in the Lo Shu grid.

    FORWARD (顺飞): Stars move in ascending order (clockwise)
    REVERSE (逆飞): Stars move in descending order (counter-clockwise)
    """
    FORWARD = 'f'  # 顺飞 - Yang stars
    REVERSE = 'r'  # 逆飞 - Yin stars


@dataclass(frozen=True)
class Position:
    """
    A position in the 3x3 Lo Shu grid.

    Coordinates are 0-indexed:
    (0,0) (0,1) (0,2)
    (1,0) (1,1) (1,2)  <- (1,1) is center
    (2,0) (2,1) (2,2)
    """
    row: int
    col: int

    def __post_init__(self):
        if not (0 <= self.row <= 2 and 0 <= self.col <= 2):
            raise ValueError(f"Position must be within 3x3 grid: ({self.row}, {self.col})")

    @property
    def opposite(self) -> Position:
        """Get the opposite position across the center."""
        return Position(2 - self.row, 2 - self.col)

    @property
    def is_center(self) -> bool:
        """Check if this is the center position."""
        return self.row == 1 and self.col == 1

    def to_tuple(self) -> Tuple[int, int]:
        """Convert to tuple for compatibility."""
        return (self.row, self.col)


@dataclass(frozen=True)
class Mountain:
    """
    One of the 24 Mountains (compass directions) in Feng Shui.

    Each mountain is 15 degrees of the compass and has:
    - A Chinese character name
    - A fixed position in the Lo Shu grid
    - A Yuan Long (天/人/地) category
    - A flight order (forward/reverse)
    """
    name: str
    position: Position
    yuan_long: str  # 天, 人, or 地
    flight_order: FlightOrder

    @classmethod
    def from_name(cls, name: str) -> Mountain:
        """Create a Mountain from its Chinese name."""
        from .constants import (
            FIXED_POSITIONS,
            YUAN_LONG_MAPPING,
            STAR_TO_FLIGHT,
        )

        pos_tuple = FIXED_POSITIONS.get(name)
        if pos_tuple is None:
            raise ValueError(f"Unknown mountain name: {name}")

        position = Position(pos_tuple[0], pos_tuple[1])
        yuan_long = YUAN_LONG_MAPPING.get(name, '天')
        flight_char = STAR_TO_FLIGHT.get(name, 'f')
        flight_order = FlightOrder.FORWARD if flight_char == 'f' else FlightOrder.REVERSE

        return cls(
            name=name,
            position=position,
            yuan_long=yuan_long,
            flight_order=flight_order,
        )


@dataclass(frozen=True)
class Grid:
    """
    A 3x3 Lo Shu grid with numbers 1-9.

    The grid represents the distribution of Flying Stars,
    with the center star being the main reference point.
    """
    cells: Tuple[Tuple[int, ...], ...]

    def __post_init__(self):
        if len(self.cells) != 3:
            raise ValueError("Grid must have 3 rows")
        for row in self.cells:
            if len(row) != 3:
                raise ValueError("Grid must have 3 columns")

    @classmethod
    def from_lists(cls, lists: List[List[int]]) -> Grid:
        """Create a Grid from nested lists."""
        return cls(tuple(tuple(row) for row in lists))

    @property
    def center(self) -> int:
        """Get the center value."""
        return self.cells[1][1]

    def at(self, position: Position) -> int:
        """Get value at a position."""
        return self.cells[position.row][position.col]

    def to_lists(self) -> List[List[int]]:
        """Convert to nested lists for compatibility."""
        return [list(row) for row in self.cells]

    def to_chinese(self) -> List[List[str]]:
        """Convert all numbers to Chinese numerals."""
        from .constants import ARABIC_TO_CHINESE
        return [[ARABIC_TO_CHINESE.get(n, str(n)) for n in row] for row in self.cells]

    @property
    def outer_ring(self) -> List[int]:
        """Get the outer ring values in clockwise order."""
        positions = [
            (0, 0), (0, 1), (0, 2),
            (1, 2), (2, 2), (2, 1),
            (2, 0), (1, 0)
        ]
        return [self.cells[r][c] for r, c in positions]

    def rotate_outer(self, steps: int) -> Grid:
        """
        Rotate the outer ring clockwise by the given number of steps.

        The center cell remains unchanged.
        """
        if steps == 0:
            return self

        positions = [
            (0, 0), (0, 1), (0, 2),
            (1, 2), (2, 2), (2, 1),
            (2, 0), (1, 0)
        ]

        outer = self.outer_ring
        steps = steps % 8
        new_outer = outer[-steps:] + outer[:-steps]

        new_cells = [list(row) for row in self.cells]
        for i, (r, c) in enumerate(positions):
            new_cells[r][c] = new_outer[i]

        return Grid.from_lists(new_cells)

    def get_shift_to_position(self, target_digit: int, target_index: int = 5) -> int:
        """
        Calculate the shift needed to move a digit to a target outer ring position.

        Args:
            target_digit: The digit to move
            target_index: The target index in the outer ring (default 5 = bottom-center)

        Returns:
            Number of clockwise steps needed
        """
        outer = self.outer_ring
        current_index = outer.index(target_digit)
        return (target_index - current_index) % 8
