"""
Lunar Python Adapter - Wraps lunar_python library.

This adapter implements the LunarPort protocol, providing
BaZi calculation and lunar calendar functionality.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, Tuple

from lunar_python import Solar, Lunar

from bazi.domain.models import (
    BaZi,
    BirthData,
    Pillar,
    HeavenlyStem,
    EarthlyBranch,
)


class LunarPythonAdapter:
    """
    Adapter that wraps the lunar_python library.

    Implements the LunarPort Protocol for BaZi calculation
    and lunar calendar operations.
    """

    def get_bazi(self, birth: BirthData) -> BaZi:
        """
        Calculate the Four Pillars (BaZi) from birth data.

        Args:
            birth: Birth date/time information

        Returns:
            BaZi with all four pillars calculated
        """
        solar = Solar.fromYmdHms(
            birth.year,
            birth.month,
            birth.day,
            birth.hour,
            birth.minute,
            0,
        )
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        return self._eight_char_to_bazi(eight_char)

    def get_bazi_from_datetime(self, dt: datetime) -> BaZi:
        """
        Calculate BaZi from a datetime object.

        Args:
            dt: Python datetime

        Returns:
            BaZi with all four pillars
        """
        solar = Solar.fromYmdHms(
            dt.year,
            dt.month,
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
        )
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        return self._eight_char_to_bazi(eight_char)

    def solar_to_lunar(
        self,
        year: int,
        month: int,
        day: int,
    ) -> Tuple[int, int, int, bool]:
        """
        Convert solar date to lunar date.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Tuple of (lunar_year, lunar_month, lunar_day, is_leap_month)
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        return (
            lunar.getYear(),
            lunar.getMonth(),
            lunar.getDay(),
            lunar.isLeap(),
        )

    def lunar_to_solar(
        self,
        year: int,
        month: int,
        day: int,
        is_leap: bool = False,
    ) -> Tuple[int, int, int]:
        """
        Convert lunar date to solar date.

        Args:
            year: Lunar year
            month: Lunar month
            day: Lunar day
            is_leap: Whether it's a leap month

        Returns:
            Tuple of (solar_year, solar_month, solar_day)
        """
        lunar = Lunar.fromYmd(year, month, day)
        if is_leap:
            # lunar_python handles leap months differently
            # For now, we ignore leap month flag as it's complex
            pass
        solar = lunar.getSolar()

        return (
            solar.getYear(),
            solar.getMonth(),
            solar.getDay(),
        )

    def get_year_pillar(self, year: int, month: int, day: int) -> Pillar:
        """
        Get the year pillar for a given date.

        Note: The year pillar changes at Lichun (立春), not Jan 1.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Year pillar
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        chars = eight_char.toString().split()[0]
        return Pillar.from_chinese(chars)

    def get_month_pillar(self, year: int, month: int, day: int) -> Pillar:
        """
        Get the month pillar for a given date.

        Note: The month pillar changes at each solar term (节气).

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Month pillar
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        chars = eight_char.toString().split()[1]
        return Pillar.from_chinese(chars)

    def get_day_pillar(self, year: int, month: int, day: int) -> Pillar:
        """
        Get the day pillar for a given date.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Day pillar
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        chars = eight_char.toString().split()[2]
        return Pillar.from_chinese(chars)

    def get_hour_pillar(
        self,
        year: int,
        month: int,
        day: int,
        hour: int,
    ) -> Pillar:
        """
        Get the hour pillar for a given date and time.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day
            hour: Hour (0-23)

        Returns:
            Hour pillar
        """
        solar = Solar.fromYmdHms(year, month, day, hour, 0, 0)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        chars = eight_char.toString().split()[3]
        return Pillar.from_chinese(chars)

    def get_jieqi(self, year: int, month: int, day: int) -> Optional[str]:
        """
        Get the solar term (节气) for a date if it falls on one.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Name of solar term if date is a jieqi, None otherwise
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        # Check if this date is a jieqi day
        jieqi = lunar.getJieQi()
        if jieqi:
            return jieqi

        return None

    def get_next_jieqi(
        self,
        year: int,
        month: int,
        day: int,
    ) -> Tuple[str, date]:
        """
        Get the next solar term after the given date.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Tuple of (jieqi_name, jieqi_date)
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        next_jieqi = lunar.getNextJieQi(True)
        jieqi_solar = next_jieqi.getSolar()

        return (
            next_jieqi.getName(),
            date(jieqi_solar.getYear(), jieqi_solar.getMonth(), jieqi_solar.getDay()),
        )

    def days_until_next_jieqi(
        self,
        year: int,
        month: int,
        day: int,
    ) -> int:
        """
        Calculate days until the next solar term.

        Used for determining earth-dominant periods (土旺).

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            Number of days until next jieqi
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        next_jieqi = lunar.getNextJieQi(True)
        jieqi_solar = next_jieqi.getSolar()

        return jieqi_solar.subtract(solar)

    def is_earth_dominant_period(
        self,
        year: int,
        month: int,
        day: int,
    ) -> bool:
        """
        Check if date is in earth-dominant period (last 18 days before season change).

        During this period, Earth element is strongest regardless of season.

        Args:
            year: Solar year
            month: Solar month
            day: Solar day

        Returns:
            True if in earth-dominant period
        """
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()

        # Get the month branch to check if we're in an earth branch month
        eight_char = lunar.getEightChar()
        month_zhi = eight_char.toString().split()[1][1]

        # Earth branches: 辰 (Chen), 未 (Wei), 戌 (Xu), 丑 (Chou)
        earth_branches = {'辰', '未', '戌', '丑'}

        if month_zhi in earth_branches:
            # Check if within 18 days of next jieqi
            days = self.days_until_next_jieqi(year, month, day)
            return days <= 18

        return False

    def get_jieqi_dates(
        self,
        year: int,
        jieqi_names: list[str],
    ) -> list[date]:
        """
        Get the dates of specified solar terms for a given year.

        Args:
            year: Solar year
            jieqi_names: List of solar term names in Chinese (e.g., ["立春", "立夏"])

        Returns:
            List of dates when those solar terms occur
        """
        solar = Solar.fromYmd(year, 1, 1)
        lunar = solar.getLunar()
        jieqi_table = lunar.getJieQiTable()

        result = []
        for name in jieqi_names:
            if name in jieqi_table:
                jieqi_solar = jieqi_table[name]
                result.append(date(
                    jieqi_solar.getYear(),
                    jieqi_solar.getMonth(),
                    jieqi_solar.getDay(),
                ))
        return result

    def _eight_char_to_bazi(self, eight_char) -> BaZi:
        """
        Convert lunar_python EightChar to domain BaZi.

        Args:
            eight_char: lunar_python EightChar object

        Returns:
            Domain BaZi object
        """
        # EightChar.toString() returns "甲子 丙寅 戊辰 壬子" format
        pillars_str = eight_char.toString().split()

        return BaZi(
            year_pillar=Pillar.from_chinese(pillars_str[0]),
            month_pillar=Pillar.from_chinese(pillars_str[1]),
            day_pillar=Pillar.from_chinese(pillars_str[2]),
            hour_pillar=Pillar.from_chinese(pillars_str[3]),
        )
