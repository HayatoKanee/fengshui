"""
BaZi (八字) aggregate and BirthData value object.

Pure Python - NO Django dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .elements import WuXing
from .pillar import Pillar
from .stems_branches import HeavenlyStem, EarthlyBranch


@dataclass(frozen=True)
class BirthData:
    """
    Input data for BaZi calculation.

    Value object representing birth time information.
    """
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    is_male: bool = True
    name: Optional[str] = None

    def __post_init__(self):
        """
        验证出生数据。
        Validate birth data with comprehensive checks.
        """
        # 基础范围检查
        if not (0 <= self.hour <= 23):
            raise ValueError(f"Hour must be 0-23, got: {self.hour}")
        if not (0 <= self.minute <= 59):
            raise ValueError(f"Minute must be 0-59, got: {self.minute}")

        # 使用 datetime 验证日期有效性（处理闰年、月份天数等）
        # Use datetime to validate date (handles leap years, days per month, etc.)
        try:
            datetime(self.year, self.month, self.day)
        except ValueError as e:
            raise ValueError(f"无效日期 Invalid date {self.year}-{self.month}-{self.day}: {e}")

    @classmethod
    def from_datetime(cls, dt: datetime, is_male: bool = True, name: Optional[str] = None) -> BirthData:
        """Create BirthData from a datetime object."""
        return cls(
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=dt.hour,
            minute=dt.minute,
            is_male=is_male,
            name=name,
        )


@dataclass(frozen=True)
class BaZi:
    """
    The Four Pillars of Destiny (八字/四柱).

    Aggregate root containing the four pillars and derived properties.
    This is the core domain model for BaZi analysis.
    """
    year_pillar: Pillar
    month_pillar: Pillar
    day_pillar: Pillar
    hour_pillar: Pillar

    def __str__(self) -> str:
        """Return Chinese representation (e.g., '甲子 乙丑 丙寅 丁卯')."""
        return f"{self.year_pillar} {self.month_pillar} {self.day_pillar} {self.hour_pillar}"

    @property
    def chinese(self) -> str:
        """Chinese representation of all four pillars."""
        return str(self)

    @property
    def pillars(self) -> List[Pillar]:
        """List of all four pillars in order: year, month, day, hour."""
        return [self.year_pillar, self.month_pillar, self.day_pillar, self.hour_pillar]

    @property
    def day_master(self) -> HeavenlyStem:
        """
        The Day Master (日主/日元) - the stem of the day pillar.

        This is the most important element representing the self.
        """
        return self.day_pillar.stem

    @property
    def day_master_wuxing(self) -> WuXing:
        """Five Element of the Day Master."""
        return self.day_master.wuxing

    @property
    def all_stems(self) -> List[HeavenlyStem]:
        """All four heavenly stems."""
        return [p.stem for p in self.pillars]

    @property
    def all_branches(self) -> List[EarthlyBranch]:
        """All four earthly branches."""
        return [p.branch for p in self.pillars]

    def wuxing_count(self) -> Dict[WuXing, int]:
        """
        Count occurrences of each WuXing element in stems and branches.

        Note: This is a simple count, not weighted by hidden stems.
        """
        count: Dict[WuXing, int] = {element: 0 for element in WuXing}

        for pillar in self.pillars:
            count[pillar.stem_wuxing] += 1
            count[pillar.branch_wuxing] += 1

        return count

    def contains_all_wuxing(self) -> bool:
        """Check if all five elements are present (五行俱全)."""
        count = self.wuxing_count()
        return all(v > 0 for v in count.values())

    @classmethod
    def from_chinese(cls, bazi_str: str) -> BaZi:
        """
        从中文字符串创建八字。
        Create BaZi from Chinese string.

        Args:
            bazi_str: String like '甲子 乙丑 丙寅 丁卯' or '甲子乙丑丙寅丁卯'

        Returns:
            BaZi instance

        Raises:
            ValueError: If string is not valid 8-character BaZi
        """
        chars = bazi_str.replace(" ", "")
        if len(chars) != 8:
            raise ValueError(f"八字必须8个字符 BaZi requires 8 characters, got: {len(chars)}")

        try:
            return cls(
                year_pillar=Pillar.from_chinese(chars[0:2]),
                month_pillar=Pillar.from_chinese(chars[2:4]),
                day_pillar=Pillar.from_chinese(chars[4:6]),
                hour_pillar=Pillar.from_chinese(chars[6:8]),
            )
        except ValueError as e:
            raise ValueError(f"无效八字 Invalid BaZi '{bazi_str}': {e}") from e

    @classmethod
    def from_pillars(cls, year: str, month: str, day: str, hour: str) -> BaZi:
        """
        Create BaZi from four pillar strings.

        Args:
            year: Year pillar like '甲子'
            month: Month pillar like '乙丑'
            day: Day pillar like '丙寅'
            hour: Hour pillar like '丁卯'
        """
        return cls(
            year_pillar=Pillar.from_chinese(year),
            month_pillar=Pillar.from_chinese(month),
            day_pillar=Pillar.from_chinese(day),
            hour_pillar=Pillar.from_chinese(hour),
        )
