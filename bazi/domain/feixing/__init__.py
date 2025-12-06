"""
FeiXing (Flying Star) Domain Module.

Domain models and pure calculation logic for Flying Star Feng Shui.
The Flying Star system uses a 3x3 Lo Shu grid with numbers 1-9,
where each number represents a "star" with specific characteristics.
"""
from .models import Grid, Position, Mountain, FlightOrder
from .calculator import FeiXingCalculator

__all__ = [
    "Grid",
    "Position",
    "Mountain",
    "FlightOrder",
    "FeiXingCalculator",
]
