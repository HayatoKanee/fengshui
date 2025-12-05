"""
Lunar Calendar Port - Interface for lunar calendar operations.

This port abstracts the lunar_python library, allowing the domain
to work with any lunar calendar implementation.
"""
from __future__ import annotations

from abc import abstractmethod
from datetime import date, datetime
from typing import Optional, Protocol, Tuple

from ..models import BaZi, BirthData, Pillar


class LunarPort(Protocol):
    """
    Protocol for lunar calendar operations.

    This interface abstracts lunar calendar functionality,
    currently implemented by lunar_python library.
    """

    @abstractmethod
    def get_bazi(self, birth: BirthData) -> BaZi:
        """
        Calculate the Four Pillars (BaZi) from birth data.

        Args:
            birth: Birth date/time information

        Returns:
            BaZi with all four pillars calculated
        """
        ...

    @abstractmethod
    def get_bazi_from_datetime(self, dt: datetime) -> BaZi:
        """
        Calculate BaZi from a datetime object.

        Args:
            dt: Python datetime

        Returns:
            BaZi with all four pillars
        """
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...

    @abstractmethod
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
        ...
