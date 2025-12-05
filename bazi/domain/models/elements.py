"""
Five Elements (WuXing) and Yin-Yang domain models.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Set


class YinYang(Enum):
    """Yin-Yang polarity (阴阳)."""
    YANG = "阳"
    YIN = "阴"

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def opposite(self) -> YinYang:
        return YinYang.YIN if self == YinYang.YANG else YinYang.YANG


class WuXing(Enum):
    """Five Elements (五行)."""
    WOOD = "木"
    FIRE = "火"
    EARTH = "土"
    METAL = "金"
    WATER = "水"

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def generates(self) -> WuXing:
        """Element this generates (生)."""
        return _GENERATES[self]

    @property
    def overcomes(self) -> WuXing:
        """Element this overcomes/conquers (克)."""
        return _OVERCOMES[self]

    @property
    def generated_by(self) -> WuXing:
        """Element that generates this (被生)."""
        return _GENERATED_BY[self]

    @property
    def overcome_by(self) -> WuXing:
        """Element that overcomes this (被克)."""
        return _OVERCOME_BY[self]

    @property
    def beneficial(self) -> Set[WuXing]:
        """Elements beneficial to this element (有利)."""
        return {self, self.generated_by}

    @property
    def harmful(self) -> Set[WuXing]:
        """Elements harmful to this element (不利)."""
        return {self.generates, self.overcomes, self.overcome_by}

    @classmethod
    def from_chinese(cls, char: str) -> WuXing:
        """Create WuXing from Chinese character."""
        for element in cls:
            if element.value == char:
                return element
        raise ValueError(f"Unknown element: {char}")


# Generation cycle (生): Wood → Fire → Earth → Metal → Water → Wood
_GENERATES: Dict[WuXing, WuXing] = {
    WuXing.WOOD: WuXing.FIRE,
    WuXing.FIRE: WuXing.EARTH,
    WuXing.EARTH: WuXing.METAL,
    WuXing.METAL: WuXing.WATER,
    WuXing.WATER: WuXing.WOOD,
}

# Overcoming cycle (克): Wood → Earth → Water → Fire → Metal → Wood
_OVERCOMES: Dict[WuXing, WuXing] = {
    WuXing.WOOD: WuXing.EARTH,
    WuXing.FIRE: WuXing.METAL,
    WuXing.EARTH: WuXing.WATER,
    WuXing.METAL: WuXing.WOOD,
    WuXing.WATER: WuXing.FIRE,
}

# Reverse mappings
_GENERATED_BY: Dict[WuXing, WuXing] = {v: k for k, v in _GENERATES.items()}
_OVERCOME_BY: Dict[WuXing, WuXing] = {v: k for k, v in _OVERCOMES.items()}


class WangXiang(Enum):
    """Seasonal strength phases (旺相休囚死)."""
    WANG = "旺"   # Prosperous (1.2x)
    XIANG = "相"  # Prime (1.2x)
    XIU = "休"    # Rest (1.0x)
    QIU = "囚"    # Imprisoned (0.8x)
    SI = "死"     # Dead (0.8x)

    @property
    def chinese(self) -> str:
        return self.value

    @property
    def multiplier(self) -> float:
        """Strength multiplier for calculations."""
        return _WANG_XIANG_VALUES[self]


_WANG_XIANG_VALUES: Dict[WangXiang, float] = {
    WangXiang.WANG: 1.2,
    WangXiang.XIANG: 1.2,
    WangXiang.XIU: 1.0,
    WangXiang.QIU: 0.8,
    WangXiang.SI: 0.8,
}
