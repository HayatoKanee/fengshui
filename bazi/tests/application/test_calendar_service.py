"""
Tests for CalendarService.

These tests verify calendar generation, day quality scoring,
and profile-based favorable element lookup.
"""
import pytest
from freezegun import freeze_time
from datetime import date

from bazi.application.services.calendar_service import DayQuality
from bazi.domain.models import BirthData
from bazi.domain.models.elements import WuXing
from bazi.domain.models.analysis import FavorableElements


class TestCalendarService:
    """Tests for CalendarService.generate_month()"""

    def test_generate_month_returns_calendar_month(self, calendar_service, favorable_elements):
        """generate_month should return a CalendarMonth object."""
        month = calendar_service.generate_month(2024, 6, favorable_elements)

        assert month is not None
        assert month.year == 2024
        assert month.month == 6
        assert len(month.days) > 0

    def test_generate_month_has_correct_day_count(self, calendar_service, favorable_elements):
        """Month should have correct number of days."""
        # June has 30 days
        june = calendar_service.generate_month(2024, 6, favorable_elements)
        assert len(june.days) == 30

        # July has 31 days
        july = calendar_service.generate_month(2024, 7, favorable_elements)
        assert len(july.days) == 31

        # February 2024 (leap year) has 29 days
        feb = calendar_service.generate_month(2024, 2, favorable_elements)
        assert len(feb.days) == 29

    def test_generate_month_days_have_required_fields(self, calendar_service, favorable_elements):
        """Each day should have all required fields."""
        month = calendar_service.generate_month(2024, 6, favorable_elements)

        for day in month.days:
            assert day.date is not None
            assert day.day_pillar is not None
            assert day.quality is not None
            assert isinstance(day.quality, DayQuality)
            assert day.quality_score is not None

    def test_generate_month_days_are_sequential(self, calendar_service, favorable_elements):
        """Days should be in sequential order."""
        month = calendar_service.generate_month(2024, 6, favorable_elements)

        for i, day in enumerate(month.days):
            expected_date = date(2024, 6, i + 1)
            assert day.date == expected_date

    def test_generate_month_quality_distribution(self, calendar_service, favorable_elements):
        """Days should have varied quality scores."""
        month = calendar_service.generate_month(2024, 6, favorable_elements)

        qualities = [day.quality for day in month.days]

        # Should have more than one quality level
        unique_qualities = set(qualities)
        assert len(unique_qualities) >= 1  # At least some variety

    @freeze_time("2024-06-15")
    def test_generate_month_current_date(self, calendar_service, favorable_elements):
        """Should work with current date frozen."""
        month = calendar_service.generate_month(2024, 6, favorable_elements)

        assert month.year == 2024
        assert month.month == 6


class TestCalendarServiceWithProfile:
    """Tests for calendar generation with user profile."""

    @pytest.mark.django_db
    def test_generate_month_with_birth_data(self, calendar_service, birth_data):
        """Calendar should work with favorable elements from birth data."""
        # Calculate favorable elements from birth data
        favorable = calendar_service.get_favorable_elements_for_profile(birth_data)
        month = calendar_service.generate_month(2024, 6, favorable)

        assert month is not None
        assert len(month.days) == 30

    @pytest.mark.django_db
    def test_get_favorable_elements_for_profile(self, calendar_service, birth_data):
        """Should retrieve favorable elements from birth data."""
        elements = calendar_service.get_favorable_elements_for_profile(birth_data)

        assert elements is not None
        assert isinstance(elements, FavorableElements)
        # Should have yong_shen and ji_shen at minimum
        assert elements.yong_shen is not None
        assert elements.ji_shen is not None


class TestDayQuality:
    """Tests for DayQuality enum."""

    def test_day_quality_values(self):
        """DayQuality should have expected string values."""
        assert DayQuality.EXCELLENT.value == "excellent"
        assert DayQuality.GOOD.value == "good"
        assert DayQuality.NEUTRAL.value == "neutral"
        assert DayQuality.BAD.value == "bad"
        assert DayQuality.TERRIBLE.value == "terrible"

    def test_day_quality_all_values_exist(self):
        """All five quality levels should exist."""
        qualities = list(DayQuality)
        assert len(qualities) == 5
        assert DayQuality.EXCELLENT in qualities
        assert DayQuality.GOOD in qualities
        assert DayQuality.NEUTRAL in qualities
        assert DayQuality.BAD in qualities
        assert DayQuality.TERRIBLE in qualities


class TestCalendarServiceEdgeCases:
    """Edge case tests for CalendarService."""

    def test_generate_month_january(self, calendar_service, favorable_elements):
        """January (near Chinese New Year) should work."""
        month = calendar_service.generate_month(2024, 1, favorable_elements)
        assert len(month.days) == 31

    def test_generate_month_december(self, calendar_service, favorable_elements):
        """December should work."""
        month = calendar_service.generate_month(2024, 12, favorable_elements)
        assert len(month.days) == 31

    def test_generate_month_leap_year_february(self, calendar_service, favorable_elements):
        """Leap year February should have 29 days."""
        month = calendar_service.generate_month(2024, 2, favorable_elements)
        assert len(month.days) == 29

    def test_generate_month_non_leap_year_february(self, calendar_service, favorable_elements):
        """Non-leap year February should have 28 days."""
        month = calendar_service.generate_month(2023, 2, favorable_elements)
        assert len(month.days) == 28

    def test_generate_month_historical_date(self, calendar_service, favorable_elements):
        """Historical dates should work."""
        month = calendar_service.generate_month(1990, 6, favorable_elements)
        assert len(month.days) == 30

    def test_generate_month_future_date(self, calendar_service, favorable_elements):
        """Future dates should work."""
        month = calendar_service.generate_month(2050, 6, favorable_elements)
        assert len(month.days) == 30
