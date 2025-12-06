"""
Calendar Application Service.

Generates calendar data with day quality assessments based on
a user's BaZi profile.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional, TYPE_CHECKING

from bazi.domain.models import (
    BaZi,
    BirthData,
    WuXing,
    Pillar,
    FavorableElements,
)
from bazi.domain.services import (
    WuXingCalculator,
    DayMasterAnalyzer,
)

if TYPE_CHECKING:
    from bazi.domain.ports import LunarPort


class DayQuality(Enum):
    """Quality assessment for a calendar day."""

    EXCELLENT = "excellent"  # 大吉
    GOOD = "good"  # 吉
    NEUTRAL = "neutral"  # 平
    BAD = "bad"  # 凶
    TERRIBLE = "terrible"  # 大凶


@dataclass
class CalendarDay:
    """
    Calendar day information with BaZi analysis.

    Contains all information needed to render a calendar day,
    including quality assessment based on user's BaZi.
    """

    date: date
    day_pillar: Pillar
    quality: DayQuality
    quality_score: int  # -2 to +2
    jieqi: Optional[str]  # Solar term if this day is one
    notes: List[str]  # Reasons for the quality rating

    @property
    def day_number(self) -> int:
        """Day of month (1-31)."""
        return self.date.day

    @property
    def weekday(self) -> int:
        """Day of week (0=Monday, 6=Sunday)."""
        return self.date.weekday()

    @property
    def is_weekend(self) -> bool:
        """Whether this is a weekend day."""
        return self.weekday >= 5


@dataclass
class CalendarMonth:
    """
    A month of calendar data with BaZi analysis.

    Contains all days in the month with quality assessments.
    """

    year: int
    month: int
    days: List[CalendarDay]
    month_pillar: Pillar

    @property
    def first_weekday(self) -> int:
        """Weekday of the first day of month (0=Monday)."""
        return date(self.year, self.month, 1).weekday()

    @property
    def num_days(self) -> int:
        """Number of days in the month."""
        return len(self.days)

    def get_day(self, day_number: int) -> Optional[CalendarDay]:
        """Get a specific day by day number (1-31)."""
        if 1 <= day_number <= len(self.days):
            return self.days[day_number - 1]
        return None


class CalendarService:
    """
    Application service for calendar generation.

    Generates calendar data with day quality assessments based on
    a user's BaZi profile and favorable/unfavorable elements.

    Usage:
        service = CalendarService(lunar_adapter)
        month_data = service.generate_month(2024, 12, favorable_elements)
    """

    def __init__(
        self,
        lunar_adapter: LunarPort,
        wuxing_calculator: Optional[WuXingCalculator] = None,
        day_master_analyzer: Optional[DayMasterAnalyzer] = None,
    ):
        """
        Initialize the calendar service.

        Args:
            lunar_adapter: Adapter for lunar calendar calculations
            wuxing_calculator: Calculator for WuXing relationships (optional)
            day_master_analyzer: Analyzer for day master strength (optional)
        """
        self._lunar = lunar_adapter
        self._wuxing_calc = wuxing_calculator or WuXingCalculator()
        self._day_master = day_master_analyzer or DayMasterAnalyzer()

    def generate_month(
        self,
        year: int,
        month: int,
        favorable: FavorableElements,
    ) -> CalendarMonth:
        """
        Generate a month of calendar data with quality assessments.

        Args:
            year: Calendar year
            month: Calendar month (1-12)
            favorable: User's favorable/unfavorable elements

        Returns:
            CalendarMonth with all days analyzed
        """
        # Get month pillar
        month_pillar = self._lunar.get_month_pillar(year, month, 15)

        # Get number of days in month
        num_days = calendar.monthrange(year, month)[1]

        # Generate data for each day
        days = []
        for day_num in range(1, num_days + 1):
            day_data = self._analyze_day(year, month, day_num, favorable)
            days.append(day_data)

        return CalendarMonth(
            year=year,
            month=month,
            days=days,
            month_pillar=month_pillar,
        )

    def generate_day(
        self,
        year: int,
        month: int,
        day: int,
        favorable: FavorableElements,
    ) -> CalendarDay:
        """
        Generate calendar data for a single day.

        Args:
            year: Calendar year
            month: Calendar month (1-12)
            day: Calendar day (1-31)
            favorable: User's favorable/unfavorable elements

        Returns:
            CalendarDay with quality assessment
        """
        return self._analyze_day(year, month, day, favorable)

    def _analyze_day(
        self,
        year: int,
        month: int,
        day: int,
        favorable: FavorableElements,
    ) -> CalendarDay:
        """
        Analyze a single day's quality.

        Args:
            year: Calendar year
            month: Calendar month
            day: Calendar day
            favorable: User's favorable/unfavorable elements

        Returns:
            CalendarDay with quality assessment
        """
        # Get day pillar
        day_pillar = self._lunar.get_day_pillar(year, month, day)

        # Check for solar term (jieqi)
        jieqi = self._lunar.get_jieqi(year, month, day)

        # Calculate quality score based on day pillar's elements
        score, notes = self._calculate_quality_score(day_pillar, favorable)

        # Convert score to quality enum
        quality = self._score_to_quality(score)

        return CalendarDay(
            date=date(year, month, day),
            day_pillar=day_pillar,
            quality=quality,
            quality_score=score,
            jieqi=jieqi,
            notes=notes,
        )

    def _calculate_quality_score(
        self,
        day_pillar: Pillar,
        favorable: FavorableElements,
    ) -> tuple[int, List[str]]:
        """
        Calculate a quality score for a day based on favorable elements.

        The score is based on:
        - Day stem's element (+1/-1 for favorable/unfavorable)
        - Day branch's element (+1/-1 for favorable/unfavorable)
        - Hidden stems' elements (weighted by ratio)

        Args:
            day_pillar: The day's pillar
            favorable: User's favorable/unfavorable elements

        Returns:
            Tuple of (score, notes) where score is -2 to +2
        """
        score = 0.0
        notes = []

        # Check day stem
        stem_element = day_pillar.stem_wuxing
        if stem_element in favorable.favorable:
            score += 1.0
            notes.append(f"日干{day_pillar.stem.chinese}({stem_element.value})为喜用")
        elif stem_element in favorable.unfavorable:
            score -= 1.0
            notes.append(f"日干{day_pillar.stem.chinese}({stem_element.value})为忌神")

        # Check day branch main element
        branch_element = day_pillar.branch_wuxing
        if branch_element in favorable.favorable:
            score += 0.5
            notes.append(f"日支{day_pillar.branch.chinese}({branch_element.value})为喜用")
        elif branch_element in favorable.unfavorable:
            score -= 0.5
            notes.append(f"日支{day_pillar.branch.chinese}({branch_element.value})为忌神")

        # Check hidden stems (weighted by ratio)
        for hidden_stem, ratio in day_pillar.hidden_stems.items():
            hidden_element = hidden_stem.wuxing
            if hidden_element in favorable.favorable:
                score += 0.3 * ratio
            elif hidden_element in favorable.unfavorable:
                score -= 0.3 * ratio

        # Clamp score to -2 to +2 range
        score = max(-2, min(2, round(score)))

        return int(score), notes

    def _score_to_quality(self, score: int) -> DayQuality:
        """Convert numeric score to quality enum."""
        if score >= 2:
            return DayQuality.EXCELLENT
        elif score >= 1:
            return DayQuality.GOOD
        elif score >= 0:
            return DayQuality.NEUTRAL
        elif score >= -1:
            return DayQuality.BAD
        else:
            return DayQuality.TERRIBLE

    # ============================================
    # Calendar Taboo Methods (Special Day Checks)
    # ============================================

    @staticmethod
    def is_yang_gong_taboo(lunar_month: int, lunar_day: int) -> bool:
        """
        Check if a lunar date is one of the Yang Gong Thirteen Taboos (杨公十三忌).

        These are traditionally inauspicious days for important activities.

        Args:
            lunar_month: Lunar month (1-12)
            lunar_day: Lunar day (1-30)

        Returns:
            True if the date is a Yang Gong taboo day
        """
        yang_gong_taboos = {
            (1, 13),   # 正月十三
            (2, 11),   # 二月十一
            (3, 9),    # 三月初九
            (4, 7),    # 四月初七
            (5, 5),    # 五月初五
            (6, 3),    # 六月初三
            (7, 1),    # 七月初一
            (7, 29),   # 七月二十九
            (8, 27),   # 八月二十七
            (9, 25),   # 九月二十五
            (10, 23),  # 十月二十三
            (11, 21),  # 十一月二十一
            (12, 19),  # 十二月十九
        }
        return (lunar_month, lunar_day) in yang_gong_taboos

    def is_si_jue_ri(self, year: int, month: int, day: int) -> bool:
        """
        Check if a date is one of the '四绝日' (Four "Jue" Days).

        These are the days before Li Chun (立春), Li Xia (立夏),
        Li Qiu (立秋), and Li Dong (立冬).

        Args:
            year: Solar year
            month: Solar month (1-12)
            day: Solar day (1-31)

        Returns:
            True if the date is a Si Jue day
        """
        # Get the day before each "Li" solar term
        jue_jieqi = ["立春", "立夏", "立秋", "立冬"]
        return self._is_day_before_jieqi(year, month, day, jue_jieqi)

    def is_si_li_ri(self, year: int, month: int, day: int) -> bool:
        """
        Check if a date is one of the '四离日' (Four "Li" Days).

        These are the days before Chun Fen (春分), Xia Zhi (夏至),
        Qiu Fen (秋分), and Dong Zhi (冬至).

        Args:
            year: Solar year
            month: Solar month (1-12)
            day: Solar day (1-31)

        Returns:
            True if the date is a Si Li day
        """
        # Get the day before each equinox/solstice
        li_jieqi = ["春分", "夏至", "秋分", "冬至"]
        return self._is_day_before_jieqi(year, month, day, li_jieqi)

    def _is_day_before_jieqi(
        self,
        year: int,
        month: int,
        day: int,
        jieqi_names: list[str],
    ) -> bool:
        """
        Check if a date is the day before one of the specified solar terms.

        Args:
            year: Solar year
            month: Solar month (1-12)
            day: Solar day (1-31)
            jieqi_names: List of solar term names to check

        Returns:
            True if the date is the day before any of the specified solar terms
        """
        try:
            # Get jieqi dates for this year from lunar adapter
            jieqi_dates = self._lunar.get_jieqi_dates(year, jieqi_names)

            current_date = date(year, month, day)

            for jieqi_date in jieqi_dates:
                # Check if current date is the day before this jieqi
                day_before = jieqi_date - datetime.timedelta(days=1)
                if current_date == day_before:
                    return True
            return False
        except Exception:
            # If jieqi lookup fails, return False to avoid breaking the calendar
            return False

    def get_favorable_elements_for_profile(
        self,
        birth_data: BirthData,
    ) -> FavorableElements:
        """
        Calculate favorable elements for a birth profile.

        Convenience method that performs the day master analysis
        and returns the favorable elements.

        Args:
            birth_data: Birth date/time information

        Returns:
            FavorableElements for the profile
        """
        bazi = self._lunar.get_bazi(birth_data)
        is_earth_dominant = self._lunar.is_earth_dominant_period(
            birth_data.year,
            birth_data.month,
            birth_data.day,
        )

        _, favorable, _ = self._day_master.full_analysis(bazi, is_earth_dominant)
        return favorable
