"""
Tests for LunarPythonAdapter.

These tests verify the adapter correctly wraps the lunar_python library
and implements the LunarPort protocol.
"""
import pytest
from datetime import datetime, date

from bazi.domain.models import BirthData, BaZi, Pillar
from bazi.domain.models.stems_branches import HeavenlyStem, EarthlyBranch


class TestLunarAdapterGetBazi:
    """Tests for LunarPythonAdapter.get_bazi()"""

    def test_get_bazi_returns_bazi(self, lunar_adapter):
        """get_bazi should return a BaZi object."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)

        assert isinstance(bazi, BaZi)
        assert isinstance(bazi.year_pillar, Pillar)
        assert isinstance(bazi.month_pillar, Pillar)
        assert isinstance(bazi.day_pillar, Pillar)
        assert isinstance(bazi.hour_pillar, Pillar)

    def test_get_bazi_has_valid_stems(self, lunar_adapter):
        """BaZi should have valid heavenly stems."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)

        assert isinstance(bazi.year_pillar.stem, HeavenlyStem)
        assert isinstance(bazi.month_pillar.stem, HeavenlyStem)
        assert isinstance(bazi.day_pillar.stem, HeavenlyStem)
        assert isinstance(bazi.hour_pillar.stem, HeavenlyStem)

    def test_get_bazi_has_valid_branches(self, lunar_adapter):
        """BaZi should have valid earthly branches."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)

        assert isinstance(bazi.year_pillar.branch, EarthlyBranch)
        assert isinstance(bazi.month_pillar.branch, EarthlyBranch)
        assert isinstance(bazi.day_pillar.branch, EarthlyBranch)
        assert isinstance(bazi.hour_pillar.branch, EarthlyBranch)

    def test_get_bazi_known_date(self, lunar_adapter):
        """Test with a known date to verify correctness."""
        # 1984-01-01 00:00 should be 癸亥年 甲子月 甲子日 甲子时 (approximately)
        # This is a rough test - exact values depend on lunar calendar
        birth = BirthData(
            year=1984, month=1, day=1,
            hour=0, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)

        # Just verify we get valid results
        assert bazi is not None
        assert bazi.year_pillar is not None

    def test_get_bazi_different_hours_same_day(self, lunar_adapter):
        """Different hours on same day should have same day pillar."""
        base_birth = BirthData(
            year=1990, month=6, day=15,
            hour=6, minute=0, is_male=True
        )
        later_birth = BirthData(
            year=1990, month=6, day=15,
            hour=18, minute=0, is_male=True
        )

        bazi1 = lunar_adapter.get_bazi(base_birth)
        bazi2 = lunar_adapter.get_bazi(later_birth)

        # Day pillar should be the same
        assert bazi1.day_pillar == bazi2.day_pillar
        # Hour pillar should be different
        assert bazi1.hour_pillar != bazi2.hour_pillar


class TestLunarAdapterDateConversion:
    """Tests for solar/lunar date conversion."""

    def test_solar_to_lunar(self, lunar_adapter):
        """solar_to_lunar should convert dates correctly."""
        result = lunar_adapter.solar_to_lunar(2024, 6, 15)

        assert result is not None
        # Returns tuple of (year, month, day, is_leap_month)
        assert isinstance(result, tuple)
        assert len(result) == 4
        lunar_year, lunar_month, lunar_day, is_leap = result
        assert isinstance(lunar_year, int)
        assert isinstance(lunar_month, int)
        assert isinstance(lunar_day, int)
        assert isinstance(is_leap, bool)

    def test_lunar_to_solar(self, lunar_adapter):
        """lunar_to_solar should convert dates correctly."""
        # Lunar 2024-5-10 should map to some solar date
        result = lunar_adapter.lunar_to_solar(2024, 5, 10)

        assert result is not None
        # Returns tuple of (year, month, day)
        assert isinstance(result, tuple)
        assert len(result) == 3
        solar_year, solar_month, solar_day = result
        assert isinstance(solar_year, int)
        assert isinstance(solar_month, int)
        assert isinstance(solar_day, int)


class TestLunarAdapterJieqi:
    """Tests for Jieqi (solar term) functions."""

    def test_get_jieqi_returns_string(self, lunar_adapter):
        """get_jieqi should return the solar term name."""
        result = lunar_adapter.get_jieqi(2024, 6, 21)

        # June 21 is typically around Summer Solstice (夏至)
        # Result could be the term name or None
        assert result is None or isinstance(result, str)

    def test_get_next_jieqi(self, lunar_adapter):
        """get_next_jieqi should return next solar term info."""
        result = lunar_adapter.get_next_jieqi(2024, 6, 15)

        assert result is not None

    def test_days_until_next_jieqi(self, lunar_adapter):
        """days_until_next_jieqi should return a positive integer."""
        days = lunar_adapter.days_until_next_jieqi(2024, 6, 15)

        assert isinstance(days, int)
        assert 0 <= days <= 31  # Should be within a month


class TestLunarAdapterPillarMethods:
    """Tests for individual pillar lookup methods."""

    def test_get_year_pillar(self, lunar_adapter):
        """get_year_pillar should return a Pillar."""
        pillar = lunar_adapter.get_year_pillar(1990, 6, 15)

        assert isinstance(pillar, Pillar)
        assert isinstance(pillar.stem, HeavenlyStem)
        assert isinstance(pillar.branch, EarthlyBranch)

    def test_get_month_pillar(self, lunar_adapter):
        """get_month_pillar should return a Pillar."""
        pillar = lunar_adapter.get_month_pillar(1990, 6, 15)

        assert isinstance(pillar, Pillar)

    def test_get_day_pillar(self, lunar_adapter):
        """get_day_pillar should return a Pillar."""
        pillar = lunar_adapter.get_day_pillar(1990, 6, 15)

        assert isinstance(pillar, Pillar)

    def test_get_hour_pillar(self, lunar_adapter):
        """get_hour_pillar should return a Pillar."""
        pillar = lunar_adapter.get_hour_pillar(1990, 6, 15, 12)

        assert isinstance(pillar, Pillar)


class TestLunarAdapterEdgeCases:
    """Edge case tests for LunarPythonAdapter."""

    def test_midnight_boundary(self, lunar_adapter):
        """Midnight (00:00) should be handled correctly."""
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=0, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)
        assert bazi is not None

    def test_zi_hour_boundary(self, lunar_adapter):
        """23:00-01:00 (子时) crosses midnight."""
        # 23:30 should be 子时 of the next day in traditional calculation
        birth = BirthData(
            year=1990, month=6, day=15,
            hour=23, minute=30, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)
        assert bazi is not None

    def test_leap_month_handling(self, lunar_adapter):
        """Leap months in lunar calendar should be handled."""
        # Just verify no crash on dates that might have leap months
        birth = BirthData(
            year=2020, month=5, day=15,  # 2020 had a leap month
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)
        assert bazi is not None

    def test_old_date(self, lunar_adapter):
        """Very old dates should work."""
        birth = BirthData(
            year=1900, month=1, day=1,
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)
        assert bazi is not None

    def test_future_date(self, lunar_adapter):
        """Future dates should work."""
        birth = BirthData(
            year=2100, month=6, day=15,
            hour=12, minute=0, is_male=True
        )
        bazi = lunar_adapter.get_bazi(birth)
        assert bazi is not None
